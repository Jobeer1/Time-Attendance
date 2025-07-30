"""
Data processing service for CSV/Excel operations.
"""
import re
import pandas as pd
import logging
import os
from config import Config
from .ocr_service import OCRService

class DataService:
    """Service for data processing and cleaning operations"""
    
    def __init__(self):
        """Initialize data service with OCR capabilities"""
        self.ocr_service = OCRService()
    
    def process_image_to_csv(self, image_path, output_path=None):
        """
        Process an image using the enhanced OCR service and save as CSV.
        Returns the path to the created CSV file.
        """
        try:
            # Extract structured data using OCR service
            csv_content = self.ocr_service.extract_structured_data(image_path)
            
            # Generate output path if not provided
            if not output_path:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_path = os.path.join(Config.UPLOAD_FOLDER, f"{base_name}_extracted.csv")
            
            # Save CSV content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            logging.info(f"Image processed and CSV saved: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {e}")
            raise
    
    def batch_process_images_to_csv(self, image_paths, output_dir=None):
        """
        Process multiple images and create individual CSV files.
        Returns a dictionary mapping image paths to CSV paths.
        """
        if not output_dir:
            output_dir = Config.UPLOAD_FOLDER
        
        results = {}
        
        for image_path in image_paths:
            try:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                csv_path = os.path.join(output_dir, f"{base_name}_extracted.csv")
                
                # Process image
                csv_path = self.process_image_to_csv(image_path, csv_path)
                results[image_path] = csv_path
                
            except Exception as e:
                logging.error(f"Failed to process {image_path}: {e}")
                results[image_path] = None
        
        return results
    
    @staticmethod
    def fix_account_prefix(acc):
        """
        Strictly corrects the account number prefix according to business rules.
        Only the prefix is changed, the digits are preserved.
        """
        acc = acc.strip().replace(' ', '').replace('O', '0').replace('I', '1')  # OCR fix: O→0, I→1
        # Remove any non-alphanumeric prefix chars
        acc_digits = re.sub(r'^[^0-9A-Z]+', '', acc)
        
        # Business rules
        if re.match(r'^(003|004)\d{6,}$', acc_digits):
            return 'N' + acc_digits
        if re.match(r'^(027|028)\d{6,}$', acc_digits):
            return 'E' + acc_digits
        if re.match(r'^(009|010)\d{6,}$', acc_digits):
            return 'U' + acc_digits
        if re.match(r'^(0001|0002)\d{4,}$', acc_digits):
            return 'I' + acc_digits
        if re.match(r'^(01|02)\d{6,}$', acc_digits):
            return 'MT' + acc_digits
        
        # Already has correct prefix?
        if re.match(r'^[NEUI]0\d{6,}$', acc_digits) or re.match(r'^MT0\d{6,}$', acc_digits):
            return acc_digits
        
        # Fallback: return as is
        return acc_digits
    
    @staticmethod
    def clean_field(val):
        """
        Cleans and standardizes a field value, fixing common OCR errors.
        """
        if not isinstance(val, str):
            return val
        
        v = val.strip()
        v = v.replace('O', '0').replace('I', '1').replace('l', '1')  # OCR: O→0, I/l→1
        v = re.sub(r'[''"""\']', '', v)
        v = re.sub(r'[^\w\s\-.,/]', '', v)
        return v
    
    @staticmethod
    def extract_accounts(lines, debug_log_path=None):
        """
        Robustly extract all account records from OCR lines, handling multi-line, multi-page, and fragmented fields.
        Strictly applies business rules to account numbers and cleans all fields.
        """
        cols = [
            'Account_ID', 'Account_Name', 'Last_Visit', 'Last_Receipt_Payment', 'Current', 
            '30_Days', '60_Days', '90_Days', '120_Days', '150_Days', 'Outstanding', 
            'Address', 'Status', 'Payment_Date', 'ID_Number', 'Claim_Number', 'Claim_Status'
        ]
        
        # Enhanced account ID patterns based on sample data
        account_patterns = [
            r'^[EN]\d{7}$',           # E0272645, N0039352
            r'^\d{8}$',               # 10303073, 40040476
            r'^[A-Z]\d{7}$',          # Generic letter + 7 digits
            r'^\d{7,8}$',             # 7-8 digit numbers
        ]
        
        # Skip patterns for headers/footers
        skip_patterns = [
            r'PROMED|MEDICAL AID|ACCOUNT NAME|LAST VISIT|CURRENT|OUTSTANDING',
            r'PAGE|RUN DATE|DOCTOR|REPORT|SELECTED|QUARTERLY|WRITE',
            r'Account_ID|Account_Name',  # CSV headers
        ]
        
        # Pattern matching
        id_pat = re.compile(r'\b(\d{13})\b')  # 13-digit ID numbers
        date_pat = re.compile(r'\b(\d{2}\.\d{2}\.\d{2})\b')  # DD.MM.YY dates
        amount_pat = re.compile(r'\b-?\d+\.?\d*\b')  # Financial amounts
        claim_pat = re.compile(r'\b([A-Z0-9]{6,})\b')  # Claim numbers
        status_code_pat = re.compile(r'\b(CLM STM|BAD DEBT|BAD|GOOD|PENDING|ACTIVE)\b', re.I)
        
        records = []
        debug_lines = []
        current = None
        
        for idx, line in enumerate(lines):
            l = line.strip()
            if not l or l == '\f':
                continue
            
            debug_lines.append(f"[LINE {idx}] {l}")
            
            # Skip header/footer lines
            skip_line = False
            for skip_pat in skip_patterns:
                if re.search(skip_pat, l, re.IGNORECASE):
                    skip_line = True
                    break
            
            if skip_line:
                debug_lines.append(f"  → Skipped header/footer")
                continue
            
            # Parse the line into parts
            if ',' in l:
                parts = [p.strip() for p in l.split(',')]
            else:
                parts = re.split(r'\s{2,}', l)
                parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) < 2:
                continue
            
            # Check if this starts a new account record
            account_id = parts[0].strip()
            is_new_account = False
            
            for pattern in account_patterns:
                if re.match(pattern, account_id):
                    is_new_account = True
                    break
            
            if is_new_account:
                # Save previous record
                if current:
                    records.append(current)
                
                # Start new record
                current = {c: '' for c in cols}
                current['Account_ID'] = DataService.fix_account_prefix(account_id)
                
                # Map parts to columns if we have enough data
                if len(parts) >= 10:  # Complete row
                    field_mapping = [
                        'Account_ID', 'Account_Name', 'Last_Visit', 'Last_Receipt_Payment',
                        'Current', '30_Days', '60_Days', '90_Days', '120_Days', '150_Days',
                        'Outstanding', 'Address', 'Status', 'Payment_Date', 'ID_Number',
                        'Claim_Number', 'Claim_Status'
                    ]
                    
                    for i, field in enumerate(field_mapping):
                        if i < len(parts):
                            current[field] = DataService.clean_field(parts[i])
                else:
                    # Partial data - map what we can
                    if len(parts) > 1:
                        current['Account_Name'] = DataService.clean_field(parts[1])
                    
                    # Try to identify other fields by pattern
                    for part in parts[2:]:
                        part = part.strip()
                        if not part:
                            continue
                        
                        # Date pattern
                        if re.match(r'\d{2}\.\d{2}\.\d{2}', part) and not current['Last_Visit']:
                            current['Last_Visit'] = DataService.clean_field(part)
                        
                        # Financial amounts (in sequence)
                        elif re.match(r'-?\d+\.?\d*$', part.replace(',', '')):
                            if not current['Last_Receipt_Payment']:
                                current['Last_Receipt_Payment'] = DataService.clean_field(part)
                            elif not current['Current']:
                                current['Current'] = DataService.clean_field(part)
                            elif not current['30_Days']:
                                current['30_Days'] = DataService.clean_field(part)
                            elif not current['60_Days']:
                                current['60_Days'] = DataService.clean_field(part)
                            elif not current['90_Days']:
                                current['90_Days'] = DataService.clean_field(part)
                            elif not current['120_Days']:
                                current['120_Days'] = DataService.clean_field(part)
                            elif not current['150_Days']:
                                current['150_Days'] = DataService.clean_field(part)
                            elif not current['Outstanding']:
                                current['Outstanding'] = DataService.clean_field(part)
                        
                        # 13-digit ID number
                        elif re.match(r'\d{13}', part) and not current['ID_Number']:
                            current['ID_Number'] = DataService.clean_field(part)
                        
                        # Status codes
                        elif re.match(r'CLM STM|BAD DEBT|BAD|GOOD|PENDING|ACTIVE', part, re.IGNORECASE):
                            if part.upper() in ['CLM STM', 'BAD DEBT']:
                                current['Claim_Status'] = DataService.clean_field(part.upper())
                            else:
                                current['Status'] = DataService.clean_field(part.upper())
                        
                        # Claim number
                        elif re.match(r'^[A-Z0-9]{6,}$', part) and not current['Claim_Number']:
                            current['Claim_Number'] = DataService.clean_field(part)
                        
                        # Address (longer text)
                        elif len(part) > 5 and not current['Address'] and not re.match(r'-?\d+\.?\d*$', part.replace(',', '')):
                            current['Address'] = DataService.clean_field(part)
                
                debug_lines.append(f"  → New account: {current['Account_ID']} | {current['Account_Name']}")
                
            elif current:
                # Continue parsing additional data for the current account
                id_match = id_pat.search(l)
                if id_match and not current['ID_Number']:
                    current['ID_Number'] = DataService.clean_field(id_match.group(1))
                    debug_lines.append(f"  → ID: {id_match.group(1)}")
                
                claim_match = claim_pat.search(l)
                if claim_match and not current['Claim_Number']:
                    current['Claim_Number'] = DataService.clean_field(claim_match.group(1))
                    debug_lines.append(f"  → Claim: {claim_match.group(1)}")
                
                status_code_match = status_code_pat.search(l)
                if status_code_match:
                    if status_code_match.group(1).upper() in ['CLM STM', 'BAD DEBT']:
                        current['Claim_Status'] = DataService.clean_field(status_code_match.group(1).upper())
                    else:
                        current['Status'] = DataService.clean_field(status_code_match.group(1).upper())
                    debug_lines.append(f"  → Status: {status_code_match.group(1)}")
                
                # Address continuation (if not already set and no other patterns match)
                if not current['Address'] and not any([id_match, claim_match, status_code_match]):
                    # Only use as address if it's not just numbers
                    if not re.match(r'^[\d\s\.,\-]+$', l):
                        current['Address'] = DataService.clean_field(l)
                        debug_lines.append(f"  → Address: {l}")
        
        # Save last record
        if current:
            records.append(current)
        
        # Write debug log
        if debug_log_path:
            with open(debug_log_path, 'w', encoding='utf-8') as f:
                for line in debug_lines:
                    f.write(line + '\n')
        
        # Create DataFrame with all expected columns
        df = pd.DataFrame(records)
        for c in cols:
            if c not in df.columns:
                df[c] = ''
        
        df = df[cols]
        debug_lines.append(f"\nFinal extracted records: {len(df)}")
        
        return df
    
    @staticmethod
    def convert_to_excel(csv_path, output_path):
        """
        Convert CSV to Excel with formatting.
        """
        df = pd.read_csv(csv_path)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Accounts')
            ws = writer.sheets['Accounts']
            
            # Add auto filter
            ws.auto_filter.ref = ws.dimensions
            
            # Freeze first row
            ws.freeze_panes = ws['A2']
            
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                ws.column_dimensions[col_letter].width = max_length + 2
        
        logging.info(f"Excel file created: {output_path}")
        return output_path
