"""
Batch processing routes.
"""
import threading
from flask import Blueprint, request, redirect, flash, jsonify
from services.batch_service import BatchService
from utils.progress_tracker import progress_tracker
from utils.file_utils import save_uploaded_files
from config import Config

batch_bp = Blueprint('batch', __name__)
batch_service = BatchService()

@batch_bp.route('/batch_extract_text_from_zips', methods=['POST'])
def batch_extract_text_from_zips():
    """Extract text from multiple ZIP files"""
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
    task_id = progress_tracker.create_task()
    
    # Save all ZIP files
    zip_files = save_uploaded_files(files, Config.SUPPORTED_ZIP_FORMATS, Config.UPLOAD_FOLDER)
    
    if not zip_files:
        flash('No valid ZIP files found')
        return redirect(request.url)
    
    def process_batch_zips():
        try:
            batch_service.batch_zip_to_text(zip_files, output_name, task_id)
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_zips)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@batch_bp.route('/batch_extract_text_from_images', methods=['POST'])
def batch_extract_text_from_images():
    """Extract text from multiple image files"""
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
    task_id = progress_tracker.create_task()
    
    # Save all image files
    image_files = save_uploaded_files(files, Config.SUPPORTED_IMAGE_FORMATS, Config.UPLOAD_FOLDER)
    
    if not image_files:
        flash('No valid image files found')
        return redirect(request.url)
    
    def process_batch_images():
        try:
            batch_service.batch_images_to_text(image_files, output_name, task_id)
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_images)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})
