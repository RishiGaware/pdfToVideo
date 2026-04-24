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
    
    def __init__(self, pdf_path, output_dir, progress_callback=None, original_filename=None):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.progress_callback = progress_callback
        self.original_filename = original_filename
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
            
            # Release file early to avoid Windows lock issues
            await asyncio.to_thread(analyzer.close)

            # Stage 2: Segmentation
            self._update_progress(20, "Segmenting into logical topics...")
            segmenter = TopicSegmenter(elements, tables)
            topics = await asyncio.to_thread(segmenter.segment)

            # Stage 3: Classification & IR (Expanded into atomic steps)
            self._update_progress(30, "Preparing animation steps...")
            scenes = SceneClassifier.to_ir(topics)
            
            # Flatten all steps across all scenes for parallel processing
            atomic_steps = []
            for scene in scenes:
                for step in scene["steps"]:
                    # Attach metadata for renderer selection
                    step["type"] = scene["type"]
                    step["title"] = scene["title"]
                    # Renderer expects 'bullets' key for content
                    step["bullets"] = step["bullets_to_show"]
                    atomic_steps.append(step)

            # Stage 3.5: Identify Global Video Title (From Original Filename)
            filename = self.original_filename or os.path.basename(self.pdf_path)
            video_title = os.path.splitext(filename)[0]
            self._update_progress(35, f"Setting video title: {video_title}")
            
            # Stage 4: Parallel Synthesis (Audio & Visuals for every step)
            self._update_progress(40, "Synthesizing narration and animation...")
            
            audio_dir = os.path.join(self.output_dir, "audio")
            visual_dir = os.path.join(self.output_dir, "slides")
            os.makedirs(audio_dir, exist_ok=True)
            os.makedirs(visual_dir, exist_ok=True)

            total_assets = len(atomic_steps) * 2
            completed_assets = 0

            def on_asset_done():
                nonlocal completed_assets
                completed_assets += 1
                pct = 40 + int((completed_assets / total_assets) * 40)
                self._update_progress(pct, f"Preparing animations ({completed_assets}/{total_assets})...")

            # Parallel Audio for all steps
            audio_engine = AudioEngine()
            audio_task = audio_engine.batch_generate(atomic_steps, audio_dir, on_asset_done)

            # Parallel Visuals for all steps
            async def render_step_visual(step, renderer, visual_dir, on_asset_done):
                img_path = os.path.join(visual_dir, f"step_{step['id']}.png")
                stype = step["type"]
                
                # Selection logic
                if stype == "IntroScene":
                    render_func = renderer.render_title_slide
                elif stype == "TableScene":
                    render_func = renderer.render_table_slide
                else:
                    render_func = renderer.render_training_slide
                    
                await asyncio.to_thread(render_func, step, img_path)
                step["image_path"] = img_path
                on_asset_done()

            renderer = SlideRenderer(video_title=video_title)
            visual_tasks = [render_step_visual(s, renderer, visual_dir, on_asset_done) for s in atomic_steps]

            await asyncio.gather(audio_task, *visual_tasks)

            # Stage 5: Assembly
            self._update_progress(80, "Stitching animation steps...")
            video_path = await self._assemble(atomic_steps)
            
            self._update_progress(100, "Success! Video ready.")
            return video_path
        except Exception as e:
            logger.error(f"Engine failure: {e}")
            raise

    async def _assemble(self, steps):
        """Assembles atomic animation steps into final MP4."""
        clips = []
        for s in steps:
            audio = AudioFileClip(s["audio_path"])
            image = ImageClip(s["image_path"]).with_duration(audio.duration)
            clip = image.with_audio(audio)
            clips.append(clip)
        
        final_video = concatenate_videoclips(clips) # method="compose" is slow and unnecessary for same-size slides
        final_path = os.path.join(self.output_dir, "final_training.mp4")
        
        # Mapping 80-100% progress
        render_logger = MoviePyProgressLogger(self._update_progress)
        
        # MoviePy's write_videofile is EXTREMELY blocking. Offload it entirely.
        # On Windows, using a specific temp_audiofile prevents 'File in use' errors.
        temp_audio = os.path.join(self.output_dir, "temp_render_audio.m4a")
        
        await asyncio.to_thread(
            final_video.write_videofile,
            final_path, 
            fps=12, 
            codec="libx264", 
            audio_codec="aac",
            temp_audiofile=temp_audio,
            remove_temp=True,
            preset="ultrafast",
            ffmpeg_params=["-movflags", "+faststart"],
            threads=1, # Single thread is safer on Windows for the final muxing stage
            logger=render_logger
        )
        
        for c in clips: c.close()
        final_video.close()
        return final_path

    def _update_progress(self, p, msg):
        if self.progress_callback:
            self.progress_callback(p, msg)
