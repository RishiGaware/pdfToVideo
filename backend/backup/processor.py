import os
import re
import pandas as pd
import numpy as np
import fitz  # PyMuPDF
from moviepy import TextClip, concatenate_videoclips, CompositeVideoClip
from proglog import ProgressBarLogger
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DEFAULT_DURATION = 3.5  # Fixed duration for silent segments

class MoviePyProgressLogger(ProgressBarLogger):
    """Capture MoviePy rendering progress and map it to the 81-100% range."""
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
                scaled = 80 + int(pct * 0.20)
                self.on_progress(scaled)
                self.last_pct = pct

def extract_text(pdf_path):
    """Simple PDF text extraction."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def chunk_text_by_context(text, max_chars=800):
    """Group sentences into larger paragraph-like chunks for SOP display."""
    # Split by double newlines first to honor original paragraph structure
    paragraphs = text.split('\n\n')
    chunks = []
    
    for para in paragraphs:
        para = para.strip().replace('\n', ' ')
        if not para: continue
        
        # If the paragraph itself is huge, split it into smaller chunks
        if len(para) > max_chars:
            raw_sentences = re.split(r'(?<=[.!?])\s+', para)
            current_chunk = ""
            for sentence in raw_sentences:
                if len(current_chunk) + len(sentence) > max_chars and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk = (current_chunk + " " + sentence).strip()
            if current_chunk:
                chunks.append(current_chunk)
        else:
            chunks.append(para)
    
    return chunks

def build_segment_clip(text: str):
    """Build a single silent segment clip (480p for MAX SPEED)."""
    # 1. Dynamic Duration: Slightly faster reading pace
    duration = max(3.0, len(text) / 25.0)
    
    # 2. Font Scaling: Adjusted for 480p (854x480)
    font_size = 30
    if len(text) > 600: font_size = 18
    elif len(text) > 300: font_size = 24

    # 3. Create TextClip (854x480 Resolution)
    txt_clip = TextClip(
        text=text,
        font_size=font_size,
        color='black',
        bg_color='white',
        size=(854, 480),
        method='caption',
        text_align='center'
    ).with_duration(duration)
    
    return txt_clip

def process_pdf_to_video(pdf_path, output_dir, job_id, progress_callback=None):
    """End-to-end minimal processor (Silent Version with Grouped Context)."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Extract and Chunk
    text = extract_text(pdf_path)
    chunks = chunk_text_by_context(text)
    
    if not chunks:
        raise ValueError("No readable text found in PDF.")

    # 2. Use Pandas to manage data
    df = pd.DataFrame({'text': chunks})
    total = len(df)
    clips = []

    # 3. Create Silent Clips with dynamic logic
    for i, row in df.iterrows():
        try:
            clip = build_segment_clip(row['text'])
            clips.append(clip)
            
            if progress_callback:
                progress_callback(int((i + 1) / total * 80)) 
        except Exception as e:
            logger.error(f"Error processing segment {i}: {e}")

    if not clips:
        raise ValueError("Failed to generate any clips.")

    # 4. Final Assembly
    final_video = concatenate_videoclips(clips, method="compose")
    video_path = os.path.join(output_dir, "final.mp4")
    
    render_logger = MoviePyProgressLogger(progress_callback) if progress_callback else None

    final_video.write_videofile(
        video_path, 
        fps=12, 
        codec="libx264", 
        audio=False, # Disable audio
        preset="ultrafast",
        threads=1,
        logger=render_logger
    )
    
    if progress_callback:
        progress_callback(100)
    
    # Cleanup
    for c in clips:
        c.close()
    final_video.close()
    
    return video_path
