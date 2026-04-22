import sys
import os
sys.path.append(os.getcwd())

from app.engine.analyzer import DocumentAnalyzer
import fitz

# Mocking a document is hard, let's just inspect the logic on a real one if available
# We will use the user's report PDF if found, or just do a unit test on the logic

def test_heading_logic():
    # Mock span data similar to what's in the user's report
    # Case: PROBLEM DEFINITION / DESCRIPTION: (Bold, Caps, Colon)
    spans = [
        {"text": "PROBLEM DEFINITION / DESCRIPTION:", "size": 10.0, "flags": 16, "font": "Arial-BoldMT"}
    ]
    
    line_text = " ".join([s["text"] for s in spans]).strip()
    max_size = max([s["size"] for s in spans])
    is_bold = any((s["flags"] & 16) or "bold" in s["font"].lower() for s in spans)
    is_all_caps = line_text.isupper() and len(line_text) > 3
    has_colon = line_text.endswith(":")
    
    body_size = 10.0 # Same as heading
    heading_size = 15.0 # Much larger
    
    score = 0
    if max_size > body_size * 1.15: score += 2
    if is_bold: score += 1
    if is_all_caps: score += 0.5
    if has_colon: score += 1
    
    etype = "paragraph"
    if max_size > heading_size * 1.1:
        etype = "title"
    elif score >= 1.5 and len(line_text.split()) < 12:
        etype = "heading"
        
    print(f"Text: {line_text}")
    print(f"Score: {score}")
    print(f"Result Type: {etype}")

if __name__ == "__main__":
    test_heading_logic()
