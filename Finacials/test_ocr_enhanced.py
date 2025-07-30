"""
Enhanced test script for the new OCR service.
Tests table extraction and CSV formatting capabilities.
"""

import os
import sys
sys.path.append('.')

from services.ocr_service import OCRService

def test_ocr_service(image_path=None):
    """Test the new OCR service with table extraction capabilities"""
    
    print("🧪 Testing Enhanced OCR Service for Financial Reports")
    print("=" * 60)
    
    # Initialize OCR service
    ocr_service = OCRService()
    
    # Show target format first
    show_target_format()
    
    if not image_path:
        image_path = input("\nEnter path to test image: ").strip()
    
    if not image_path or not os.path.exists(image_path):
        print("⚠️ No valid image provided. Testing configurations only.")
        show_configuration_details()
        return
    
    print(f"\n📄 Processing image: {image_path}")
    print("-" * 60)
    
    try:
        # Test structured data extraction
        print("\n🔍 Extracting structured data...")
        csv_output = ocr_service.extract_structured_data(image_path)
        
        print("\n📊 CSV Output:")
        print("=" * 40)
        print(csv_output)
        
        # Save output to file
        output_file = f"test_output_{os.path.basename(image_path)}.csv"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(csv_output)
        print(f"\n💾 Output saved to: {output_file}")
        
        # Analyze output quality
        analyze_output_quality(csv_output)
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

def show_target_format():
    """Show the target CSV format we're aiming for"""
    target_file = "page1_corrected.csv"
    
    print("\n🎯 Target Format:")
    print("-" * 30)
    
    if os.path.exists(target_file):
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        print("First 10 lines of target format:")
        for i, line in enumerate(lines[:10]):
            print(f"  {i+1}: {line}")
        
        if len(lines) > 10:
            print(f"  ... and {len(lines)-10} more lines")
    else:
        print("Expected format example:")
        print("  Report_Header,PROMED REP-SP0050X")
        print("  Run_Date,25.06.25")
        print("  Doctor,DR. C.I. STOYANOV")
        print("  Report_Type,SELECTED MEDICAL AID LISTING")
        print("  Page_Number,1")
        print("  Medical_Aid,JUN - QUARTERLY WRITE OFFS")
        print("  ")
        print("  Account_ID,Account_Name,Last_Visit,...")
        print("  10303073,PRIVATE BAG X4216 S,07.03.22,...")

def analyze_output_quality(csv_output):
    """Analyze the quality of the CSV output"""
    print("\n📈 Output Quality Analysis:")
    print("-" * 30)
    
    lines = csv_output.split('\n')
    
    # Count different types of lines
    metadata_lines = 0
    header_line_found = False
    data_lines = 0
    empty_lines = 0
    
    for line in lines:
        if not line.strip():
            empty_lines += 1
        elif ',' in line:
            if 'Account_ID' in line:
                header_line_found = True
            elif any(key in line for key in ['Report_Header', 'Run_Date', 'Doctor', 'Report_Type', 'Page_Number', 'Medical_Aid']):
                metadata_lines += 1
            else:
                data_lines += 1
    
    print(f"  ✅ Metadata lines: {metadata_lines}")
    print(f"  ✅ Header line found: {header_line_found}")
    print(f"  ✅ Data lines: {data_lines}")
    print(f"  📝 Empty lines: {empty_lines}")
    print(f"  📊 Total lines: {len(lines)}")
    
    # Check for common patterns
    has_account_ids = any('E027' in line or 'N003' in line or '1030' in line for line in lines)
    has_amounts = any('.' in line and any(c.isdigit() for c in line) for line in lines)
    has_dates = any('.' in line and len([p for p in line.split('.') if p.isdigit()]) >= 2 for line in lines)
    
    print(f"  🆔 Contains account IDs: {has_account_ids}")
    print(f"  💰 Contains amounts: {has_amounts}")
    print(f"  📅 Contains dates: {has_dates}")

def show_configuration_details():
    """Show details about OCR configurations"""
    print("\n⚙️ OCR Configuration Details:")
    print("-" * 40)
    
    configs = {
        'PSM 6': 'Uniform block of text - Best for structured tables',
        'PSM 4': 'Single column of text - Good for financial reports',
        'PSM 1': 'Automatic page segmentation with OSD',
        'PSM 3': 'Fully automatic page segmentation (balanced)',
        'OEM 3': 'Default OCR Engine Mode (LSTM + Legacy)',
        'preserve_interword_spaces=1': 'Maintain original spacing between words',
        'Enhanced Preprocessing': 'Noise reduction, contrast enhancement, morphological operations',
        'Simple Preprocessing': 'Gaussian blur and Otsu thresholding',
        'Minimal Preprocessing': 'Basic binary thresholding'
    }
    
    for config, description in configs.items():
        print(f"  {config}: {description}")

def test_raw_extraction(image_path):
    """Test raw text extraction for debugging"""
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"\n🔍 Raw Text Extraction Test: {image_path}")
    print("-" * 50)
    
    ocr_service = OCRService()
    
    try:
        raw_text = ocr_service.extract_raw_text(image_path)
        print(f"Text length: {len(raw_text)} characters")
        print("\nFirst 1000 characters:")
        print(raw_text[:1000])
        if len(raw_text) > 1000:
            print("\n... (truncated)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--raw" and len(sys.argv) > 2:
            test_raw_extraction(sys.argv[2])
        else:
            test_ocr_service(sys.argv[1])
    else:
        test_ocr_service()
