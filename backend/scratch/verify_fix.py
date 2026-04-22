import sys
import os
import fitz

# Add backend to path to import app
sys.path.append(r'c:\Users\rishi.gaware\Desktop\pdfToVideo\backend')

from app.engine.cleaner import TrainingContentCleaner

def create_test_pdf(path):
    doc = fitz.open()
    for i in range(5):
        page = doc.new_page()
        # Header (Fixed)
        page.insert_text((50, 50), "COMPANY CONFIDENTIAL REPORT")
        # Body
        page.insert_text((50, 200), f"This is the body content of page {i+1}.")
        # Footer (Dynamic)
        page.insert_text((50, 750), f"ID-12345-ABC | Page {i+1} of 5 | Ref: SOP-99")
    doc.save(path)
    doc.close()

def test_on_generated():
    pdf_path = "test_generated.pdf"
    create_test_pdf(pdf_path)
    
    doc = fitz.open(pdf_path)
    cleaner = TrainingContentCleaner(doc)
    
    print(f"Testing on generated PDF: {pdf_path}")
    print("\nDetected Headers/Footers (Exact):")
    for noise in sorted(list(cleaner.header_footers)):
        print(f" - '{noise}'")
    
    print("\nDetected Noise Templates (Normalized):")
    for template in sorted(list(cleaner.noise_templates)):
        print(f" - '{template}'")
    
    print("\nCleaning Results:")
    for p_idx in range(len(doc)):
        page = doc[p_idx]
        h = page.rect.height
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            cleaned = cleaner.clean_block(text, b[:4], h)
            status = "[REMOVED]" if not cleaned else "[KEPT]"
            print(f" Page {p_idx}: {status} '{text}'")
            
    doc.close()
    os.remove(pdf_path)

if __name__ == "__main__":
    test_on_generated()
