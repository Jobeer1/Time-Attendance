from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
import os
import tempfile
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import logging
import PyPDF2
import uuid
import threading
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash messages

# Use Downloads folder for easy access to output files
DOWNLOADS_FOLDER = r"E:\Downloads"
UPLOAD_FOLDER = tempfile.gettempdir()  # For temporary uploads
OUTPUT_FOLDER = DOWNLOADS_FOLDER  # All outputs go to Downloads

# Progress tracking
progress_tracker = {}

def update_progress(task_id, progress, message):
    """Update progress for a task"""
    progress_tracker[task_id] = {
        'progress': progress,
        'message': message,
        'timestamp': time.time()
    }
    # Small delay to ensure proper updates
    time.sleep(0.01)

def get_progress(task_id):
    """Get current progress for a task"""
    return progress_tracker.get(task_id, {'progress': 0, 'message': 'Starting...', 'timestamp': time.time()})

# Set up logging
logging.basicConfig(level=logging.INFO)


# Step 1: Convert PDF to Images
def pdf_to_images(pdf_path, output_dir=None, task_id=None):
    """
    Converts PDF pages to high-quality images for OCR processing.
    Returns list of image file paths.
    """
    if not output_dir:
        output_dir = UPLOAD_FOLDER
    
    try:
        if task_id:
            update_progress(task_id, 10, "Loading PDF document...")
        
        # Convert at high DPI for better OCR accuracy
        images = convert_from_path(pdf_path, dpi=400, fmt='PNG')
        total_pages = len(images)
        
        print(f"Converting {total_pages} PDF pages to images...")
        logging.info(f"Converting {total_pages} PDF pages to images...")
        
        if task_id:
            update_progress(task_id, 20, f"Converting {total_pages} pages to images...")
        
        image_paths = []
        for page_num, img in enumerate(images, 1):
            print(f"Converting page {page_num}/{total_pages} to image...")
            logging.info(f"Converting page {page_num}/{total_pages} to image...")
            
            # Save each page as a high-quality PNG
            image_path = os.path.join(output_dir, f'page_{page_num:03d}.png')
            img.save(image_path, 'PNG', quality=95)
            image_paths.append(image_path)
            
            # Update progress
            progress_percent = 20 + (page_num / total_pages) * 60  # 20-80%
            if task_id:
                update_progress(task_id, progress_percent, f"Converting page {page_num}/{total_pages}...")
            
            print(f"Page {page_num} saved as: {os.path.basename(image_path)}")
            logging.info(f"Page {page_num} saved as: {os.path.basename(image_path)}")
        
        if task_id:
            update_progress(task_id, 90, "Creating download package...")
        
        print(f"PDF conversion completed. {len(image_paths)} images created.")
        logging.info(f"PDF conversion completed. {len(image_paths)} images created.")
        return image_paths
        
    except Exception as e:
        if task_id:
            update_progress(task_id, 0, f"Error: {str(e)}")
        print(f"Error converting PDF to images: {e}")
        logging.error(f"Error converting PDF to images: {e}")
        raise

