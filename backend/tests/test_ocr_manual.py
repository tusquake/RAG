
import os
import sys
import unittest
from PIL import Image, ImageDraw, ImageFont

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pdf_processor import PDFProcessor

class TestOCR(unittest.TestCase):
    def test_ocr_extraction(self):
        # 1. Create an image with text
        img = Image.new('RGB', (500, 200), color = (255, 255, 255))
        d = ImageDraw.Draw(img)
        # Use default font
        d.text((10,10), "This is a test of OCR functionality", fill=(0,0,0))
        
        # 2. Save as PDF (image-based PDF)
        pdf_path = "test_ocr.pdf"
        img.save(pdf_path, "PDF", resolution=100.0)
        
        try:
            # 3. Process it
            processor = PDFProcessor()
            # We call the sync method directly for testing
            result = processor._extract_sync(pdf_path)
            
            print(f"Extracted Text: {result['text']}")
            
            # 4. Verify
            self.assertIn("OCR", result['text'])
            self.assertIn("functionality", result['text'])
            print("SUCCESS: OCR correctly extracted text from image-based PDF!")
            
        finally:
            # Cleanup
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

if __name__ == '__main__':
    unittest.main()
