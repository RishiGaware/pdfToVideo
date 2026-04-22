import re

class TrainingTransformer:
    """Transforms raw document text into punchy training bullets."""
    
    def __init__(self, max_bullets=5, max_words=12):
        self.max_bullets = max_bullets
        self.max_words = max_words

    def transform_to_slides(self, topic_data):
        """Converts a single topic into one or more training slides."""
        title = topic_data["title"]
        full_text = " ".join(topic_data["content"])
        
        # 1. Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', full_text)
        raw_bullets = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # 2. Refine bullets (summarization heuristic)
        refined_bullets = []
        for b in raw_bullets:
            # Simplify bullet: remove transitions and trim to max words
            clean_b = self._summarize_sentence(b)
            if clean_b:
                refined_bullets.append(clean_b)
        
        # 3. Chunk into slides (max_bullets per slide)
        slides = []
        for i in range(0, len(refined_bullets), self.max_bullets):
            chunk = refined_bullets[i : i + self.max_bullets]
            
            # Label parts if multiple slides
            part_title = title
            if len(refined_bullets) > self.max_bullets:
                part_idx = (i // self.max_bullets) + 1
                part_title += f" (Part {part_idx})"
                
            slides.append({
                "title": part_title,
                "bullets": chunk,
                "has_tables": len(topic_data.get("tables", [])) > 0 if i == 0 else False,
                "tables": topic_data.get("tables", []) if i == 0 else []
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
        # 1. Remove introductory filler words only
        fillers = r'^(Therefore|Additionally|Furthermore|In addition|Generally|Notably|It should be noted that|Please note that|Observe that)\s*,?\s*'
        clean = re.sub(fillers, '', sentence, flags=re.IGNORECASE).strip()
        
        # 2. Capitalize first letter
        clean = clean[0].upper() + clean[1:] if clean else ""
        
        # 3. Preserve full text (no truncation)
        # 4. Standardize trailing punctuation for slides
        clean = re.sub(r'[.!?]$', '', clean)
        
        return clean.strip()
