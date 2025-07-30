# PDF to Excel/CSV Converter - Modular Architecture

## Overview

This project has been refactored from a monolithic Flask application into a clean, modular architecture with enhanced OCR capabilities specifically optimized for financial document processing.

## 🏗️ Architecture

### Project Structure
```
├── app_new.py                  # Main Flask application
├── config.py                   # Configuration management
├── utils/
│   ├── progress_tracker.py     # Progress tracking for long-running tasks
│   └── file_utils.py          # File handling utilities
├── services/
│   ├── pdf_service.py          # PDF processing (conversion to images)
│   ├── ocr_service.py          # Enhanced OCR with structured data extraction
│   ├── data_service.py         # Data processing and CSV operations
│   └── batch_service.py        # Batch processing coordination
├── routes/
│   ├── pdf_routes.py           # PDF conversion endpoints
│   ├── text_routes.py          # Text processing endpoints
│   ├── batch_routes.py         # Batch processing endpoints
│   └── file_routes.py          # File management endpoints
├── static/
│   ├── css/styles.css          # Enhanced UI styles
│   └── js/progress.js          # Progress tracking frontend
├── templates/
│   ├── index.html              # Original UI
│   └── index_new.html          # Enhanced UI with progress tracking
└── test_ocr_improvements.py    # OCR validation test script
```

## 🚀 Key Features

### Enhanced OCR Service
- **Multiple OCR Configurations**: Automatically tries different Tesseract configurations to find the best result
- **Financial Document Optimization**: Specialized preprocessing for financial reports and tables
- **Structured Data Extraction**: Converts OCR text into properly formatted CSV matching sample structure
- **Quality Evaluation**: Scores OCR results to select the best extraction method

### Modular Services
- **PDF Service**: Handles PDF to image conversion with progress tracking
- **Data Service**: Processes images to CSV with enhanced OCR integration
- **Batch Service**: Coordinates multi-file processing with download packaging
- **Progress Tracker**: Real-time progress updates for long-running operations

### CSV Output Format
The system produces CSV files that exactly match the expected financial report format:

```csv
Report_Header,PROMED REP-SP0050X
Run_Date,25.06.25
Doctor,DR. C.I. STOYANOV
Report_Type,SELECTED MEDICAL AID LISTING
Page_Number,1
Medical_Aid,JUN - QUARTERLY WRITE OFFS

Account_ID,Account_Name,Last_Visit,Last_Receipt_Payment,Current,30_Days,60_Days,90_Days,120_Days,150_Days,Outstanding,Address,Status,Payment_Date,ID_Number,Claim_Number,Claim_Status
10303073,PRIVATE BAG X4216 S,07.03.22,0.00,0.00,0.00,0.00,0.00,10407.90,0.00,10407.90,PRIVATE BAG X4216 S,BAD,0.00.00,9007315300083,,CLM STM
E0272645,ADDONS,04.09.24,-1940.10,0.00,0.00,0.00,1731.40,0.00,0.00,1731.40,26 WONDERBOOM ST,BAD,0.00.00,700220123083,96351327,CLM STM
```

## 📋 API Endpoints

### PDF to CSV Conversion
- **POST** `/pdf_to_csv` - Convert single PDF to structured CSV
- **POST** `/batch_pdf_to_csv` - Convert multiple PDFs to CSV files

### PDF to Images
- **POST** `/pdf_to_images` - Convert single PDF to images
- **POST** `/batch_pdf_to_images` - Convert multiple PDFs to images

### Text Processing
- **POST** `/text_to_csv` - Convert text/images to CSV
- **POST** `/batch_text_to_csv` - Batch text to CSV conversion

### File Management
- **GET** `/progress/<task_id>` - Get processing progress
- **GET** `/download/<filename>` - Download processed files
- **GET** `/list_files` - List available output files

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Tesseract OCR
- Required Python packages (see requirements.txt)

### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract OCR (Windows)
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

