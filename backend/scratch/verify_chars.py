import sys
import os
import fitz

# Add backend to path to import app
sys.path.append(r'c:\Users\rishi.gaware\Desktop\pdfToVideo\backend')

from app.engine.cleaner import TrainingContentCleaner

class MockBbox:
    def __getitem__(self, idx):
        return 200 if idx == 1 else 300

def test_character_replacement():
    doc = fitz.open() # Dummy doc
    cleaner = TrainingContentCleaner(doc)
    
    # Text with non-breaking hyphens (U+2011) and other special chars
    test_text = "02\u2011Mar\u20112026, Bag\u2011in\u2011Bottle, de\u2011cartoning room, AHMFV\u201126\u201103"
    print(f"Original text: {test_text.encode('unicode_escape')}")
    
    # Mock bbox in the middle of a 720h page
    bbox = [100, 200, 500, 250]
    page_height = 720
    
    cleaned = cleaner.clean_block(test_text, bbox, page_height)
    print(f"Cleaned text:  {cleaned}")
    
    if "\u2011" not in cleaned and "-" in cleaned:
        print("SUCCESS: Non-breaking hyphens replaced with standard hyphens.")
    else:
        print("FAILURE: Characters not replaced correctly.")

    # Test other characters
    other_text = "\u201cSmart Quotes\u201d and En\u2013Dash and Bullet \u2022"
    cleaned_other = cleaner.clean_block(other_text, bbox, page_height)
    print(f"Original other: {other_text.encode('unicode_escape')}")
    print(f"Cleaned other:  {cleaned_other}")

if __name__ == "__main__":
    test_character_replacement()
