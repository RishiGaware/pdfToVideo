import fitz
import re
import ftfy
from collections import Counter

class TrainingContentCleaner:
    """Advanced cleanup for raw PDF text into training-ready content."""
    
    def __init__(self, doc: fitz.Document):
        self.doc = doc
        self.header_footers, self.noise_templates = self._identify_noise()

    def _normalize(self, text):
        """Normalize text by replacing digits with # for template matching."""
        return re.sub(r'\d+', '#', text.strip())

    def _identify_noise(self):
        """Detect headers, footers, and page numbers by cross-page repetition."""
        block_counts = Counter()
        template_counts = Counter()
        potential_noise = set()
        potential_templates = set()
        
        # Sample pages (all if < 30, else first 15 + last 15)
        sample_pages = range(len(self.doc))
        if len(self.doc) > 30:
            sample_pages = list(range(15)) + list(range(len(self.doc) - 15, len(self.doc)))

        for p_idx in sample_pages:
            page = self.doc[p_idx]
            h = page.rect.height
            blocks = page.get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                if not text: continue
                # Noise is usually at top (0-12%) or bottom (88-100%)
                is_marginal = b[1] < h * 0.12 or b[3] > h * 0.88
                if is_marginal:
                    block_counts[text] += 1
                    template_counts[self._normalize(text)] += 1

        # Threshold: if it appears in multiple sample pages relative to doc length
        # For small docs (2-5 pages), threshold is 2. For larger, it's roughly 1/3 of sample.
        threshold = max(2, len(sample_pages) // 3)
        
        for text, count in block_counts.items():
            if count >= threshold:
                potential_noise.add(text)
        
        for template, count in template_counts.items():
            if count >= threshold:
                potential_templates.add(template)
        
        return potential_noise, potential_templates

    def clean_block(self, text, bbox, page_height):
        """Determine if a block should be kept and clean its text."""
        text = text.strip()
        if not text: return None
        
        # 1. Check for detected headers/footers (Exact match)
        if text in self.header_footers:
            return None
            
        # 2. Check for normalized noise templates
        if self._normalize(text) in self.noise_templates:
            # Only remove if it's in the margin (Extra safety for templates)
            if bbox[1] < page_height * 0.12 or bbox[3] > page_height * 0.88:
                return None

        # 3. Check for specific page numbering / common noise patterns
        # Use re.search instead of re.match to catch partial matches in margins
        page_patterns = [
            r'Page\s+\d+', r'\d+\s+of\s+\d+', 
            r'^Ref\.\s+SOP\s+No\.', r'^\d+$', 
            r'Confidential', r'Property of'
        ]
        if any(re.search(p, text, re.I) for p in page_patterns):
            # Only remove if it's in the margin
            if bbox[1] < page_height * 0.12 or bbox[3] > page_height * 0.88:
                return None

        # 4. Use ftfy to fix encoding issues and mojibake
        text = ftfy.fix_text(text)
        
        # 5. Replace special hyphens and other problematic characters for rendering
        special_chars = {
            '\u2011': '-', '\u2010': '-', '\u2013': '-', '\u2014': '--',
            '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
            '\u00a0': ' ', '\u2022': '*', '\u2212': '-'
        }
        for char, replacement in special_chars.items():
            text = text.replace(char, replacement)

        # 6. Remove common artifacts like repeated underscores, weird squares
        text = text.replace('□', '')
        text = re.sub(r'_{3,}', '', text)
        
        return text.strip()
