import fitz
import re
import ftfy
from collections import Counter
from .utils import DOCUMENT_NOISE_PATTERNS, HEADER_ZONE_PERCENT, FOOTER_ZONE_PERCENT

class TrainingContentCleaner:
    """Advanced cleanup for raw PDF text into training-ready content."""
    
    def __init__(self, doc: fitz.Document):
        self.doc = doc
        self.header_footers, self.noise_templates, self.primary_header, self.position_noise = self._identify_noise()

    def _normalize(self, text):
        """Normalize text by replacing digits with # for template matching."""
        return re.sub(r'\d+', '#', text.strip())

    def _identify_noise(self):
        """Detect headers, footers, and position-locked repetitive noise."""
        block_counts = Counter()
        top_marginal_counts = Counter()
        template_counts = Counter()
        position_counts = Counter() # (rounded_x, rounded_y, text) -> frequency
        
        potential_noise = set()
        potential_templates = set()
        position_noise = set()
        
        # Sample pages
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
                
                # 1. Zone-based Repetition (Headers/Footers)
                is_marginal = b[1] < h * HEADER_ZONE_PERCENT or b[3] > h * (1 - FOOTER_ZONE_PERCENT)
                if is_marginal:
                    block_counts[text] += 1
                    template_counts[self._normalize(text)] += 1
                    if b[1] < h * HEADER_ZONE_PERCENT:
                        top_marginal_counts[text] += 1
                
                # 2. Position-Locked Repetition (Watermarks, sidebars, internal templates)
                # We round by 5px to handle minor rendering offsets
                pos_key = (int(b[0] // 5), int(b[1] // 5), text)
                position_counts[pos_key] += 1

        # Thresholds
        threshold = max(2, len(sample_pages) // 3)
        strong_threshold = max(2, int(len(sample_pages) * 0.5)) # Must appear in >50% of samples
        
        for text, count in block_counts.items():
            if count >= threshold:
                potential_noise.add(text)
        
        for template, count in template_counts.items():
            if count >= threshold:
                potential_templates.add(template)

        for pos_key, count in position_counts.items():
            if count >= strong_threshold:
                position_noise.add(pos_key)
        
        # Determine the primary header
        primary_header = None
        if top_marginal_counts:
            most_common = top_marginal_counts.most_common(1)[0]
            if most_common[1] >= threshold:
                primary_header = most_common[0]
        
        return potential_noise, potential_templates, primary_header, position_noise

    def clean_block(self, text, bbox, page_height):
        """Determine if a block should be kept and clean its text."""
        text = text.strip()
        if not text: return None

        # 0. Check for Position-Locked Noise (Smart analyzer)
        pos_key = (int(bbox[0] // 5), int(bbox[1] // 5), text)
        if pos_key in self.position_noise:
            return None

        # 1. Strict artifact removal
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.I)
        text = re.sub(r'Ref\.?\s*SOP.*', '', text, flags=re.I)
        
        # 2. Check for detected headers/footers (Exact match)
        if text.strip() in self.header_footers:
            return None
            
        # 3. Check for normalized noise templates
        if self._normalize(text) in self.noise_templates:
            return None

        # 4. Check for specific page numbering / common noise patterns (Always ignore)
        if any(re.search(p, text, re.I) for p in DOCUMENT_NOISE_PATTERNS):
            return None

        # 5. Fix encoding and symbols
        text = ftfy.fix_text(text)
        
        # 6. Replace special hyphens and problematic characters
        special_chars = {
            '\u2011': '-', '\u2010': '-', '\u2013': '-', '\u2014': '--',
            '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
            '\u00a0': ' ', '\u2022': '*', '\u2212': '-'
        }
        for char, replacement in special_chars.items():
            text = text.replace(char, replacement)

        # 7. FINAL STRICT CLEANING (Remove non-ASCII and collapse spaces)
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # remove weird chars
        text = re.sub(r'\s+', ' ', text)
        
        cleaned = text.strip()
        return cleaned if cleaned else None
