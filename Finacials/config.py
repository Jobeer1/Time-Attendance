"""
Configuration settings for the PDF to Excel/CSV Converter application.
"""
import os
import tempfile

class Config:
    """Application configuration class"""
    
    # Flask settings
    SECRET_KEY = 'your_secret_key_here'
    DEBUG = True
    
    # File paths
    DOWNLOADS_FOLDER = r"E:\Downloads"
    UPLOAD_FOLDER = tempfile.gettempdir()
    OUTPUT_FOLDER = DOWNLOADS_FOLDER  # All outputs go to Downloads
    
    # OCR settings
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    # Balanced OCR config for accurate text extraction
    OCR_CONFIG = r'--oem 3 --psm 3 -c preserve_interword_spaces=1'
    
    # PDF processing settings
    PDF_DPI = 400  # High DPI for better OCR accuracy
    IMAGE_FORMAT = 'PNG'
    IMAGE_QUALITY = 95
    
    # Progress tracking settings
    PROGRESS_UPDATE_DELAY = 0.01  # Small delay to ensure proper updates
    FRONTEND_POLL_INTERVAL = 2000  # Frontend polling interval in ms
    
    # Supported file formats
    SUPPORTED_PDF_FORMATS = ('.pdf',)
    SUPPORTED_IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')
    SUPPORTED_ZIP_FORMATS = ('.zip',)
    
    @classmethod
    def ensure_directories_exist(cls):
        """Ensure required directories exist"""
        os.makedirs(cls.DOWNLOADS_FOLDER, exist_ok=True)
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