# Step 1.5: Batch Convert Multiple PDFs to Images (Sequential Processing)
def batch_pdf_to_images(pdf_files, output_dir=None, task_id=None):
    """
    Converts multiple PDF files to high-quality images for OCR processing SEQUENTIALLY.
    Processes one PDF at a time to avoid resource overload.
    Returns dict mapping PDF filename to list of image file paths.
    """
    if not output_dir:
        output_dir = UPLOAD_FOLDER
    
    results = {}
    total_pdfs = len(pdf_files)
    
    try:
        if task_id:
            update_progress(task_id, 2, f"Starting sequential conversion of {total_pdfs} PDF files...")
        
        # Process each PDF sequentially (one at a time)
        for pdf_idx, (pdf_filename, pdf_path) in enumerate(pdf_files.items(), 1):
            base_progress = 5 + (pdf_idx - 1) * 85 / total_pdfs
            
            if task_id:
                update_progress(task_id, base_progress, 
                              f"📄 Processing PDF {pdf_idx}/{total_pdfs}: {pdf_filename}")
            
            print(f"📄 Processing PDF {pdf_idx}/{total_pdfs}: {pdf_filename}")
            logging.info(f"📄 Processing PDF {pdf_idx}/{total_pdfs}: {pdf_filename}")
            
            try:
                # Load PDF and get page count
                if task_id:
                    update_progress(task_id, base_progress + 2, 
                                  f"📖 Loading PDF {pdf_idx}: {pdf_filename}...")
                
                images = convert_from_path(pdf_path, dpi=400, fmt='PNG')
                total_pages = len(images)
                pdf_images = []
                
                if task_id:
                    update_progress(task_id, base_progress + 5, 
                                  f"📄 PDF {pdf_idx}: Converting {total_pages} pages...")
                
                # Create subfolder for each PDF
                pdf_folder = os.path.join(output_dir, f"{os.path.splitext(pdf_filename)[0]}_images")
                os.makedirs(pdf_folder, exist_ok=True)
                
                # Convert each page sequentially
                for page_num, img in enumerate(images, 1):
                    # Update progress more frequently for better user feedback
                    page_progress = base_progress + 5 + (page_num / total_pages) * 75
                    if task_id:
                        update_progress(task_id, page_progress, 
                                      f"📄 PDF {pdf_idx}/{total_pdfs} - Page {page_num}/{total_pages}: {os.path.basename(pdf_filename)}")
                    
                    # Add a small progress update before intensive image operations
                    if task_id and page_num > 1:
                        update_progress(task_id, page_progress + 0.5, 
                                      f"� Saving page {page_num}/{total_pages} from {os.path.basename(pdf_filename)}...")
                    
                    image_path = os.path.join(pdf_folder, f'page_{page_num:03d}.png')
                    img.save(image_path, 'PNG', quality=95)
                    pdf_images.append(image_path)
                    
                    print(f"  ✅ Page {page_num}/{total_pages} converted")
                    logging.info(f"  ✅ Page {page_num}/{total_pages} converted for {pdf_filename}")
                
                results[pdf_filename] = pdf_images
                
                completion_progress = base_progress + 80
                if task_id:
                    update_progress(task_id, completion_progress, 
                                  f"✅ Completed PDF {pdf_idx}/{total_pdfs}: {len(pdf_images)} images created")
                
                print(f"✅ Completed PDF {pdf_idx}/{total_pdfs}: {len(pdf_images)} images created")
                logging.info(f"✅ Completed PDF {pdf_idx}/{total_pdfs}: {len(pdf_images)} images created")
                
            except Exception as e:
                error_msg = f"❌ Error processing PDF {pdf_idx} ({pdf_filename}): {str(e)}"
                print(error_msg)
                logging.error(error_msg)
                if task_id:
                    update_progress(task_id, base_progress + 80, error_msg)
                # Continue with next PDF instead of stopping
                results[pdf_filename] = []
        
        if task_id:
            update_progress(task_id, 95, "📦 Creating download package...")
        
        success_count = len([k for k, v in results.items() if v])
        final_msg = f"🎉 Batch conversion completed! {success_count}/{total_pdfs} PDFs processed successfully."
        print(final_msg)
        logging.info(final_msg)
        
        return results
        
    except Exception as e:
        error_msg = f"❌ Critical error in batch PDF conversion: {str(e)}"
        if task_id:
            update_progress(task_id, 0, error_msg)
        print(error_msg)
        logging.error(error_msg)
        raise

# Step 2: Hybrid Text Extraction (Direct + OCR)
def extract_text_hybrid(pdf_path, output_txt_path=None):
    """
    Hybrid approach: Try direct text extraction first, fall back to OCR if needed.
    Returns a list of lines (strings).
    """
    print("Starting hybrid text extraction...")
    logging.info("Starting hybrid text extraction...")
    
    # First, try direct text extraction
    direct_text = try_direct_text_extraction(pdf_path)
    
    if direct_text and len(direct_text) > 100:  # If we got substantial text
        print("Direct text extraction successful - using extracted text")
        logging.info("Direct text extraction successful - using extracted text")
        lines = direct_text.splitlines()
    else:
        print("Direct text extraction failed or insufficient - falling back to OCR")
        logging.info("Direct text extraction failed or insufficient - falling back to OCR")
        lines = extract_text_tesseract(pdf_path)
    
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            for l in lines:
                f.write(l + '\n')
    
    return lines

def try_direct_text_extraction(pdf_path):
    """
    Attempts to extract text directly from PDF without OCR.
    Returns text string if successful, empty string if failed.
    """
    try:
        # Use PyPDF2 for direct text extraction
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text_pages = []
            for page_num, page in enumerate(pdf_reader.pages, 1):
                print(f"Extracting text from page {page_num} (direct method)...")
                text = page.extract_text()
                if text:
                    text_pages.append(f"=== PAGE {page_num} ===")
                    text_pages.append(text)
                    text_pages.append("\f")
            
            if text_pages:
                return '\n'.join(text_pages)
    except Exception as e:
        print(f"Direct text extraction failed: {e}")
        logging.error(f"Direct text extraction failed: {e}")
    
    return ""


