"""
Text extraction routes.
"""
import os
import threading
from flask import Blueprint, request, redirect, flash, jsonify, send_file
from services.ocr_service import OCRService
from services.data_service import DataService
from utils.file_utils import get_output_path
from config import Config

text_bp = Blueprint('text', __name__)
ocr_service = OCRService()

@text_bp.route('/extract_text', methods=['POST'])
def extract_text():
    """Extract text from PDF using hybrid method"""
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
    
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(pdf_path)
    txt_path = get_output_path(f'{output_name}_text.txt')
    
    try:
        lines = ocr_service.extract_text_hybrid(pdf_path, output_txt_path=txt_path)
        return send_file(txt_path, as_attachment=True)
    except Exception as e:
        flash(f'Text extraction failed: {e}')
        return redirect(request.url)

@text_bp.route('/extract_text_from_images', methods=['POST'])
def extract_text_from_images():
    """Extract text from ZIP of images"""
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
    
    zip_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(zip_path)
    txt_path = get_output_path(f'{output_name}_text.txt')
    
    try:
        lines = ocr_service.extract_text_from_images_zip(zip_path, output_txt_path=txt_path)
        return send_file(txt_path, as_attachment=True)
    except Exception as e:
        flash(f'Text extraction from images failed: {e}')
        return redirect(request.url)

@text_bp.route('/convert_csv', methods=['POST'])
def convert_csv():
    """Convert text file to CSV (naive conversion)"""
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
    
    txt_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(txt_path)
    csv_path = get_output_path(f'{output_name}_scrambled.csv')
    
    # Naive conversion: each line split by comma, tab, or just as one column
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

@text_bp.route('/clean_csv', methods=['POST'])
def clean_csv():
    """Clean CSV using gold standard logic"""
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
    
    csv_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(csv_path)
    debug_log = get_output_path(f'{output_name}_clean_debug.log')
    
    # Use gold standard cleaning logic
    with open(csv_path, encoding='utf-8') as f:
        lines = [line.strip('\n') for line in f]
    
    df = DataService.extract_accounts(lines, debug_log_path=debug_log)
    cleaned_csv_path = get_output_path(f'{output_name}_cleaned.csv')
    df.to_csv(cleaned_csv_path, index=False)
    
    return send_file(cleaned_csv_path, as_attachment=True)

@text_bp.route('/convert_xls', methods=['POST'])
def convert_xls():
    """Convert CSV to Excel with formatting"""
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
    
    csv_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(csv_path)
    excel_path = get_output_path(f'{output_name}_accounts.xlsx')
    
    DataService.convert_to_excel(csv_path, excel_path)
    
    return send_file(excel_path, as_attachment=True)
