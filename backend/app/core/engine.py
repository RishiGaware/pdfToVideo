import asyncio
import os
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from app.services.analyzer import DocumentAnalyzer, TableAnalyzer
from app.services.segmenter import TopicSegmenter
from app.services.classifier import SceneClassifier
from app.services.audio import AudioEngine
from app.services.renderer import SlideRenderer
import logging

logger = logging.getLogger(__name__)

from proglog import ProgressBarLogger

class MoviePyProgressLogger(ProgressBarLogger):
    """Capture MoviePy rendering progress and map it to the 80-100% range."""
    def __init__(self, on_progress):
        super().__init__()
        self.on_progress = on_progress
        self.last_pct = -1

    def callback(self, **changes):
        bars = self.state.get('bars', {})
        target_bar = bars.get('frame_index') or bars.get('t')
        
        if target_bar and target_bar.get('total', 0) > 0:
            pct = int((target_bar['index'] / target_bar['total']) * 100)
            if pct > self.last_pct:
                # Map 0-100% of encoding to 80-99% of total progress
                scaled = 80 + int(pct * 0.19)
                self.on_progress(scaled, f"Exporting frames ({pct}%)...")
                self.last_pct = pct

class AutomatedTrainingEngine:
    """The central orchestrator for the Intelligent Document-to-Video Engine (IDVE)."""
    
    def __init__(self, pdf_path, output_dir, progress_callback=None):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        os.makedirs(output_dir, exist_ok=True)

    async def run(self):
        """Executes the 7-stage pipeline (Non-blocking)."""
        try:
            # Stage 1: Extraction (Move to thread)
            self._update_progress(10, "Extracting document structure...")
            analyzer = await asyncio.to_thread(DocumentAnalyzer, self.pdf_path)
            elements = await asyncio.to_thread(analyzer.get_structure)
            
            table_analyzer = await asyncio.to_thread(TableAnalyzer, self.pdf_path)
            tables = await asyncio.to_thread(table_analyzer.get_tables)

            # Stage 2: Segmentation
            self._update_progress(20, "Segmenting into logical topics...")
            segmenter = TopicSegmenter(elements, tables)
            topics = await asyncio.to_thread(segmenter.segment)

            # Stage 3: Classification & IR
            self._update_progress(30, "Classifying scenes...")
            scenes = SceneClassifier.to_ir(topics)

            # Stage 3.5: Identify Global Video Title
            video_title = "Automated Training"
            for el in elements:
                if el["type"] == "title":
                    video_title = el["text"]
                    break
            
            # Stage 4: Parallel Synthesis (Audio & Visuals)
            self._update_progress(40, "Synthesizing narration and visuals...")
            
            audio_dir = os.path.join(self.output_dir, "audio")
            visual_dir = os.path.join(self.output_dir, "slides")
            os.makedirs(audio_dir, exist_ok=True)
            os.makedirs(visual_dir, exist_ok=True)

            total_assets = len(scenes) * 2
            completed_assets = 0

            def on_asset_done():
                nonlocal completed_assets
                completed_assets += 1
                pct = 40 + int((completed_assets / total_assets) * 40)
                self._update_progress(pct, f"Preparing scene assets ({completed_assets}/{total_assets})...")

            # Parallel Audio
            audio_engine = AudioEngine()
            audio_task = audio_engine.batch_generate(scenes, audio_dir, on_asset_done)

            # Parallel Visuals (Pillow Rendering in Parallel)
            async def render_scene_visual(scene, renderer, visual_dir, on_asset_done):
                img_path = os.path.join(visual_dir, f"slide_{scene['id']}.png")
                stype = scene["type"]
                
                # Template selection logic (Uniform minimalist style)
                if stype == "IntroScene":
                    render_func = renderer.render_title_slide
                elif stype == "TableScene":
                    render_func = renderer.render_table_slide
                else:
                    render_func = renderer.render_training_slide
                    
                await asyncio.to_thread(render_func, scene, img_path)
                scene["image_path"] = img_path
                on_asset_done()

            # Create shared renderer for font caching
            renderer = SlideRenderer(video_title=video_title)
            visual_tasks = [render_scene_visual(s, renderer, visual_dir, on_asset_done) for s in scenes]

            await asyncio.gather(audio_task, *visual_tasks)

            # Stage 5: Assembly (Move MoviePy render to thread)
            self._update_progress(80, "Assembling final training video...")
            video_path = await self._assemble(scenes)
            
            self._update_progress(100, "Success! Video ready.")
            return video_path
        except Exception as e:
            logger.error(f"Engine failure: {e}")
            raise

    async def _assemble(self, scenes):
        """Assembles clips into final MP4 (Non-blocking)."""
        clips = []
        for s in scenes:
            audio = AudioFileClip(s["audio_path"])
            image = ImageClip(s["image_path"]).with_duration(audio.duration)
            clip = image.with_audio(audio)
            clips.append(clip)
        
        final_video = concatenate_videoclips(clips) # method="compose" is slow and unnecessary for same-size slides
        final_path = os.path.join(self.output_dir, "final_training.mp4")
        
        # Mapping 80-100% progress
        render_logger = MoviePyProgressLogger(self._update_progress)
        
        # MoviePy's write_videofile is EXTREMELY blocking. Offload it entirely.
        await asyncio.to_thread(
            final_video.write_videofile,
            final_path, 
            fps=12, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            threads=4, # Use more threads for speed
            logger=render_logger
        )
        
        for c in clips: c.close()
        final_video.close()
        return final_path

    def _update_progress(self, p, msg):
        if self.progress_callback:
            self.progress_callback(p, msg)
