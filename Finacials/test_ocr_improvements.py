#!/usr/bin/env python3
"""
Test script to validate OCR service improvements for structured CSV extraction.
Tests the parsing and CSV formatting capabilities without requiring actual images.
"""

import sys
import os
from services.ocr_service import OCRService

def test_header_extraction():
    """Test header metadata extraction"""
    print("=" * 60)
    print("Testing Header Metadata Extraction")
    print("=" * 60)
    
    # Sample header text similar to what OCR might extract
    sample_header_text = """
    PROMED REP-SP0050X
    RUN DATE: 25.06.25
    DR. C.I. STOYANOV
    SELECTED MEDICAL AID LISTING
    Page 1
    JUN - QUARTERLY WRITE OFFS
    
    Account Name    Last Visit    Last Receipt Payment    Current    30 Days
    """
    
    ocr_service = OCRService()
    metadata = ocr_service.extract_header_metadata(sample_header_text)
    
    print("Extracted metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    expected_keys = ['Report_Header', 'Run_Date', 'Doctor', 'Report_Type', 'Page_Number', 'Medical_Aid']
    missing_keys = [key for key in expected_keys if key not in metadata]
    if missing_keys:
        print(f"Warning: Missing expected keys: {missing_keys}")
    else:
        print("✓ All expected metadata keys found")
    
    return metadata

def test_table_parsing():
    """Test table data parsing"""
    print("\n" + "=" * 60)
    print("Testing Table Data Parsing")
    print("=" * 60)
    
    # Sample table data similar to what OCR might extract
    sample_table_text = """
    Account_ID,Account_Name,Last_Visit,Last_Receipt_Payment,Current,30_Days,60_Days,90_Days,120_Days,150_Days,Outstanding,Address,Status,Payment_Date,ID_Number,Claim_Number,Claim_Status
    10303073,PRIVATE BAG X4216 S,07.03.22,0.00,0.00,0.00,0.00,0.00,10407.90,0.00,10407.90,PRIVATE BAG X4216 S,BAD,0.00.00,9007315300083,,CLM STM
    E0272645,ADDONS,04.09.24,-1940.10,0.00,0.00,0.00,1731.40,0.00,0.00,1731.40,26 WONDERBOOM ST,BAD,0.00.00,700220123083,96351327,CLM STM
    E0272665,AMBROX 300,02.09.24,0.00,0.00,0.00,0.00,399.70,0.00,0.00,399.70,28 WHITE EYE DAY,BAD,0.00.00,820304546082,,CLM STM
    """
    
    ocr_service = OCRService()
    table_data = ocr_service.parse_table_data(sample_table_text)
    
    print(f"Extracted {len(table_data)} table rows:")
    for i, row in enumerate(table_data):
        print(f"\nRow {i+1}:")
        for key, value in row.items():
            if value:  # Only show non-empty values
                print(f"  {key}: {value}")
    
    return table_data

def test_csv_formatting():
    """Test CSV formatting with sample data"""
    print("\n" + "=" * 60)
    print("Testing CSV Formatting")
    print("=" * 60)
    
    # Sample metadata and table data
    sample_metadata = {
        'Report_Header': 'PROMED REP-SP0050X',
        'Run_Date': '25.06.25',
        'Doctor': 'DR. C.I. STOYANOV',
        'Report_Type': 'SELECTED MEDICAL AID LISTING',
        'Page_Number': '1',
        'Medical_Aid': 'JUN - QUARTERLY WRITE OFFS'
    }
    
    sample_table_data = [
        {
            'Account_ID': '10303073',
            'Account_Name': 'PRIVATE BAG X4216 S',
            'Last_Visit': '07.03.22',
            'Last_Receipt_Payment': '0.00',
            'Current': '0.00',
            '30_Days': '0.00',
            '60_Days': '0.00',
            '90_Days': '0.00',
            '120_Days': '10407.90',
            '150_Days': '0.00',
            'Outstanding': '10407.90',
            'Address': 'PRIVATE BAG X4216 S',
            'Status': 'BAD',
            'Payment_Date': '0.00.00',
            'ID_Number': '9007315300083',
            'Claim_Number': '',
            'Claim_Status': 'CLM STM'
        },
        {
            'Account_ID': 'E0272645',
            'Account_Name': 'ADDONS',
            'Last_Visit': '04.09.24',
            'Last_Receipt_Payment': '-1940.10',
            'Current': '0.00',
            '30_Days': '0.00',
            '60_Days': '0.00',
            '90_Days': '1731.40',
            '120_Days': '0.00',
            '150_Days': '0.00',
            'Outstanding': '1731.40',
            'Address': '26 WONDERBOOM ST',
            'Status': 'BAD',
            'Payment_Date': '0.00.00',
            'ID_Number': '700220123083',
            'Claim_Number': '96351327',
            'Claim_Status': 'CLM STM'
        }
    ]
    
    ocr_service = OCRService()
    csv_output = ocr_service.convert_to_csv_format(sample_metadata, sample_table_data)
    
    print("Generated CSV output:")
    print("-" * 40)
    print(csv_output)
    print("-" * 40)
    
    # Validate CSV structure
    lines = csv_output.split('\n')
    print(f"\nCSV Validation:")
    print(f"  Total lines: {len(lines)}")
    print(f"  Metadata lines: 6")
    print(f"  Empty line: 1")
    print(f"  Header line: 1")
    print(f"  Data lines: {len(lines) - 8}")
    
    # Check if format matches expected structure
    if len(lines) >= 8:
        print(f"  ✓ Minimum lines present")
        if lines[6] == "":
            print(f"  ✓ Empty line separator found")
        else:
            print(f"  ✗ Missing empty line separator")
        
        header_line = lines[7]
        expected_headers = "Account_ID,Account_Name,Last_Visit,Last_Receipt_Payment,Current,30_Days,60_Days,90_Days,120_Days,150_Days,Outstanding,Address,Status,Payment_Date,ID_Number,Claim_Number,Claim_Status"
        if header_line == expected_headers:
            print(f"  ✓ Headers match expected format")
        else:
            print(f"  ✗ Headers don't match expected format")
            print(f"    Expected: {expected_headers}")
            print(f"    Got:      {header_line}")
    
    return csv_output

def test_end_to_end_simulation():
    """Test end-to-end processing with simulated OCR text"""
    print("\n" + "=" * 60)
    print("Testing End-to-End OCR Processing Simulation")
    print("=" * 60)
    
    # Simulate raw OCR text that might be extracted from a financial document
    simulated_ocr_text = """
    PROMED REP-SP0050X
    RUN DATE: 26.06.25                    Page 2
    DR. C.I. STOYANOV
    SELECTED MEDICAL AID LISTING
    JUN - QUARTERLY WRITE OFFS
    
    Account_ID    Account_Name         Last_Visit    Last_Receipt_Payment    Current    30_Days    Outstanding    Address           Status    ID_Number        Claim_Number    Claim_Status
    U02102473,BIYELA,09.07.24,-4530.90,0.00,0.00,0.00,1834.38,0.00,0.00,1834.38,435 RIVERSIDE,BAD,0.00.00,6206170818087,,CLM STM
    U02102476,BIYELA,30.08.24,-1285.20,0.00,0.00,0.00,1256.00,0.00,0.00,1256.00,HOUSE 82100 CHAPTERS EC,BAD,0.00.00,920215464086,90183843,CLM STM
    E0272648,BOOTHWAY,11.09.24,-1940.10,0.00,0.00,0.00,1731.40,0.00,0.00,1731.40,POSTNET SUITE 24C,BAD,0.00.00,700220123083,,CLM STM
    """
    
    ocr_service = OCRService()
    
    # Test the complete processing pipeline
    print("1. Extracting header metadata...")
    metadata = ocr_service.extract_header_metadata(simulated_ocr_text)
    print(f"   Found {len(metadata)} metadata items")
    
    print("2. Parsing table data...")
    table_data = ocr_service.parse_table_data(simulated_ocr_text)
    print(f"   Found {len(table_data)} table rows")
    
    print("3. Converting to CSV format...")
    csv_output = ocr_service.convert_to_csv_format(metadata, table_data)
    
    print("4. Final CSV output:")
    print("-" * 50)
    print(csv_output)
    print("-" * 50)
    
    # Save to file for inspection
    output_file = "test_output.csv"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(csv_output)
    print(f"\n✓ Output saved to {output_file}")
    
    return csv_output

def main():
    """Run all tests"""
    print("OCR Service Improvement Tests")
    print("=" * 60)
    
    try:
        # Run individual tests
        test_header_extraction()
        test_table_parsing()
        test_csv_formatting()
        test_end_to_end_simulation()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
