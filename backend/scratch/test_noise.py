import sys
import os
import fitz

# Add backend to path to import app
sys.path.append(r'c:\Users\rishi.gaware\Desktop\pdfToVideo\backend')

from app.engine.cleaner import TrainingContentCleaner

def test_cleaner(pdf_path):
    print(f"Testing cleaner on: {pdf_path}")
    doc = fitz.open(pdf_path)
    cleaner = TrainingContentCleaner(doc)
    
    print("\nDetected Headers/Footers (Exact):")
    for noise in sorted(list(cleaner.header_footers)):
        print(f" - '{noise}'")
    
    print("\nDetected Noise Templates (Normalized):")
    for template in sorted(list(cleaner.noise_templates)):
        print(f" - '{template}'")
    
    # Test cleaning on sample marginal blocks
    print("\nTesting clean_block on marginal blocks:")
    for p_idx, page in enumerate(doc):
        h = page.rect.height
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            if not text: continue
            is_marginal = b[1] < h * 0.12 or b[3] > h * 0.88
            if is_marginal:
                cleaned = cleaner.clean_block(text, b[:4], h)
                status = "[KEPT]" if cleaned else "[REMOVED]"
                print(f" Page {p_idx}: {status} '{text}'")

if __name__ == "__main__":
    pdf_dir = r'c:\Users\rishi.gaware\Desktop\pdfToVideo\backend\temp'
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    if pdfs:
        test_cleaner(os.path.join(pdf_dir, pdfs[0]))
    else:
        print("No PDF found in temp/")