# Step 2.5: Extract text from ZIP of images
def extract_text_from_images(zip_path, output_txt_path=None):
    """
    Extracts text from a ZIP file containing page images using Tesseract OCR.
    Returns a list of lines (strings).
    """
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    import zipfile
    import tempfile
    
    lines = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            image_files = sorted([f for f in zipf.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            total_pages = len(image_files)
            
            print(f"Starting OCR extraction for {total_pages} image files...")
            logging.info(f"Starting OCR extraction for {total_pages} image files...")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                for page_num, image_file in enumerate(image_files, 1):
                    print(f"Processing image {page_num}/{total_pages}: {image_file}...")
                    logging.info(f"Processing image {page_num}/{total_pages}: {image_file}...")
                    
                    # Extract image to temp directory
                    image_path = zipf.extract(image_file, temp_dir)
                    
                    # Load image and run OCR
                    img = Image.open(image_path)
                    config = r'--oem 3 --psm 3 -c preserve_interword_spaces=1'
                    
                    try:
                        text = pytesseract.image_to_string(img, lang='eng', config=config)
                        page_lines = text.splitlines()
                        
                        # Add page header for debugging
                        lines.append(f"=== PAGE {page_num} ===")
                        lines.extend(page_lines)
                        lines.append("\f")  # page break marker
                        
                        print(f"Page {page_num} extracted: {len(page_lines)} lines")
                        logging.info(f"Page {page_num} extracted: {len(page_lines)} lines")
                        
                    except Exception as e:
                        print(f"Error processing page {page_num}: {e}")
                        logging.error(f"Error processing page {page_num}: {e}")
                        lines.append(f"=== PAGE {page_num} ERROR ===")
                        lines.append("\f")
    
    except Exception as e:
        print(f"Error processing ZIP file: {e}")
        logging.error(f"Error processing ZIP file: {e}")
        raise
    
    print(f"OCR extraction completed. Total lines: {len(lines)}")
    logging.info(f"OCR extraction completed. Total lines: {len(lines)}")
    
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            for l in lines:
                f.write(l + '\n')
    
    return lines
def extract_text_tesseract(pdf_path, output_txt_path=None):
    """
    Extracts all text from all pages of a PDF using Tesseract OCR optimized for accuracy and completeness.
    Returns a list of lines (strings).
    """
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    # Convert all pages at optimal DPI
    images = convert_from_path(pdf_path, dpi=300, fmt='PNG')
    total_pages = len(images)
    
    print(f"Starting OCR extraction for {total_pages} pages...")
    logging.info(f"Starting OCR extraction for {total_pages} pages...")
    
    lines = []
    
    for page_num, img in enumerate(images, 1):
        print(f"Processing page {page_num}/{total_pages}...")
        logging.info(f"Processing page {page_num}/{total_pages}...")
        
        # Use PSM 3 (automatic) which works best for mixed text/table layouts
        # and preserve word spacing for table structure
        config = r'--oem 3 --psm 3 -c preserve_interword_spaces=1'
        
        try:
            text = pytesseract.image_to_string(img, lang='eng', config=config)
            page_lines = text.splitlines()
            
            # Add page header for debugging
            lines.append(f"=== PAGE {page_num} ===")
            lines.extend(page_lines)
            lines.append("\f")  # page break marker
            
            print(f"Page {page_num} extracted: {len(page_lines)} lines")
            logging.info(f"Page {page_num} extracted: {len(page_lines)} lines")
            
        except Exception as e:
            print(f"Error processing page {page_num}: {e}")
            logging.error(f"Error processing page {page_num}: {e}")
            lines.append(f"=== PAGE {page_num} ERROR ===")
            lines.append("\f")
    
    print(f"OCR extraction completed. Total lines: {len(lines)}")
    logging.info(f"OCR extraction completed. Total lines: {len(lines)}")
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            for l in lines:
                f.write(l + '\n')
    return lines

# Step 2: Post-process extracted text to arrange into required columns
import re

# --- New robust post-processing implementation ---
def fix_account_prefix(acc):
    """
    Strictly corrects the account number prefix according to business rules.
    Only the prefix is changed, the digits are preserved.
    """
    acc = acc.strip().replace(' ', '').replace('O', '0').replace('I', '1')  # OCR fix: O→0, I→1
    # Remove any non-alphanumeric prefix chars
    acc_digits = re.sub(r'^[^0-9A-Z]+', '', acc)
    # Rules
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

def clean_field(val):
    """
    Cleans and standardizes a field value, fixing common OCR errors.
    """
    if not isinstance(val, str):
        return val
    v = val.strip()
    v = v.replace('O', '0').replace('I', '1').replace('l', '1')  # OCR: O→0, I/l→1
    v = re.sub(r'[‘’“”"\']', '', v)
    v = re.sub(r'[^\w\s\-.,/]', '', v)
    return v

def extract_accounts(lines, debug_log_path=None):
    """
    Robustly extract all account records from OCR lines, handling multi-line, multi-page, and fragmented fields.
    Strictly applies business rules to account numbers and cleans all fields.
    """
    import re
    cols = [
        'Account_ID', 'Account_Name', 'Last_Visit', 'Last_Receipt_Payment', 'Current', '30_Days', '60_Days', '90_Days', '120_Days', '150_Days', 'Outstanding', 'Address', 'Status', 'ID_Number', 'Claim', 'Status_Code'
    ]
    acc_id_pat = re.compile(r'^(\d{7,}|[A-Z]\d{7,}|[A-Z]{1,2}\d{5,7}|[A-Z0-9]{6,})')
    id_pat = re.compile(r'ID:?\s*([0-9]{13})\b')
    date_pat = re.compile(r'(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})')
    amount_pat = re.compile(r'-?\d+[.,]\d{2}')
    claim_pat = re.compile(r'Claim:?\s*([A-Z0-9]+)?')
    status_code_pat = re.compile(r'CLM STM|BAD|CLM|STM|BAD DEBT|CLMSTM|CLM\s+STM', re.I)

    records = []
    debug_lines = []
    current = None
    for idx, line in enumerate(lines):
        l = line.strip()
        if not l or l == '\f':
            continue
        debug_lines.append(f"[LINE {idx}] {l}")
        # Skip headers/footers
        if l.upper().startswith(('MEDICAL AID', 'ACCOUNT NAME', 'LAST VISIT', 'LAST RECEIPT', 'PAYMENT', 'CURRENT', '30 DAYS', '60 DAYS', '90 DAYS', '120 DAYS', '150 DAYS', 'OUTS', 'SELECTED MEDICAL', 'PROMED', 'PAGE NO', 'RUN DATE', 'REPORT_HEADER', 'RUN_DATE', 'DOCTOR', 'REPORT_TYPE', 'PAGE_NUMBER')):
            continue
        # Detect new account start
        parts = [p.strip() for p in l.split(',')]
        if acc_id_pat.match(parts[0]) and len(parts) >= 3:
            # Save previous record
            if current:
                records.append(current)
            # Start new record
            current = {c: '' for c in cols}
            # Strictly fix account number prefix
            current['Account_ID'] = fix_account_prefix(parts[0])
            # Clean all fields
            for i, c in enumerate(cols[1:], 1):
                if len(parts) > i:
                    current[c] = clean_field(parts[i])
            debug_lines.append(f"  → New account: {current['Account_ID']} | {current['Account_Name']}")
        elif current:
            # Try to fill missing fields from subsequent lines
            id_match = id_pat.search(l)
            if id_match:
                current['ID_Number'] = clean_field(id_match.group(1))
                debug_lines.append(f"  → ID: {id_match.group(1)}")
            claim_match = claim_pat.search(l)
            if claim_match and claim_match.group(1):
                current['Claim'] = clean_field(claim_match.group(1))
                debug_lines.append(f"  → Claim: {claim_match.group(1)}")
            status_code_match = status_code_pat.search(l)
            if status_code_match:
                current['Status_Code'] = clean_field(status_code_match.group(0))
                debug_lines.append(f"  → Status_Code: {status_code_match.group(0)}")
            # Address (if not already set)
            if not current['Address'] and not any([id_match, claim_match, status_code_match]):
                current['Address'] = clean_field(l)
                debug_lines.append(f"  → Address: {l}")
    # Save last record
    if current:
        records.append(current)
    # Write debug log
    if debug_log_path:
        with open(debug_log_path, 'w', encoding='utf-8') as f:
            for l in debug_lines:
                f.write(l + '\n')
    # Output all records, even if some fields are missing
    df = pd.DataFrame(records)
    for c in cols:
        if c not in df.columns:
            df[c] = ''
    df = df[cols]
    return df

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/progress/<task_id>')
def progress_status(task_id):
    """Get progress status for a task"""
    progress_data = get_progress(task_id)
    return jsonify(progress_data)

# Multi-step debug-friendly workflow
@app.route('/pdf_to_images', methods=['POST'])
def pdf_to_images_route():
    if 'pdf_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['pdf_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    output_name = request.form.get('output_name', 'output')
    if not output_name:
        output_name = 'output'
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(pdf_path)
    
    def process_pdf():
        try:
            update_progress(task_id, 5, "Starting PDF conversion...")
            image_paths = pdf_to_images(pdf_path, task_id=task_id)
            
            # Create a zip file with all images
            import zipfile
            zip_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for img_path in image_paths:
                    zipf.write(img_path, os.path.basename(img_path))
            
            # Clean up individual image files
            for img_path in image_paths:
                try:
                    os.remove(img_path)
                except:
                    pass
            
            update_progress(task_id, 100, f"Completed! File saved to Downloads: {output_name}_images.zip")
            
        except Exception as e:
            update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_pdf)
    thread.start()
    
    # Return task ID for progress tracking
    return jsonify({'task_id': task_id, 'status': 'started'})

@app.route('/batch_pdf_to_images', methods=['POST'])
def batch_pdf_to_images_route():
    if 'pdf_files' not in request.files:
        flash('No files selected')
        return redirect(request.url)
    
    files = request.files.getlist('pdf_files')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected')
        return redirect(request.url)
    
    output_name = request.form.get('output_name', 'batch_output')
    if not output_name:
        output_name = 'batch_output'
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Save all PDF files
    pdf_files = {}
    for file in files:
        if file.filename.lower().endswith('.pdf'):
            # Extract just the filename for storage (remove folder path)
            safe_filename = os.path.basename(file.filename)
            # If there are duplicate names, add a counter
            original_name = safe_filename
            counter = 1
            while safe_filename in pdf_files:
                name, ext = os.path.splitext(original_name)
                safe_filename = f"{name}_{counter}{ext}"
                counter += 1
            
            pdf_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            file.save(pdf_path)
            pdf_files[safe_filename] = pdf_path
            
            print(f"📁 Uploaded: {file.filename} → {safe_filename}")
            logging.info(f"📁 Uploaded: {file.filename} → {safe_filename}")
    
    if not pdf_files:
        flash('No valid PDF files found')
        return redirect(request.url)
    
    def process_batch_pdfs():
        try:
            update_progress(task_id, 1, "Starting batch PDF conversion...")
            results = batch_pdf_to_images(pdf_files, task_id=task_id)
            
            # Create a master zip file with all image folders
            import zipfile
            zip_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_batch_images.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for pdf_name, image_paths in results.items():
                    pdf_base = os.path.splitext(pdf_name)[0]
                    for img_path in image_paths:
                        # Add to ZIP with folder structure
                        arcname = f"{pdf_base}_images/{os.path.basename(img_path)}"
                        zipf.write(img_path, arcname)
            
            # Clean up individual image files and folders
            for pdf_name, image_paths in results.items():
                for img_path in image_paths:
                    try:
                        os.remove(img_path)
                    except:
                        pass
                # Remove the folder
                try:
                    pdf_folder = os.path.dirname(image_paths[0]) if image_paths else None
                    if pdf_folder:
                        os.rmdir(pdf_folder)
                except:
                    pass
            
            update_progress(task_id, 100, f"Completed! File saved to Downloads: {output_name}_batch_images.zip")
            
        except Exception as e:
            update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_pdfs)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@app.route('/extract_text', methods=['POST'])
