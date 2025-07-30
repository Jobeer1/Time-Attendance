"""
OCR Service optimized for extracting structured tabular data from financial reports.

This service is specifically designed to extract clean, columnar data that can be
easily converted to CSV format matching the style of financial reports.
"""

import cv2
import numpy as np
import pytesseract
import pandas as pd
import re
from PIL import Image, ImageEnhance
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OCRConfig:
    """Configuration for OCR processing"""
    psm: int  # Page Segmentation Mode
    oem: int  # OCR Engine Mode
    preserve_interword_spaces: int
    tessedit_char_whitelist: str = ""
    description: str = ""


class OCRService:
    """Service for extracting structured data from images using OCR"""
    
    def __init__(self):
        # Configure Tesseract path for Windows
        import os
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # OCR configurations optimized for different types of tabular data
        # Reduced to fastest and most effective configs based on test results
        self.table_configs = [
            # PSM 3: Fully automatic page segmentation (best performer - Score: 90.0)
            OCRConfig(
                psm=3,
                oem=3,
                preserve_interword_spaces=1,
                description="Fully automatic segmentation"
            ),
            # PSM 6: Uniform block of text (fallback for structured tables)
            OCRConfig(
                psm=6,
                oem=3,
                preserve_interword_spaces=1,
                tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,- /():",
                description="Table mode - uniform text blocks"
            )
        ]
        
        # Header patterns for financial reports
        self.header_patterns = {
            'report_header': r'PROMED\s+REP-\w+',
            'run_date': r'\d{2}\.\d{2}\.\d{2}',
            'doctor': r'DR\.\s+[A-Z\.\s]+',
            'report_type': r'SELECTED\s+MEDICAL\s+AID\s+LISTING',
            'page_number': r'Page\s+\d+',
            'medical_aid': r'[A-Z]+\s+-\s+[A-Z\s]+'
        }
        
        # Column headers that match the expected CSV format exactly
        self.expected_columns = [
            'Account_ID', 'Account_Name', 'Last_Visit', 'Last_Receipt_Payment',
            'Current', '30_Days', '60_Days', '90_Days', '120_Days', '150_Days',
            'Outstanding', 'Address', 'Status', 'Payment_Date', 'ID_Number',
            'Claim_Number', 'Claim_Status'
        ]

    def preprocess_image(self, image_path: str, config_type: str = "enhanced") -> np.ndarray:
        """
        Preprocess image for better OCR results on financial documents
        """
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        if config_type == "enhanced":
            # Enhanced preprocessing for financial documents
            
            # 1. Noise reduction
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # 2. Contrast enhancement using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # 3. Morphological operations to clean up text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # 4. Adaptive thresholding for better text separation
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
        elif config_type == "simple":
            # Simple preprocessing
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (1, 1), 0)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
        else:  # minimal
            # Minimal preprocessing
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        
        return binary

    def extract_text_with_config(self, image: np.ndarray, config: OCRConfig) -> str:
        """
        Extract text using specific OCR configuration
        """
        # Build tesseract config string
        tesseract_config = f'--oem {config.oem} --psm {config.psm}'
        
        if config.preserve_interword_spaces:
            tesseract_config += f' -c preserve_interword_spaces={config.preserve_interword_spaces}'
        
        if config.tessedit_char_whitelist:
            tesseract_config += f' -c tessedit_char_whitelist={config.tessedit_char_whitelist}'
        
        # Additional config for better table extraction
        tesseract_config += ' -c tessedit_create_hocr=0'
        tesseract_config += ' -c tessedit_create_tsv=0'
        
        try:
            # Extract text
            text = pytesseract.image_to_string(image, config=tesseract_config)
            return text.strip()
        except Exception as e:
            print(f"OCR failed with config {config.description}: {str(e)}")
            return ""

    def evaluate_extraction_quality(self, text: str) -> float:
        """
        Evaluate the quality of extracted text for financial reports
        """
        if not text:
            return 0.0
        
        score = 0.0
        
        # Check for expected patterns
        if re.search(r'PROMED', text, re.IGNORECASE):
            score += 20
        
        # Check for date patterns
        if re.search(r'\d{2}\.\d{2}\.\d{2}', text):
            score += 15
        
        # Check for account ID patterns
        if re.search(r'[EN]\d{7}', text):
            score += 15
        
        # Check for currency amounts
        if re.search(r'\d+\.\d{2}', text):
            score += 10
        
        # Check for table structure (multiple columns)
        lines = text.split('\n')
        tabular_lines = 0
        for line in lines:
            # Count lines that look like table rows (multiple space-separated values)
            parts = line.split()
            if len(parts) >= 5:  # Minimum columns for a table row
                tabular_lines += 1
        
        if tabular_lines > 5:
            score += 20
        elif tabular_lines > 2:
            score += 10
        
        # Penalize for too much noise (random characters)
        noise_chars = len(re.findall(r'[^\w\s.,\-/():.]', text))
        if noise_chars > len(text) * 0.1:  # More than 10% noise
            score -= 20
        
        # Check for proper line structure
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        if 20 <= avg_line_length <= 200:  # Reasonable line length
            score += 10
        
        return max(0.0, min(100.0, score))

    def extract_with_best_config(self, image_path: str) -> Tuple[str, str]:
        """
        Try multiple OCR configurations and return the best result
        """
        best_text = ""
        best_score = 0.0
        best_config_desc = ""
        
        # Try only the most effective preprocessing method first
        preprocessing_methods = ["enhanced"]  # Start with best method
        
        for preprocess_method in preprocessing_methods:
            try:
                # Preprocess image
                processed_image = self.preprocess_image(image_path, preprocess_method)
                
                # Try each OCR configuration
                for config in self.table_configs:
                    text = self.extract_text_with_config(processed_image, config)
                    score = self.evaluate_extraction_quality(text)
                    
                    config_desc = f"{preprocess_method} + {config.description}"
                    print(f"Config '{config_desc}': Score = {score:.1f}")
                    
                    if score > best_score:
                        best_score = score
                        best_text = text
                        best_config_desc = config_desc
                        
            except Exception as e:
                print(f"Error with preprocessing {preprocess_method}: {str(e)}")
                continue
        
        # If enhanced preprocessing didn't work well, try simple as fallback
        if best_score < 50.0:
            for preprocess_method in ["simple"]:
                try:
                    processed_image = self.preprocess_image(image_path, preprocess_method)
                    
                    for config in self.table_configs:
                        text = self.extract_text_with_config(processed_image, config)
                        score = self.evaluate_extraction_quality(text)
                        
                        config_desc = f"{preprocess_method} + {config.description}"
                        print(f"Fallback Config '{config_desc}': Score = {score:.1f}")
                        
                        if score > best_score:
                            best_score = score
                            best_text = text
                            best_config_desc = config_desc
                            
                except Exception as e:
                    print(f"Error with fallback preprocessing {preprocess_method}: {str(e)}")
                    continue
        
        print(f"Best configuration: {best_config_desc} (Score: {best_score:.1f})")
        return best_text, best_config_desc

    def extract_header_metadata(self, text: str) -> Dict[str, str]:
        """
        Extract header metadata from the OCR text to match expected CSV format
        """
        metadata = {}
        lines = text.split('\n')
        
        # Look for header information in the first 20 lines
        for line in lines[:20]:
            line = line.strip()
            if not line:
                continue
            
            # Extract PROMED report header
            if 'PROMED' in line.upper() and 'REP' in line.upper():
                # Try to extract the exact report code
                match = re.search(r'PROMED\s+REP[-\s]*([A-Z0-9]+)', line, re.IGNORECASE)
                if match:
                    metadata['Report_Header'] = f"PROMED REP-{match.group(1)}"
                else:
                    metadata['Report_Header'] = "PROMED REP-SP0050X"  # Default
            
            # Extract run date (format: DD.MM.YY)
            date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2})', line)
            if date_match and 'Run_Date' not in metadata:
                metadata['Run_Date'] = date_match.group()
            
            # Extract doctor name
            if line.upper().startswith('DR.') or 'DR.' in line.upper():
                doctor_match = re.search(r'DR\.\s*([A-Z\.\s]+)', line.upper())
                if doctor_match:
                    metadata['Doctor'] = f"DR. {doctor_match.group(1).strip()}"
            
            # Extract page number
            page_match = re.search(r'PAGE\s+(\d+)', line, re.IGNORECASE)
            if page_match:
                metadata['Page_Number'] = page_match.group(1)
            
            # Extract medical aid info (typically contains "WRITE OFF" or similar)
            if ('WRITE' in line.upper() and 'OFF' in line.upper()) or \
               ('QUARTERLY' in line.upper()) or \
               (re.search(r'[A-Z]{3}\s*-\s*[A-Z\s]+', line)):
                # Clean up the medical aid line
                medical_aid = re.sub(r'^\s*[-\s]*', '', line)
                medical_aid = re.sub(r'\s+', ' ', medical_aid)
                if medical_aid and len(medical_aid) > 5:
                    metadata['Medical_Aid'] = medical_aid.upper()
        
        # Set default report type
        metadata['Report_Type'] = 'SELECTED MEDICAL AID LISTING'
        
        return metadata

    def parse_table_data(self, text: str) -> List[Dict[str, str]]:
        """
        Parse the main table data from OCR text, extracting account records.
        Uses robust pattern matching to identify and extract complete account rows.
        """
        lines = text.split('\n')
        table_data = []
        
        print(f"DEBUG: Parsing {len(lines)} lines of text")
        
        # Enhanced account ID patterns based on sample data
        account_patterns = [
            r'^[A-Z0-9]{6,12}$',         # 6-12 alphanum, flexible
            r'^[A-Z]{0,3}\d{6,10}$',    # Optional prefix, 6-10 digits
            r'^[A-Z]{0,3}\d{6,10}[A-Z]{0,3}$', # Prefix/suffix
            r'^\d{7,8}$',               # 7-8 digit numbers
        ]
        # Fuzzy fallback: allow O/0, I/1 confusion, strip leading/trailing non-alphanum
        def normalize_account_id(s):
            s = s.strip().upper()
            s = re.sub(r'[^A-Z0-9]', '', s)  # Remove all non-alphanum chars
            s = s.replace('O', '0').replace('I', '1').replace('L', '1')
            return s
        def fuzzy_account_id(s):
            s_norm = normalize_account_id(s)
            for pat in account_patterns:
                if re.match(pat, s_norm):
                    return True
            return False
        
        # Skip patterns for obvious header/footer content
        skip_patterns = [
            r'PROMED|MEDICAL AID|ACCOUNT NAME|LAST VISIT|CURRENT|OUTSTANDING',
            r'PAGE|RUN DATE|DOCTOR|REPORT|SELECTED|QUARTERLY|WRITE',
            r'Account_ID|Account_Name',  # CSV headers
        ]
        
        # Financial amount pattern (handles negative values and decimals)
        amount_pattern = r'^-?\d+\.?\d*$'
        
        # Date pattern (DD.MM.YY format)
        date_pattern = r'^\d{2}\.\d{2}\.\d{2}$'
        
        # ID number pattern (13 digits)
        id_pattern = r'^\d{13}$'
        
        # Status pattern
        status_pattern = r'^(BAD|GOOD|PENDING|ACTIVE|CLM STM|BAD DEBT)$'
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line == '\f':
                continue
            
            # Debug: Show lines for analysis
            if i < 30:
                print(f"DEBUG Line {i}: '{line}'")
            
            # Skip header/footer lines
            skip_line = False
            for skip_pat in skip_patterns:
                if re.search(skip_pat, line, re.IGNORECASE):
                    skip_line = True
                    break
            
            if skip_line:
                print(f"DEBUG: Skipping header/footer line: {line}")
                continue
            
            # Parse comma-separated or space-separated data
            if ',' in line:
                parts = [part.strip() for part in line.split(',')]
            else:
                # Split on multiple spaces (2+ spaces)
                parts = re.split(r'\s{2,}', line)
                parts = [part.strip() for part in parts if part.strip()]
            
            # Must have at least account ID and name
            if len(parts) < 2:
                continue
            
            # Normalize and check account ID
            account_id_raw = parts[0].strip()
            account_id = normalize_account_id(account_id_raw)
            is_account_line = False
            # Try all patterns
            for pattern in account_patterns:
                if re.match(pattern, account_id):
                    is_account_line = True
                    print(f"DEBUG: Found account ID match: '{account_id}' with pattern '{pattern}' (raw: '{account_id_raw}')")
                    break
            # Fuzzy fallback
            if not is_account_line and fuzzy_account_id(account_id_raw):
                is_account_line = True
                print(f"DEBUG: Fuzzy account ID match: '{account_id_raw}' (normalized: '{account_id}')")
            # Extra fallback: if the line contains a 7+ digit number anywhere, treat as account row
            if not is_account_line:
                match = re.search(r'\d{7,}', line)
                if match:
                    is_account_line = True
                    print(f"DEBUG: Fallback: found 7+ digit number '{match.group()}' in line, treating as account row: '{line}'")
            # Extra fallback: if first part is mostly digits and line has enough columns
            if not is_account_line and len(parts) >= 4 and sum(c.isdigit() for c in account_id) >= 5:
                is_account_line = True
                print(f"DEBUG: Fallback: first part mostly digits, treating as account row: '{account_id_raw}' (normalized: '{account_id}')")
            if not is_account_line:
                print(f"DEBUG: No account ID pattern match for: '{account_id_raw}' (normalized: '{account_id}')")
                continue
            # Use normalized account_id in output
            account_id = account_id
            
            # Create structured row data
            row_data = {
                'Account_ID': account_id,
                'Account_Name': parts[1].strip() if len(parts) > 1 else '',
                'Last_Visit': '',
                'Last_Receipt_Payment': '',
                'Current': '',
                '30_Days': '',
                '60_Days': '',
                '90_Days': '',
                '120_Days': '',
                '150_Days': '',
                'Outstanding': '',
                'Address': '',
                'Status': '',
                'Payment_Date': '',
                'ID_Number': '',
                'Claim_Number': '',
                'Claim_Status': ''
            }
            
            # If we have many parts, try to map them directly to expected columns
            if len(parts) >= 10:  # Likely a complete row
                field_mapping = [
                    'Account_ID', 'Account_Name', 'Last_Visit', 'Last_Receipt_Payment',
                    'Current', '30_Days', '60_Days', '90_Days', '120_Days', '150_Days',
                    'Outstanding', 'Address', 'Status', 'Payment_Date', 'ID_Number',
                    'Claim_Number', 'Claim_Status'
                ]
                
                for idx, field in enumerate(field_mapping):
                    if idx < len(parts):
                        row_data[field] = parts[idx].strip()
                
                print(f"DEBUG: Mapped complete row with {len(parts)} fields")
                
            else:
                # Parse individual fields by pattern recognition
                for idx, part in enumerate(parts[2:], 2):  # Skip Account_ID and Account_Name
                    part = part.strip()
                    if not part:
                        continue
                    
                    # Date field (Last_Visit)
                    if re.match(date_pattern, part) and not row_data['Last_Visit']:
                        row_data['Last_Visit'] = part
                        print(f"DEBUG: Found date field: {part}")
                    
                    # Financial amounts (in sequence: Last_Receipt_Payment, Current, 30_Days, etc.)
                    elif re.match(amount_pattern, part.replace(',', '')):
                        if not row_data['Last_Receipt_Payment']:
                            row_data['Last_Receipt_Payment'] = part
                        elif not row_data['Current']:
                            row_data['Current'] = part
                        elif not row_data['30_Days']:
                            row_data['30_Days'] = part
                        elif not row_data['60_Days']:
                            row_data['60_Days'] = part
                        elif not row_data['90_Days']:
                            row_data['90_Days'] = part
                        elif not row_data['120_Days']:
                            row_data['120_Days'] = part
                        elif not row_data['150_Days']:
                            row_data['150_Days'] = part
                        elif not row_data['Outstanding']:
                            row_data['Outstanding'] = part
                        print(f"DEBUG: Found amount field: {part}")
                    
                    # ID Number (13 digits)
                    elif re.match(id_pattern, part) and not row_data['ID_Number']:
                        row_data['ID_Number'] = part
                        print(f"DEBUG: Found ID number: {part}")
                    
                    # Status
                    elif re.match(status_pattern, part, re.IGNORECASE):
                        if part.upper() in ['CLM STM', 'BAD DEBT']:
                            row_data['Claim_Status'] = part.upper()
                        else:
                            row_data['Status'] = part.upper()
                        print(f"DEBUG: Found status: {part}")
                    
                    # Claim number (alphanumeric, 6+ chars)
                    elif re.match(r'^[A-Z0-9]{6,}$', part) and not row_data['Claim_Number']:
                        row_data['Claim_Number'] = part
                        print(f"DEBUG: Found claim number: {part}")
                    
                    # Address (longer text that doesn't match other patterns)
                    elif len(part) > 5 and not re.match(amount_pattern, part.replace(',', '')) and not row_data['Address']:
                        row_data['Address'] = part
                        print(f"DEBUG: Found address: {part}")
            
            # Add the record
            table_data.append(row_data)
            print(f"DEBUG: Added account record: ID={row_data['Account_ID']}, Name={row_data['Account_Name']}")
        
        print(f"DEBUG: Total account records extracted: {len(table_data)}")
        return table_data

    def convert_to_csv_format(self, metadata: Dict[str, str], table_data: List[Dict[str, str]]) -> str:
        """
        Convert extracted data to CSV format matching the exact target structure.
        Format matches the sample CSV files exactly.
        """
        csv_lines = []
        
        # Add metadata in the exact order expected
        metadata_keys = [
            ('Report_Header', 'PROMED REP-SP0050X'),
            ('Run_Date', ''),
            ('Doctor', ''),
            ('Report_Type', 'SELECTED MEDICAL AID LISTING'),
            ('Page_Number', ''),
            ('Medical_Aid', '')
        ]
        
        for key, default_value in metadata_keys:
            value = metadata.get(key, default_value)
            csv_lines.append(f"{key},{value}")
        
        # Add empty line to separate metadata from data
        csv_lines.append("")
        
        # Add column headers exactly as expected
        headers = ",".join(self.expected_columns)
        csv_lines.append(headers)
        
        # Add table data rows
        for row in table_data:
            csv_row = []
            for col in self.expected_columns:
                value = row.get(col, "")
                # Clean up the value
                if value:
                    value = str(value).strip()
                    # Fix common OCR errors
                    value = value.replace('O', '0').replace('I', '1') if col == 'Account_ID' else value
                csv_row.append(value)
            csv_lines.append(",".join(csv_row))
        
        return "\n".join(csv_lines)

    def extract_structured_data(self, image_path: str) -> str:
        """
        Main method to extract structured data from an image and return as CSV
        """
        print(f"Processing image: {image_path}")
        
        # Extract text with best configuration
        text, config_used = self.extract_with_best_config(image_path)
        # Log raw OCR text for debugging
        self.log_raw_ocr_text(text, image_path)
    def log_raw_ocr_text(self, text, image_path):
        # Save raw OCR text for debugging
        debug_dir = 'ocr_debug_logs'
        import os
        os.makedirs(debug_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(image_path))[0]
        debug_path = os.path.join(debug_dir, f'{base}_raw_ocr.txt')
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[DEBUG] Raw OCR text saved to {debug_path}")
        
        if not text:
            return "Error: No text could be extracted from the image"
        
        print(f"Extracted text length: {len(text)} characters")
        try:
            print(f"Using configuration: {config_used}")
        except Exception:
            pass
        
        # Extract header metadata
        metadata = self.extract_header_metadata(text)
        print(f"Extracted metadata: {metadata}")
        
        # Parse table data
        table_data = self.parse_table_data(text)
        print(f"Extracted {len(table_data)} table rows")
        
        # Convert to CSV format
        csv_output = self.convert_to_csv_format(metadata, table_data)
        
        return csv_output

    def extract_raw_text(self, image_path: str) -> str:
        """
        Extract raw text for debugging purposes
        """
        text, _ = self.extract_with_best_config(image_path)
        return text

    def batch_extract_text_from_images(self, image_files, task_id=None):
        """
        Extract text from multiple image files.
        Returns a dictionary mapping image filenames to extracted text lines.
        """
        from utils.progress_tracker import progress_tracker
        
        results = {}
        total_files = len(image_files)
        
        for i, (filename, filepath) in enumerate(image_files.items(), 1):
            try:
                if task_id:
                    progress = 10 + (i / total_files) * 80  # Progress from 10% to 90%
                    progress_tracker.update_progress(
                        task_id, progress, f"Processing image {i}/{total_files}: {filename}"
                    )
                
                # Extract raw text from image
                text = self.extract_raw_text(filepath)
                
                # Split into lines and clean
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                results[filename] = lines
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                results[filename] = [f"Error: {str(e)}"]
        
        return results

    def extract_text_hybrid(self, pdf_path, output_txt_path=None):
        """
        Extract text from PDF using a hybrid approach (direct text + OCR fallback).
        This method is for compatibility with the existing text routes.
        """
        try:
            # First try direct text extraction from PDF
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text_lines = []
                
                for page in reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_lines.extend(text.split('\n'))
                
                # If we got meaningful text, use it
                if len(text_lines) > 5:  # Arbitrary threshold
                    if output_txt_path:
                        with open(output_txt_path, 'w', encoding='utf-8') as f:
                            for line in text_lines:
                                f.write(line + '\n')
                    return text_lines
        
        except Exception as e:
            print(f"Direct text extraction failed: {e}")
        
        # Fallback to OCR approach
        try:
            # Convert PDF to images first
            from services.pdf_service import PDFService
            pdf_service = PDFService()
            image_paths = pdf_service.convert_pdf_to_images(pdf_path)
            
            # Extract text from images using OCR
            all_lines = []
            for image_path in image_paths:
                text = self.extract_raw_text(image_path)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                all_lines.extend(lines)
            
            if output_txt_path:
                with open(output_txt_path, 'w', encoding='utf-8') as f:
                    for line in all_lines:
                        f.write(line + '\n')
            
            return all_lines
            
        except Exception as e:
            print(f"OCR fallback failed: {e}")
            return [f"Error: Unable to extract text - {str(e)}"]

    def extract_text_from_images_zip(self, zip_path, output_txt_path=None):
        """
        Extract text from images in a ZIP file.
        This method is for compatibility with the existing text routes.
        """
        import zipfile
        import tempfile
        import os
        
        all_lines = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract to temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # Process each image file
                    for filename in os.listdir(temp_dir):
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                            image_path = os.path.join(temp_dir, filename)
                            try:
                                text = self.extract_raw_text(image_path)
                                lines = [line.strip() for line in text.split('\n') if line.strip()]
                                all_lines.append(f"=== {filename} ===")
                                all_lines.extend(lines)
                                all_lines.append("=" * 50)
                            except Exception as e:
                                all_lines.append(f"Error processing {filename}: {e}")
            
            if output_txt_path:
                with open(output_txt_path, 'w', encoding='utf-8') as f:
                    for line in all_lines:
                        f.write(line + '\n')
            
            return all_lines
            
        except Exception as e:
            error_msg = f"Error extracting from ZIP: {str(e)}"
            if output_txt_path:
                with open(output_txt_path, 'w', encoding='utf-8') as f:
                    f.write(error_msg)
            return [error_msg]
    
    def convert_text_to_csv(self, text_lines: List[str]) -> str:
        """
        Convert extracted text lines to CSV format.
        This method processes multi-page text and creates a unified CSV.
        """
        # Combine all lines into a single text
        combined_text = "\n".join(text_lines)
        
        # Extract header metadata from the first page
        metadata = self.extract_header_metadata(combined_text)
        
        # Parse table data from all pages
        table_data = self.parse_table_data(combined_text)
        
        print(f"Extracted {len(table_data)} table rows from {len(text_lines)} text lines")
        
        # Convert to CSV format
        return self.convert_to_csv_format(metadata, table_data)
