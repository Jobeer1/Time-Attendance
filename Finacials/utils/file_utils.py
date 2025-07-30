"""
File handling utilities.
"""
import os
import logging
from config import Config

def ensure_safe_filename(filename, existing_files=None):
    """
    Ensure filename is safe and unique.
    
    Args:
        filename: Original filename
        existing_files: Set/dict of existing filenames to avoid duplicates
    
    Returns:
        Safe filename string
    """
    if existing_files is None:
        existing_files = set()
    
    # Extract just the filename for storage (remove folder path)
    safe_filename = os.path.basename(filename)
    
    # If there are duplicate names, add a counter
    if safe_filename in existing_files:
        original_name = safe_filename
        counter = 1
        while safe_filename in existing_files:
            name, ext = os.path.splitext(original_name)
            safe_filename = f"{name}_{counter}{ext}"
            counter += 1
    
    return safe_filename

def save_uploaded_files(files, file_types, upload_dir):
    """
    Save uploaded files and return mapping of safe_filename -> file_path.
    
    Args:
        files: List of uploaded files
        file_types: Tuple of allowed file extensions (e.g., ('.pdf', '.zip'))
        upload_dir: Directory to save files
    
    Returns:
        Dict mapping safe filename to file path
    """
    saved_files = {}
    
    for file in files:
        if file.filename.lower().endswith(file_types):
            safe_filename = ensure_safe_filename(file.filename, saved_files.keys())
            file_path = os.path.join(upload_dir, safe_filename)
            file.save(file_path)
            saved_files[safe_filename] = file_path
            
            logging.info(f"📁 Uploaded: {file.filename} → {safe_filename}")
    
    return saved_files

def cleanup_files(file_paths, ignore_errors=True):
    """
    Clean up temporary files.
    
    Args:
        file_paths: List of file paths to delete
        ignore_errors: Whether to ignore deletion errors
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            if not ignore_errors:
                raise
            logging.warning(f"Failed to cleanup file {file_path}: {e}")

def cleanup_directory(directory_path, ignore_errors=True):
    """
    Clean up a directory.
    
    Args:
        directory_path: Path to directory to remove
        ignore_errors: Whether to ignore deletion errors
    """
    try:
        if os.path.exists(directory_path):
            os.rmdir(directory_path)
    except Exception as e:
        if not ignore_errors:
            raise
        logging.warning(f"Failed to cleanup directory {directory_path}: {e}")

def get_output_path(filename):
    """Get full output path for a filename"""
    return os.path.join(Config.OUTPUT_FOLDER, filename)