def extract_text():
    if 'pdf_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['pdf_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    output_name = request.form.get('output_name', 'output')
    if not output_name:
        output_name = 'output'
    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(pdf_path)
    txt_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_text.txt')
    try:
        lines = extract_text_hybrid(pdf_path, output_txt_path=txt_path)
    except Exception as e:
        flash(f'Text extraction failed: {e}')
        return redirect(url_for('index'))
    return send_file(txt_path, as_attachment=True)

@app.route('/extract_text_from_images', methods=['POST'])
def extract_text_from_images_route():
    if 'zip_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['zip_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    output_name = request.form.get('output_name', 'output')
    if not output_name:
        output_name = 'output'
    
    zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(zip_path)
    txt_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_text.txt')
    
    try:
        lines = extract_text_from_images(zip_path, output_txt_path=txt_path)
        return send_file(txt_path, as_attachment=True)
    except Exception as e:
        flash(f'Text extraction from images failed: {e}')
        return redirect(url_for('index'))

@app.route('/convert_csv', methods=['POST'])
def convert_csv():
    if 'txt_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['txt_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    output_name = request.form.get('output_name', 'output')
    if not output_name:
        output_name = 'output'
    txt_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(txt_path)
    csv_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_scrambled.csv')
    # Naive: each line split by comma, tab, or just as one column
    with open(txt_path, encoding='utf-8') as f_in, open(csv_path, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            line = line.strip('\n')
            if ',' in line:
                f_out.write(line + '\n')
            elif '\t' in line:
                f_out.write(line.replace('\t', ',') + '\n')
            else:
                f_out.write(line + '\n')
    return send_file(csv_path, as_attachment=True)

@app.route('/clean_csv', methods=['POST'])
def clean_csv():
    if 'csv_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    output_name = request.form.get('output_name', 'output')
    if not output_name:
        output_name = 'output'
    csv_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(csv_path)
    debug_log = os.path.join(OUTPUT_FOLDER, f'{output_name}_clean_debug.log')
    # Use gold standard cleaning logic
    with open(csv_path, encoding='utf-8') as f:
        lines = [line.strip('\n') for line in f]
    df = extract_accounts(lines, debug_log_path=debug_log)
    cleaned_csv_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_cleaned.csv')
    df.to_csv(cleaned_csv_path, index=False)
    return send_file(cleaned_csv_path, as_attachment=True)

@app.route('/convert_xls', methods=['POST'])
def convert_xls():
    if 'csv_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    output_name = request.form.get('output_name', 'output')
    if not output_name:
        output_name = 'output'
    csv_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(csv_path)
    df = pd.read_csv(csv_path)
    outname = os.path.join(OUTPUT_FOLDER, f'{output_name}_accounts.xlsx')
    with pd.ExcelWriter(outname, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Accounts')
        ws = writer.sheets['Accounts']
        ws.auto_filter.ref = ws.dimensions
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
    return send_file(outname, as_attachment=True)

# Step 2.6: Batch Extract text from multiple ZIP files (Sequential Processing)
def batch_extract_text_from_zips(zip_files, output_dir=None, task_id=None):
    """
    Extracts text from multiple ZIP files containing page images using Tesseract OCR SEQUENTIALLY.
    Processes one ZIP at a time to avoid resource overload.
    Returns dict mapping ZIP filename to extracted text lines.
    """
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    if not output_dir:
        output_dir = UPLOAD_FOLDER
    
    results = {}
    total_zips = len(zip_files)
    
    try:
        if task_id:
            update_progress(task_id, 2, f"Starting sequential OCR of {total_zips} ZIP files...")
        
        # Process each ZIP sequentially (one at a time)
        for zip_idx, (zip_filename, zip_path) in enumerate(zip_files.items(), 1):
            base_progress = 5 + (zip_idx - 1) * 85 / total_zips
            
            if task_id:
                update_progress(task_id, base_progress, 
                              f"📦 Processing ZIP {zip_idx}/{total_zips}: {zip_filename}")
            
            print(f"📦 Processing ZIP {zip_idx}/{total_zips}: {zip_filename}")
            logging.info(f"📦 Processing ZIP {zip_idx}/{total_zips}: {zip_filename}")
            
            try:
                # Extract text from current ZIP with detailed progress
                if task_id:
                    update_progress(task_id, base_progress + 5, 
                                  f"🔍 Analyzing ZIP {zip_idx}: {zip_filename}...")
                
                lines = extract_text_from_images_with_progress(zip_path, zip_idx, total_zips, base_progress, task_id)
                results[zip_filename] = lines
                
                completion_progress = base_progress + 80
                if task_id:
                    update_progress(task_id, completion_progress, 
                                  f"✅ Completed ZIP {zip_idx}/{total_zips}: {len(lines)} lines extracted")
                
                print(f"✅ Completed ZIP {zip_idx}/{total_zips}: {len(lines)} lines extracted")
                logging.info(f"✅ Completed ZIP {zip_idx}/{total_zips}: {len(lines)} lines extracted")
                
            except Exception as e:
                error_msg = f"❌ Error processing ZIP {zip_idx} ({zip_filename}): {str(e)}"
                print(error_msg)
                logging.error(error_msg)
                if task_id:
                    update_progress(task_id, base_progress + 80, error_msg)
                # Continue with next ZIP instead of stopping
                results[zip_filename] = [f"ERROR: {str(e)}"]
        
        if task_id:
            update_progress(task_id, 95, "📝 Finalizing text output...")
        
        success_count = len([k for k, v in results.items() if v and not str(v[0]).startswith("ERROR")])
        final_msg = f"🎉 Batch ZIP processing completed! {success_count}/{total_zips} ZIP files processed successfully."
        print(final_msg)
        logging.info(final_msg)
        
        return results
        
    except Exception as e:
        error_msg = f"❌ Critical error in batch ZIP processing: {str(e)}"
        if task_id:
            update_progress(task_id, 0, error_msg)
        print(error_msg)
        logging.error(error_msg)
        raise

def extract_text_from_images_with_progress(zip_path, zip_idx, total_zips, base_progress, task_id):
    """
    Helper function to extract text from images with detailed progress tracking.
    """
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    import zipfile
    import tempfile
    
    lines = []
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        image_files = sorted([f for f in zipf.namelist() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))])
        total_images = len(image_files)
        
        if task_id:
            update_progress(task_id, base_progress + 10, 
                          f"📦 ZIP {zip_idx}: Found {total_images} images to process...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for img_num, image_file in enumerate(image_files, 1):
                # Update progress more frequently for better user feedback
                img_progress = base_progress + 10 + (img_num / total_images) * 65
                if task_id:
                    update_progress(task_id, img_progress, 
                                  f"📦 ZIP {zip_idx}/{total_zips} - Image {img_num}/{total_images}: {os.path.basename(image_file)}")
                
                print(f"  🖼️ Processing image {img_num}/{total_images}: {image_file}")
                logging.info(f"  🖼️ Processing image {img_num}/{total_images}: {image_file}")
                
                try:
                    # Extract image to temp directory
                    image_path = zipf.extract(image_file, temp_dir)
                    
                    # Load image and run OCR
                    img = Image.open(image_path)
                    config = r'--oem 3 --psm 3 -c preserve_interword_spaces=1'
                    text = pytesseract.image_to_string(img, lang='eng', config=config)
                    page_lines = text.splitlines()
                    
                    # Add image header for debugging
                    lines.append(f"=== IMAGE {img_num}: {image_file} ===")
                    lines.extend(page_lines)
                    lines.append("\f")  # page break marker
                    
                    print(f"    ✅ Image {img_num}: {len(page_lines)} lines extracted")
                    logging.info(f"    ✅ Image {img_num}: {len(page_lines)} lines extracted")
                    
                except Exception as e:
                    error_msg = f"    ❌ Error processing image {img_num}: {str(e)}"
                    print(error_msg)
                    logging.error(error_msg)
                    lines.append(f"=== IMAGE {img_num}: {image_file} ERROR ===")
                    lines.append(str(e))
                    lines.append("\f")
    
    return lines

# Step 2.7: Batch Extract text from multiple image files (Sequential Processing)
def batch_extract_text_from_images(image_files, output_dir=None, task_id=None):
    """
    Extracts text from multiple image files using Tesseract OCR SEQUENTIALLY.
    Processes one image at a time to avoid resource overload.
    Returns dict mapping image filename to extracted text lines.
    """
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    
    if not output_dir:
        output_dir = UPLOAD_FOLDER
    
    results = {}
    total_images = len(image_files)
    
    try:
        if task_id:
            update_progress(task_id, 2, f"Starting sequential OCR of {total_images} image files...")
        
        # Process each image sequentially (one at a time)
        for img_idx, (img_filename, img_path) in enumerate(image_files.items(), 1):
            base_progress = 5 + (img_idx - 1) * 85 / total_images
            
            if task_id:
                update_progress(task_id, base_progress, 
                              f"🖼️ Processing image {img_idx}/{total_images}: {img_filename}")
            
            print(f"🖼️ Processing image {img_idx}/{total_images}: {img_filename}")
            logging.info(f"🖼️ Processing image {img_idx}/{total_images}: {img_filename}")
            
            try:
                # Load and analyze image
                if task_id:
                    update_progress(task_id, base_progress + 10, 
                                  f"📖 Loading image {img_idx}: {img_filename}...")
                
                img = Image.open(img_path)
                
                # Get image info for progress display
                width, height = img.size
                if task_id:
                    update_progress(task_id, base_progress + 20, 
                                  f"🔍 Analyzing image {img_idx}: {width}x{height} pixels...")
                
                # Run OCR with progress updates
                if task_id:
                    update_progress(task_id, base_progress + 30, 
                                  f"🤖 Running OCR on image {img_idx}: {img_filename}...")
                
                config = r'--oem 3 --psm 3 -c preserve_interword_spaces=1'
                text = pytesseract.image_to_string(img, lang='eng', config=config)
                lines = text.splitlines()
                
                # Process results
                if task_id:
                    update_progress(task_id, base_progress + 70, 
                                  f"📝 Processing OCR results for image {img_idx}...")
                
                # Add image header for debugging
                result_lines = [f"=== IMAGE {img_filename} ==="]
                result_lines.extend(lines)
                result_lines.append("\f")
                
                results[img_filename] = result_lines
                
                completion_progress = base_progress + 80
                if task_id:
                    update_progress(task_id, completion_progress, 
                                  f"✅ Completed image {img_idx}/{total_images}: {len(lines)} lines extracted")
                
                print(f"✅ Completed image {img_idx}/{total_images}: {len(lines)} lines extracted")
                logging.info(f"✅ Completed image {img_idx}/{total_images}: {len(lines)} lines extracted")
                
            except Exception as e:
                error_msg = f"❌ Error processing image {img_idx} ({img_filename}): {str(e)}"
                print(error_msg)
                logging.error(error_msg)
                if task_id:
                    update_progress(task_id, base_progress + 80, error_msg)
                # Continue with next image instead of stopping
                results[img_filename] = [f"=== IMAGE {img_filename} ERROR ===", str(e), "\f"]
        
        if task_id:
            update_progress(task_id, 95, "📝 Finalizing text output...")
        
        success_count = len([k for k, v in results.items() if v and not "ERROR" in str(v[0])])
        final_msg = f"🎉 Batch image processing completed! {success_count}/{total_images} images processed successfully."
        print(final_msg)
        logging.info(final_msg)
        
        return results
        
    except Exception as e:
        error_msg = f"❌ Critical error in batch image processing: {str(e)}"
        if task_id:
            update_progress(task_id, 0, error_msg)
        print(error_msg)
        logging.error(error_msg)
        raise

@app.route('/batch_extract_text_from_zips', methods=['POST'])
def batch_extract_text_from_zips_route():
    if 'zip_files' not in request.files:
        flash('No files selected')
        return redirect(request.url)
    
    files = request.files.getlist('zip_files')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected')
        return redirect(request.url)
    
    output_name = request.form.get('output_name', 'batch_output')
    if not output_name:
        output_name = 'batch_output'
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Save all ZIP files
    zip_files = {}
    for file in files:
        if file.filename.lower().endswith('.zip'):
            # Extract just the filename for storage (remove folder path)
            safe_filename = os.path.basename(file.filename)
            # If there are duplicate names, add a counter
            original_name = safe_filename
            counter = 1
            while safe_filename in zip_files:
                name, ext = os.path.splitext(original_name)
                safe_filename = f"{name}_{counter}{ext}"
                counter += 1
            
            zip_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            file.save(zip_path)
            zip_files[safe_filename] = zip_path
            
            print(f"📁 Uploaded ZIP: {file.filename} → {safe_filename}")
            logging.info(f"📁 Uploaded ZIP: {file.filename} → {safe_filename}")
    
    if not zip_files:
        flash('No valid ZIP files found')
        return redirect(request.url)
    
    def process_batch_zips():
        try:
            update_progress(task_id, 1, "Starting batch ZIP processing...")
            results = batch_extract_text_from_zips(zip_files, task_id=task_id)
            
            # Combine all text results into one file
            combined_txt_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_batch_text.txt')
            with open(combined_txt_path, 'w', encoding='utf-8') as f:
                for zip_name, lines in results.items():
                    f.write(f"\n=== SOURCE: {zip_name} ===\n")
                    for line in lines:
                        f.write(line + '\n')
                    f.write("\n" + "="*50 + "\n")
            
            update_progress(task_id, 100, f"Completed! File saved to Downloads: {output_name}_batch_text.txt")
            
        except Exception as e:
            update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_zips)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@app.route('/batch_extract_text_from_images', methods=['POST'])
