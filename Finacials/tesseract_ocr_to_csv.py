import os
import csv
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Path to the Tesseract executable (do not change if installed in default location)
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if not os.path.exists(TESSERACT_PATH):
    raise FileNotFoundError(f'Tesseract executable not found at {TESSERACT_PATH}. Please install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki and ensure the path is correct.')
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def pdf_to_csv(pdf_path, csv_path):
    # Convert PDF to images
    images = convert_from_path(pdf_path)
    rows = []
    for i, image in enumerate(images):
        # OCR the image
        text = pytesseract.image_to_string(image)
        # Split into lines and try to parse as CSV rows (very basic)
        for line in text.split('\n'):
            if line.strip():
                # Split by whitespace or comma
                row = [col.strip() for col in line.replace(',', ' ').split() if col.strip()]
                rows.append(row)
    # Write to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('Usage: python tesseract_ocr_to_csv.py <input.pdf> <output.csv>')
    else:
        pdf_to_csv(sys.argv[1], sys.argv[2])
        print(f'CSV written to {sys.argv[2]}')
