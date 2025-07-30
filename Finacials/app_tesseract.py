import os
import tempfile
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from pdf2image import convert_from_path
import csv

TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if not os.path.exists(TESSERACT_PATH):
    raise FileNotFoundError(f'Tesseract executable not found at {TESSERACT_PATH}. Please install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki and ensure the path is correct.')
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/', methods=['GET'])
def index():
    return render_template('index_tesseract.html')

@app.route('/extract', methods=['POST'])
def extract():
    try:
        file = request.files.get('pdf')
        if not file:
            return jsonify({'error': 'No file uploaded (step: file upload)'}), 400
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
    except Exception as e:
        return jsonify({'error': f'File upload error: {str(e)}'}), 400

    # Optional: page range
    try:
        start_page = int(request.form.get('start_page', 1))
        end_page = int(request.form.get('end_page', 0))
    except Exception as e:
        return jsonify({'error': f'Invalid page numbers (step: page range): {str(e)}'}), 400

    # Determine last page if needed
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
    except Exception as e:
        return jsonify({'error': f'Failed to read PDF for page count (step: page count): {str(e)}'}), 400

    if start_page < 1 or (end_page != 0 and end_page < start_page):
        return jsonify({'error': f'Invalid page range (step: range logic). Start: {start_page}, End: {end_page}, Total: {total_pages}'}), 400
    if end_page == 0 or end_page > total_pages:
        end_page = total_pages

    # Convert only the selected pages
    try:
        images = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)
    except Exception as e:
        return jsonify({'error': f'PDF to image conversion failed (step: convert_from_path): {str(e)}'}), 500

    rows = []
    try:
        for i, image in enumerate(images):
            try:
                text = pytesseract.image_to_string(image)
            except Exception as e:
                return jsonify({'error': f'OCR failed on page {start_page + i} (step: pytesseract): {str(e)}'}), 500
            for line in text.split('\n'):
                if line.strip():
                    row = [col.strip() for col in line.replace(',', ' ').split() if col.strip()]
                    rows.append(row)
    except Exception as e:
        return jsonify({'error': f'Error during OCR or text parsing (step: text extraction): {str(e)}'}), 500

    # Write to CSV
    try:
        csv_fd, csv_path = tempfile.mkstemp(suffix='.csv')
        with os.fdopen(csv_fd, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)
    except Exception as e:
        return jsonify({'error': f'CSV writing failed (step: csv write): {str(e)}'}), 500

    try:
        return send_file(csv_path, as_attachment=True, download_name='output.csv')
    except Exception as e:
        return jsonify({'error': f'File send failed (step: send_file): {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