def batch_extract_text_from_images_route():
    if 'image_files' not in request.files:
        flash('No files selected')
        return redirect(request.url)
    
    files = request.files.getlist('image_files')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected')
        return redirect(request.url)
    
    output_name = request.form.get('output_name', 'batch_output')
    if not output_name:
        output_name = 'batch_output'
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    # Save all image files
    image_files = {}
    supported_formats = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')
    for file in files:
        if file.filename.lower().endswith(supported_formats):
            # Extract just the filename for storage (remove folder path)
            safe_filename = os.path.basename(file.filename)
            # If there are duplicate names, add a counter
            original_name = safe_filename
            counter = 1
            while safe_filename in image_files:
                name, ext = os.path.splitext(original_name)
                safe_filename = f"{name}_{counter}{ext}"
                counter += 1
            
            img_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            file.save(img_path)
            image_files[safe_filename] = img_path
            
            print(f"📁 Uploaded Image: {file.filename} → {safe_filename}")
            logging.info(f"📁 Uploaded Image: {file.filename} → {safe_filename}")
    
    if not image_files:
        flash('No valid image files found')
        return redirect(request.url)
    
    def process_batch_images():
        try:
            update_progress(task_id, 1, "Starting batch image processing...")
            results = batch_extract_text_from_images(image_files, task_id=task_id)
            
            # Combine all text results into one file
            combined_txt_path = os.path.join(OUTPUT_FOLDER, f'{output_name}_batch_text.txt')
            with open(combined_txt_path, 'w', encoding='utf-8') as f:
                for img_name, lines in results.items():
                    f.write(f"\n=== SOURCE: {img_name} ===\n")
                    for line in lines:
                        f.write(line + '\n')
                    f.write("\n" + "="*50 + "\n")
            
            update_progress(task_id, 100, f"Completed! File saved to Downloads: {output_name}_batch_text.txt")
            
        except Exception as e:
            update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_images)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@app.route('/download/<filename>')
def download_file(filename):
    """Download a file from the Downloads folder"""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
