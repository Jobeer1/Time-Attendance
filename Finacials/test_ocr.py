"""
Test script for OCR configuration - Word-for-word extraction
Run this to test different OCR settings on a sample image
"""
import os
import sys
from PIL import Image
import pytesseract

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ocr_service import OCRService

def test_ocr_configs():
    """Test different OCR configurations"""
    
    # Initialize OCR service
    ocr_service = OCRService()
    
    print("🧪 Testing OCR Configurations")
    print("=" * 50)
    
    # Test configurations
    test_configs = {
        'Balanced (Default)': r'--oem 3 --psm 3 -c preserve_interword_spaces=1',
        'Full Page Auto': r'--oem 3 --psm 1',
        'Uniform Blocks': r'--oem 3 --psm 6',
        'Single Text Line': r'--oem 3 --psm 8',
        'Raw Line Detection': r'--oem 3 --psm 13',
        'Simple Default': r'--oem 3 --psm 3'
    }
    
    # You can test with any image file - replace this path
    test_image_path = input("Enter path to test image (or press Enter to skip): ").strip()
    
    if test_image_path and os.path.exists(test_image_path):
        try:
            img = Image.open(test_image_path)
            print(f"\n📄 Testing with image: {test_image_path}")
            print("=" * 50)
            
            for config_name, config in test_configs.items():
                print(f"\n🔧 Testing: {config_name}")
                print(f"Config: {config}")
                print("-" * 30)
                
                try:
                    text = pytesseract.image_to_string(img, lang='eng', config=config)
                    lines = text.splitlines()
                    
                    print(f"Lines extracted: {len(lines)}")
                    print("First 5 lines:")
                    for i, line in enumerate(lines[:5]):
                        if line.strip():
                            print(f"  {i+1}: {line}")
                    
                    if len(lines) > 5:
                        print(f"  ... and {len(lines)-5} more lines")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
                
                print("-" * 30)
        
        except Exception as e:
            print(f"❌ Error loading image: {e}")
    
    else:
        print("⚠️ No test image provided. Showing configuration details only.")
    
    print("\n📋 Configuration Explanations:")
    print("=" * 50)
    explanations = {
        'PSM 3': 'Fully automatic page segmentation (default)',
        'PSM 6': 'Uniform block of text (good for tables/forms)',
        'PSM 8': 'Single text word',
        'PSM 13': 'Raw line detection (minimal processing)',
        'preserve_interword_spaces=1': 'Keep original spacing between words',
        'textord_really_old_xheight=1': 'Better handling of different text heights',
        'textord_tabfind_show_vlines=0': 'Disable vertical line detection'
    }
    
    for param, explanation in explanations.items():
        print(f"  {param}: {explanation}")

if __name__ == "__main__":
    test_ocr_configs()
