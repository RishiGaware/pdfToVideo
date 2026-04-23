import re
import textwrap
from .utils import FILLER_WORDS_REGEX, COMMON_ABBREVIATIONS, clean_leading_markers

class TrainingTransformer:
    """Transforms raw document text into punchy training bullets."""
    
    def __init__(self, max_lines=13, wrap_width=100):
        self.max_lines = max_lines
        self.wrap_width = wrap_width
        
        # Build dynamic splitting regex from shared abbreviations
        # e.g. (?<!\bNo\.)(?<!\bSr\.)
        lookbehinds = "".join([f"(?<!{p})" for p in COMMON_ABBREVIATIONS.keys()])
        self.split_regex = rf"{lookbehinds}(?<=[.!?])\s+"

    def _estimate_lines(self, text):
        """Estimate how many lines this text will take when wrapped."""
        if not text: return 0
        wrapped = textwrap.wrap(text, width=self.wrap_width)
        return len(wrapped)

    def transform_to_slides(self, topic_data):
        """Converts a single topic into one or more training slides using line-budgeting."""
        title = topic_data["title"]
        full_text = " ".join(topic_data["content"])
        
        # 1. Normalize and split text
        # Step A: Convert markers like * or • into sentence boundaries if they aren't already
        full_text = re.sub(r'\s*[\*\u2022]\s*', '. ', full_text)
        
        # Step B: Split into sentences using shared abbreviation lookbehind
        sentences = re.split(self.split_regex, full_text)
        raw_bullets = [s.strip() for s in sentences if len(s.strip()) > 5]
        
        # 2. Refine bullets
        refined_bullets = []
        for b in raw_bullets:
            clean_b = self._summarize_sentence(b)
            if clean_b:
                refined_bullets.append(clean_b)
        
        # 3. Smart Chunking (Line-Budgeting)
        slides = []
        current_chunk = []
        current_line_count = 0
        
        for bullet in refined_bullets:
            bullet_lines = self._estimate_lines(bullet) + 1 # +1 for the margin/spacing between bullets
            
            # If adding this bullet exceeds the budget, close the current slide
            if current_line_count + bullet_lines > self.max_lines and current_chunk:
                slides.append({
                    "title": title,
                    "bullets": current_chunk,
                    "has_tables": False, # Tables handled in first slide usually
                    "tables": []
                })
                current_chunk = []
                current_line_count = 0
                
            current_chunk.append(bullet)
            current_line_count += bullet_lines
            
        # Add final chunk
        if current_chunk:
            # Handle tables (usually put them in the first slide of the topic)
            has_tables = len(topics_tables := topic_data.get("tables", [])) > 0
            
            slides.append({
                "title": title,
                "bullets": current_chunk,
                "has_tables": has_tables if len(slides) == 0 else False,
                "tables": topics_tables if len(slides) == 0 else []
            })
            
        # Fallback for topics with no sentences (e.g. just a heading or table)
        if not slides:
            slides.append({
                "title": title,
                "bullets": ["Module details provided in visual.", "Review document for context."] if not topic_data["tables"] else [],
                "has_tables": len(topic_data.get("tables", [])) > 0,
                "tables": topic_data.get("tables", [])
            })
            
        return slides

    def _summarize_sentence(self, sentence):
        """Clean up sentence for bullet formatting while preserving ALL content."""
        # 1. Remove introductory filler words only (Using shared regex)
        clean = re.sub(FILLER_WORDS_REGEX, '', sentence, flags=re.IGNORECASE).strip()
        
        # 2. Strip leading bullet markers like *, -, or . (Using shared helper)
        clean = clean_leading_markers(clean)
        
        # 3. Capitalize first letter
        clean = clean[0].upper() + clean[1:] if clean else ""
        
        # 4. Standardize trailing punctuation for slides
        clean = re.sub(r'[.!?]$', '', clean)
        
        return clean.strip()
