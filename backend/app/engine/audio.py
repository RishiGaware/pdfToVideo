import edge_tts
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

import re

class AudioEngine:
    """Generates narration using Edge-TTS in an asynchronous manner."""
    
    def __init__(self, voice="en-US-AriaNeural"):
        self.voice = voice
        self.semaphore = asyncio.Semaphore(5) # Limit to 5 parallel requests

    async def generate(self, text, output_path, on_item_complete=None):
        """Asynchronously generate audio for a text string."""
        # 1. Aggressive cleaning: Remove bullets, symbols, and non-standard characters
        # Only keep alphanumeric, spaces, and basic punctuation
        clean_text = re.sub(r'[^a-zA-Z0-9\s\.\,\?\!\-\"\']', ' ', text)
        clean_text = " ".join(clean_text.split()).strip()
        
        # 2. Safety truncation (Edge-TTS can fail on massive blocks)
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "..."

        if not clean_text or len(clean_text) < 2:
            clean_text = "Moving to the next topic."

        try:
            async with self.semaphore:
                communicate = edge_tts.Communicate(clean_text, self.voice)
                await communicate.save(output_path)
            
            if on_item_complete:
                on_item_complete()
                
            return output_path
        except Exception as e:
            logger.error(f"Edge-TTS failed for text '{clean_text[:100]}...': {e}")
            raise

    async def batch_generate(self, scenes, output_dir, on_item_complete=None):
        """Generate audio for multiple scenes in parallel with semi-concurrency."""
        os.makedirs(output_dir, exist_ok=True)
        tasks = []
        
        for scene in scenes:
            # Skip empty narration
            narr = scene.get("narration", "").strip()
            if not narr:
                scene["narration"] = f"Moving to {scene['title']}"

            path = os.path.join(output_dir, f"audio_{scene['id']}.mp3")
            tasks.append(self.generate(scene["narration"], path, on_item_complete))
            scene["audio_path"] = path
            
        await asyncio.gather(*tasks)
        return scenes