# Verify installation
tesseract --version
```

### Configuration
Update `config.py` with your specific paths:
```python
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
```

### Running the Application
```bash
python app_new.py
```

The application will start on `http://localhost:5000`

## 🧪 Testing

### OCR Service Testing
Run the comprehensive test suite:
```bash
python test_ocr_improvements.py
```

This validates:
- Header metadata extraction
- Table data parsing
- CSV formatting
- End-to-end processing simulation

### Expected Test Output
✓ All expected metadata keys found  
✓ Table rows extracted correctly  
✓ CSV format matches sample structure  
✓ Headers match expected format  

## 🎯 OCR Configuration Details

The system uses multiple OCR configurations with automatic fallback:

### Table Mode Configurations
1. **PSM 6** (Uniform text blocks) - Best for structured tables
2. **PSM 4** (Single column) - Good for financial reports  
3. **PSM 1** (Auto with orientation) - Handles rotated documents
4. **PSM 3** (Fully automatic) - Balanced general approach

### Preprocessing Options
- **Enhanced**: Noise reduction, contrast enhancement, morphological operations
- **Simple**: Gaussian blur with adaptive thresholding
- **Minimal**: Basic binary thresholding

### Quality Evaluation
The system scores OCR results based on:
- Presence of expected patterns (PROMED, dates, account IDs)
- Table structure quality
- Currency amount detection
- Noise level assessment

## 🔄 Processing Flow

### Single PDF to CSV
1. Upload PDF file
2. Convert PDF to images (PDF Service)
3. Extract structured data using OCR (OCR Service)
4. Process and clean data (Data Service)
5. Generate CSV output
6. Package for download (Batch Service)

### Batch PDF to CSV
1. Upload multiple PDF files
2. Process each PDF individually
3. Combine results into downloadable package
4. Real-time progress tracking

## 📊 Progress Tracking

All long-running operations provide real-time progress updates:
- Task creation with unique IDs
- Progress percentage (0-100%)
- Status messages
- Error handling and reporting

## 🎨 Frontend Features

### Enhanced UI
- File upload with drag-and-drop
- Real-time progress bars
- Download links for completed tasks
- Responsive design

### Progress Monitoring
- Automatic progress polling
- Visual progress indicators
- Completion notifications
- Error display

## 🔍 Debugging & Troubleshooting

### Common Issues

1. **Tesseract Not Found**
   - Verify installation path in config.py
   - Check PATH environment variable

2. **Poor OCR Results**
   - Run test_ocr_improvements.py to validate
   - Check image quality and preprocessing

3. **Missing Dependencies**
   - Install all requirements: `pip install -r requirements.txt`

### Debug Mode
Enable debug logging by setting `DEBUG = True` in config.py

### Test Files
- `test_ocr_improvements.py` - Comprehensive OCR testing
- Sample CSV files (page1_corrected.csv, etc.) - Expected output format

## 📈 Performance Optimizations

- **Background Processing**: Long operations run in separate threads
- **Progress Tracking**: Non-blocking progress updates
- **Efficient File Handling**: Temporary file cleanup
- **Memory Management**: Image processing optimization

## 🔒 Security Considerations

- Input validation for uploaded files
- Secure file handling with temporary directories
- File type restrictions (PDF, images only)
- Path traversal protection

## 🚀 Future Enhancements

- [ ] Machine learning-based OCR optimization
- [ ] Advanced table detection algorithms
- [ ] Multi-language support
- [ ] Cloud storage integration
- [ ] API authentication
- [ ] Batch job scheduling

## 📝 License

This project is part of a financial document processing system. All rights reserved.

## 🤝 Contributing

This is a specialized financial document processing system. Contributions should focus on:
- OCR accuracy improvements
- Performance optimizations
- Additional file format support
- Enhanced error handling

---

## Quick Start Commands

```bash
# Test the OCR service
python test_ocr_improvements.py

# Start the application
python app_new.py

# Test application import
python -c "from app_new import app; print('Flask app ready!')"
```

The modular architecture is now complete with enhanced OCR capabilities specifically optimized for financial document processing!
