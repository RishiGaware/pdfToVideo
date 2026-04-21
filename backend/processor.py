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

def split_sentences(text):
    """Basic sentence splitter."""
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    return [s.strip() for s in sentences if len(s.strip()) > 5]

def process_pdf_to_video(pdf_path, output_dir, job_id, progress_callback=None):
    """End-to-end minimal processor (Silent Version)."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Extract and Split
    text = extract_text(pdf_path)
    sentences = split_sentences(text)
    
    if not sentences:
        raise ValueError("No readable text found in PDF.")

    # 2. Use Pandas to manage data
    df = pd.DataFrame({'text': sentences})
    total = len(df)
    clips = []

    # 3. Create Silent Clips
    for i, row in df.iterrows():
        try:
            # Create TextClip
            txt_clip = TextClip(
                text=row['text'],
                font_size=50,
                color='white',
                bg_color='black',
                size=(1280, 720),
                method='caption'
            ).with_duration(DEFAULT_DURATION)
            
            clips.append(txt_clip)
            
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
