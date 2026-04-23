import fitz
import pdfplumber
import re
from collections import Counter
import logging
from .utils import DOCUMENT_NOISE_PATTERNS, HEADER_ZONE_PERCENT, FOOTER_ZONE_PERCENT
from app.services.cleaner import TrainingContentCleaner

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.cleaner = TrainingContentCleaner(self.doc)
        self.font_stats = self._get_font_stats()
        self.heading_size = self._detect_heading_size()

    def _get_font_stats(self):
        """Analyze font sizes across the document to find heading patterns."""
        sizes = []
        for page in self.doc:
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b["type"] == 0:  # Text block
                    for line in b["lines"]:
                        for span in line["spans"]:
                            sizes.append(round(span["size"], 1))
        return Counter(sizes)

    def _detect_heading_size(self):
        """Detect the size likely used for main headings."""
        if not self.font_stats: return 12.0
        sorted_sizes = sorted(
            [s for s, count in self.font_stats.items() if count >= 2], 
            reverse=True
        )
        body_size = self.font_stats.most_common(1)[0][0]
        for size in sorted_sizes:
            if size > body_size * 1.2:
                return size
        return body_size * 1.5

    def close(self):
        """Release the file handle."""
        if hasattr(self, 'doc'):
            self.doc.close()

    def get_structure(self):
        """Extract elements and map to topics with multi-signal heading detection."""
        # 1. Page-level table mapping for anti-collision
        table_analyzer = TableAnalyzer(self.pdf_path)
        page_table_bboxes = {}
        for t in table_analyzer.get_tables():
            p = t["page"]
            if p not in page_table_bboxes: page_table_bboxes[p] = []
            page_table_bboxes[p].append(t["bbox"])

        elements = []
        body_size = self.font_stats.most_common(1)[0][0] if self.font_stats else 12.0
        
        for page_num, page in enumerate(self.doc):
            page_height = page.rect.height
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b["type"] == 0:
                    for line in b["lines"]:
                        bbox = line["bbox"]
                        
                        # ANTI-COLLISION: Skip text if it resides inside a detected table
                        is_inside_table = False
                        for t_bbox in page_table_bboxes.get(page_num, []):
                            if bbox[0] >= t_bbox[0] and bbox[1] >= t_bbox[1] and \
                               bbox[2] <= t_bbox[2] and bbox[3] <= t_bbox[3]:
                                is_inside_table = True
                                break
                        if is_inside_table: continue
                        
                        # Extract detailed span info
                        line_text = " ".join([s["text"] for s in line["spans"]]).strip()
                        max_size = max([s["size"] for s in line["spans"]])
                        
                        # Detect Bold: MuPDF flags & 16 is bold, or font name has 'bold'
                        is_bold = any((s["flags"] & 16) or "bold" in s["font"].lower() for s in line["spans"])
                        is_all_caps = line_text.isupper() and len(line_text) > 3
                        has_colon = line_text.endswith(":") or re.search(r":[ \t]*$", line_text)
                        
                        # 3. Header/Footer Zone Filtering
                        # This covers the large SOP header tables shown in the document.
                        is_marginal = bbox[1] < page_height * HEADER_ZONE_PERCENT or bbox[3] > page_height * (1 - FOOTER_ZONE_PERCENT)
                        if is_marginal: continue
                        
                        # Clean and filter noise
                        cleaned_text = self.cleaner.clean_block(line_text, bbox, page_height)
                        if not cleaned_text: continue
                        
                        # HEADING SCORING LOGIC
                        etype = "paragraph"
                        score = 0
                        if max_size > body_size * 1.15: score += 2
                        if is_bold: score += 1
                        if is_all_caps: score += 1.5
                        if has_colon: score += 1
                        
                        # Titles are extra large
                        if max_size > self.heading_size * 1.1:
                            etype = "title"
                        # Headings: strong signals, short text
                        elif score >= 2.0 and len(cleaned_text.split()) < 15:
                            etype = "heading"
                        elif abs(max_size - self.heading_size) < 1.0:
                            etype = "heading"
                        # Subheadings: bold-only, moderate signals
                        elif score >= 1 and score < 2.0 and is_bold and len(cleaned_text.split()) < 12:
                            etype = "subheading"
                        
                        # TABLE-PROXIMITY UPGRADE: If a subheading sits directly above
                        # a content table, it's actually a section heading for that table
                        if etype == "subheading":
                            for t_bbox in page_table_bboxes.get(page_num, []):
                                # Table starts within 60px below this text
                                gap = t_bbox[1] - bbox[3]
                                if 0 < gap < 60:
                                    etype = "heading"
                                    break
                        
                        elements.append({
                            "type": etype,
                            "text": cleaned_text,
                            "page": page_num,
                            "size": max_size,
                            "bbox": bbox
                        })
        
        return elements

class TableAnalyzer:
    """Uses pdfplumber to detect structural tables."""
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def get_tables(self):
        tables = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_height = page.height
                # Use find_tables to get coordinates/bbox
                for t in page.find_tables():
                    bbox = t.bbox # (x0, y0, x1, y1)
                    
                    # 1. Zone Check: Headers typically occupy the top marginal zone
                    is_marginal_top = bbox[1] < page_height * HEADER_ZONE_PERCENT
                    
                    table_data = t.extract()
                    clean_table = [[col or "" for col in row] for row in table_data if any(row)]
                    if not clean_table: continue
                    
                    # 2. Content Heuristic: Check for generic administrative terms
                    table_str = " ".join([" ".join(row) for row in clean_table]).upper()
                    header_indicators = ["DOCUMENT", "SOP", "NO.", "REVISION", "PAGE", "OF", "APPROVED", "PREPARED", "DEPARTMENT"]
                    has_header_signal = any(kw in table_str for kw in header_indicators)
                    
                    # Skip if it's a top-marginal table with header content or administrative size
                    if is_marginal_top and (has_header_signal or len(clean_table) <= 8):
                        continue
                        
                    tables.append({
                        "page": page_num,
                        "data": clean_table,
                        "bbox": bbox
                    })
        return tables
