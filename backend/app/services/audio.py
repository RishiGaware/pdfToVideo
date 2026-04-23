import edge_tts
import asyncio
import os
import logging
import re

from .utils import normalize_for_speech

logger = logging.getLogger(__name__)

class AudioEngine:
    """Generates narration using Edge-TTS in an asynchronous manner."""

    def __init__(self, voice="en-IN-NeerjaNeural"):
        self.voice = voice
        self.rate = "+0%"
        self.semaphore = asyncio.Semaphore(10)

    def clean_text_for_tts(self, text: str) -> str:
        """Clean and normalize text for better narration."""

        # --- STEP 0: Normalize symbols ---
        text = normalize_for_speech(text)

        # --- STEP 3: Replace bullets with pauses ---
        text = re.sub(r'[•●▪\-]', '. ', text)

        # --- STEP 4: Fix encoding issues ---
        text = text.replace('□', ' ')
        text = text.replace('\n', '. ')

        # --- STEP 5: Keep useful punctuation ---
        text = re.sub(r'[^a-zA-Z0-9\s\.\,\?\!\-\:\(\)%]', ' ', text)

        # --- STEP 6: Normalize spaces ---
        text = re.sub(r'\s+', ' ', text).strip()

        # --- STEP 8: Fallback ---
        if not text or len(text) < 5:
            text = "Moving to the next section."

        # --- STEP 9: Smart truncation ---
        if len(text) > 2000:
            text = text[:2000]
            if '.' in text:
                text = text.rsplit('.', 1)[0] + '.'

        return text

    async def generate(self, text, output_path, on_item_complete=None):
        """Generate audio for a single scene."""
        clean_text = self.clean_text_for_tts(text)

        try:
            async with self.semaphore:
                communicate = edge_tts.Communicate(
                    clean_text,
                    self.voice,
                    rate=self.rate
                )
                await communicate.save(output_path)

            if on_item_complete:
                on_item_complete()

            return output_path

        except Exception as e:
            logger.error(f"Edge-TTS failed for text '{clean_text[:100]}...': {e}")
            raise

    async def batch_generate(self, scenes, output_dir, on_item_complete=None):
        """Generate audio for multiple scenes in parallel."""
        os.makedirs(output_dir, exist_ok=True)

        tasks = []

        for scene in scenes:
            narr = scene.get("narration", "").strip()

            if not narr:
                narr = f"Moving to {scene.get('title', 'next section')}"
                scene["narration"] = narr

            path = os.path.join(output_dir, f"audio_{scene['id']}.mp3")

            scene["audio_path"] = path
            tasks.append(self.generate(narr, path, on_item_complete))

        await asyncio.gather(*tasks)

        return scenes