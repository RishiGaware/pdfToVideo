import fitz
import pdfplumber
from collections import Counter
import logging
import re
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

    def get_structure(self):
        """Extract elements and map to topics with multi-signal heading detection."""
        elements = []
        body_size = self.font_stats.most_common(1)[0][0] if self.font_stats else 12.0
        
        for page_num, page in enumerate(self.doc):
            page_height = page.rect.height
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b["type"] == 0:
                    for line in b["lines"]:
                        bbox = line["bbox"]
                        
                        # Extract detailed span info
                        line_text = " ".join([s["text"] for s in line["spans"]]).strip()
                        max_size = max([s["size"] for s in line["spans"]])
                        
                        # Detect Bold: MuPDF flags & 16 is bold, or font name has 'bold'
                        is_bold = any((s["flags"] & 16) or "bold" in s["font"].lower() for s in line["spans"])
                        is_all_caps = line_text.isupper() and len(line_text) > 3
                        has_colon = line_text.endswith(":") or re.search(r":[ \t]*$", line_text)
                        
                        # Clean and filter noise
                        cleaned_text = self.cleaner.clean_block(line_text, bbox, page_height)
                        if not cleaned_text: continue
                        
                        # HEADING SCORING LOGIC
                        etype = "paragraph"
                        score = 0
                        if max_size > body_size * 1.15: score += 2 # Strong size signal
                        if is_bold: score += 1
                        if is_all_caps: score += 1.5 # Boosted for capitalized sections
                        if has_colon: score += 1
                        
                        # Titles are extra large
                        if max_size > self.heading_size * 1.1:
                            etype = "title"
                        # Headings must be punchy (not too long)
                        elif score >= 1.5 and len(cleaned_text.split()) < 15:
                            etype = "heading"
                        elif abs(max_size - self.heading_size) < 1.0:
                            etype = "heading"
                        
                        elements.append({
                            "type": etype,
                            "text": cleaned_text,
                            "page": page_num,
                            "size": max_size
                        })
        
        # PRIMARY TITLE INJECTION
        # Use the logical header found by the cleaner as the global video title.
        if self.cleaner.primary_header:
            elements.insert(0, {
                "type": "title",
                "text": self.cleaner.primary_header,
                "page": 0,
                "size": self.heading_size * 1.5 # Visual emphasis
            })
            logger.info(f"Used primary header as video title: {self.cleaner.primary_header}")
            
        return elements

class TableAnalyzer:
    """Uses pdfplumber to detect structural tables."""
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def get_tables(self):
        tables = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                extracted = page.extract_tables()
                if extracted:
                    # Simple heuristic to identify layout/header tables
                    heading_keywords = ["PROBLEM DEFINITION", "OBJECTIVE", "SCOPE", "SUMMARY", "DESCRIPTION"]
                    
                    for table in extracted:
                        # Filter out empty tables
                        clean_table = [[col or "" for col in row] for row in table if any(row)]
                        if not clean_table: continue
                        
                        # Check if table represents a layout header (redundant info)
                        table_str = " ".join([" ".join(row) for row in clean_table]).upper()
                        is_layout = any(kw in table_str for kw in heading_keywords) and len(clean_table) <= 6
                        
                        if not is_layout:
                            tables.append({
                                "page": page_num,
                                "data": clean_table
                            })
        return tables
