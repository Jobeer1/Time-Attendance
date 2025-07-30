"""
PDF processing routes.
"""
import os
import logging
import threading
from flask import Blueprint, request, redirect, flash, jsonify
from services.batch_service import BatchService
from services.data_service import DataService
from utils.progress_tracker import progress_tracker
from utils.file_utils import save_uploaded_files
from config import Config

pdf_bp = Blueprint('pdf', __name__)
batch_service = BatchService()
data_service = DataService()

@pdf_bp.route('/pdf_to_images', methods=['POST'])
def pdf_to_images():
    """Convert single PDF to images"""
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
    task_id = progress_tracker.create_task()
    
    # Save PDF file
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(pdf_path)
    
    def process_pdf():
        try:
            batch_service.single_pdf_to_images_with_zip(pdf_path, output_name, task_id)
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_pdf)
    thread.start()
    
    # Return task ID for progress tracking
    return jsonify({'task_id': task_id, 'status': 'started'})

@pdf_bp.route('/batch_pdf_to_images', methods=['POST'])
def batch_pdf_to_images():
    """Convert multiple PDFs to images"""
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
    task_id = progress_tracker.create_task()
    
    # Save all PDF files
    pdf_files = save_uploaded_files(files, Config.SUPPORTED_PDF_FORMATS, Config.UPLOAD_FOLDER)
    
    if not pdf_files:
        flash('No valid PDF files found')
        return redirect(request.url)
    
    def process_batch_pdfs():
        try:
            batch_service.batch_pdf_to_images_with_zip(pdf_files, output_name, task_id)
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_pdfs)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@pdf_bp.route('/pdf_to_csv', methods=['POST'])
def pdf_to_csv():
    """Convert single PDF to CSV using enhanced OCR"""
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
    task_id = progress_tracker.create_task()
    
    # Save PDF file
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(pdf_path)
    
    def process_pdf_to_csv():
        try:
            progress_tracker.update_progress(task_id, 5, "Converting PDF to images...")
            
            # Step 1: Convert PDF to images
            image_paths = batch_service.pdf_service.convert_pdf_to_images(pdf_path, task_id=task_id)
            
            progress_tracker.update_progress(task_id, 30, f"Extracting text from {len(image_paths)} pages...")
            
            # Step 2: Extract text from all images
            all_text_lines = []
            
            for page_idx, img_path in enumerate(image_paths, 1):
                progress_tracker.update_progress(task_id, 30 + page_idx * 40 / len(image_paths), 
                                               f"Processing page {page_idx}/{len(image_paths)}...")
                
                # Extract text using OCR
                text, config_used = batch_service.ocr_service.extract_with_best_config(img_path)
                
                # Add page separator and text
                all_text_lines.append(f"\n=== PAGE {page_idx} ===")
                all_text_lines.extend(text.split('\n'))
            
            progress_tracker.update_progress(task_id, 75, "Converting text to structured CSV...")
            
            # Step 3: Convert combined text to structured CSV
            csv_content = batch_service.ocr_service.convert_text_to_csv(all_text_lines)
            
            # Step 4: Save CSV file
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            csv_path = os.path.join(Config.UPLOAD_FOLDER, f"{base_name}_extracted.csv")
            
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            progress_tracker.update_progress(task_id, 85, "Creating downloadable package...")
            
            # Create downloadable zip with CSV file
            zip_path = batch_service.create_zip_download([csv_path], f"{output_name}_csv")
            
            # Clean up image files
            for img_path in image_paths:
                try:
                    os.remove(img_path)
                except:
                    pass
            
            progress_tracker.update_progress(task_id, 100, f"✅ Complete! Download: {os.path.basename(zip_path)}")
            
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"❌ Error: {str(e)}")
            logging.error(f"PDF processing error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_pdf_to_csv)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@pdf_bp.route('/batch_pdf_to_csv', methods=['POST'])
def batch_pdf_to_csv():
    """Convert multiple PDFs to CSV using enhanced OCR"""
    if 'pdf_files' not in request.files:
        flash('No files selected')
        return redirect(request.url)
    
    files = request.files.getlist('pdf_files')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected')
        return redirect(request.url)
    
    output_name = request.form.get('output_name', 'batch_csv_output')
    if not output_name:
        output_name = 'batch_csv_output'
    
    # Generate unique task ID
    task_id = progress_tracker.create_task()
    
    # Save all PDF files
    pdf_files = save_uploaded_files(files, Config.SUPPORTED_PDF_FORMATS, Config.UPLOAD_FOLDER)
    
    if not pdf_files:
        flash('No valid PDF files found')
        return redirect(request.url)
    
    def process_batch_pdfs_to_csv():
        try:
            progress_tracker.update_progress(task_id, 2, f"Starting optimized conversion of {len(pdf_files)} PDFs to CSV...")
            
            all_csv_files = []
            total_pdfs = len(pdf_files)
            
            # Process each PDF using optimized pipeline
            for pdf_idx, (pdf_filename, pdf_path) in enumerate(pdf_files.items(), 1):
                base_progress = 5 + (pdf_idx - 1) * 85 / total_pdfs
                
                progress_tracker.update_progress(task_id, base_progress, 
                                               f"PDF {pdf_idx}/{total_pdfs}: Converting {pdf_filename} to images...")
                
                try:
                    # Step 1: Convert PDF to images
                    image_paths = batch_service.pdf_service.convert_pdf_to_images(pdf_path)
                    
                    progress_tracker.update_progress(task_id, base_progress + 25/total_pdfs, 
                                                   f"PDF {pdf_idx}/{total_pdfs}: Extracting text from {len(image_paths)} pages...")
                    
                    # Step 2: Extract text from all images in this PDF
                    pdf_text_lines = []
                    pdf_base = os.path.splitext(pdf_filename)[0]
                    
                    for page_idx, img_path in enumerate(image_paths, 1):
                        # Extract text using OCR
                        text, config_used = batch_service.ocr_service.extract_with_best_config(img_path)
                        
                        # Add page separator and text
                        pdf_text_lines.append(f"\n=== PAGE {page_idx} ===")
                        pdf_text_lines.extend(text.split('\n'))
                        
                        progress_tracker.update_progress(task_id, base_progress + (25 + page_idx * 30 / len(image_paths))/total_pdfs,
                                                       f"PDF {pdf_idx}/{total_pdfs}: Processed page {page_idx}/{len(image_paths)}")
                    
                    progress_tracker.update_progress(task_id, base_progress + 60/total_pdfs, 
                                                   f"PDF {pdf_idx}/{total_pdfs}: Converting text to structured CSV...")
                    
                    # Step 3: Convert combined text to structured CSV
                    csv_content = batch_service.ocr_service.convert_text_to_csv(pdf_text_lines)
                    
                    # Step 4: Save CSV file
                    csv_filename = f"{pdf_base}_extracted.csv"
                    csv_path = os.path.join(Config.UPLOAD_FOLDER, csv_filename)
                    
                    with open(csv_path, 'w', encoding='utf-8') as f:
                        f.write(csv_content)
                    
                    all_csv_files.append(csv_path)
                    
                    # Clean up image files
                    for img_path in image_paths:
                        try:
                            os.remove(img_path)
                        except:
                            pass
                    
                    progress_tracker.update_progress(task_id, base_progress + 80/total_pdfs, 
                                                   f"✅ Completed PDF {pdf_idx}/{total_pdfs}: {len(pdf_text_lines)} lines extracted")
                    
                except Exception as e:
                    progress_tracker.update_progress(task_id, base_progress + 80/total_pdfs, 
                                                   f"❌ Error processing {pdf_filename}: {str(e)}")
                    logging.error(f"Error processing PDF {pdf_filename}: {str(e)}")
            
            progress_tracker.update_progress(task_id, 90, "📦 Creating download package...")
            
            # Create downloadable zip with all CSV files
            if all_csv_files:
                zip_path = batch_service.create_zip_download(all_csv_files, f"{output_name}_batch_csv")
                
                progress_tracker.update_progress(task_id, 100, 
                                               f"✅ Complete! {len(all_csv_files)} CSV files created. Download: {os.path.basename(zip_path)}")
            else:
                progress_tracker.update_progress(task_id, 0, "❌ No CSV files were created successfully")
            
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"❌ Error: {str(e)}")
            logging.error(f"Batch processing error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_pdfs_to_csv)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@pdf_bp.route('/image_to_csv', methods=['POST'])
def image_to_csv():
    """Convert single image to CSV using enhanced OCR - most efficient method"""
    if 'image_file' not in request.files:
        flash('No image file selected')
        return redirect(request.url)
    
    file = request.files['image_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    # Validate image format
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        flash('Invalid file format. Please upload PNG, JPG, TIFF, or BMP images.')
        return redirect(request.url)
    
    output_name = request.form.get('output_name', 'image_output')
    if not output_name:
        output_name = 'image_output'
    
    # Generate unique task ID
    task_id = progress_tracker.create_task()
    
    # Save image file
    image_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    file.save(image_path)
    
    def process_image_to_csv():
        try:
            progress_tracker.update_progress(task_id, 10, "Analyzing image...")
            
            # Extract text using enhanced OCR
            text, config_used = batch_service.ocr_service.extract_with_best_config(image_path)
            
            progress_tracker.update_progress(task_id, 60, "Converting to structured CSV...")
            
            # Convert text to CSV
            csv_content = batch_service.ocr_service.convert_text_to_csv(text.split('\n'))
            
            # Save CSV file
            base_name = os.path.splitext(file.filename)[0]
            csv_path = os.path.join(Config.UPLOAD_FOLDER, f"{base_name}_extracted.csv")
            
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            progress_tracker.update_progress(task_id, 90, "Creating download package...")
            
            # Create downloadable zip
            zip_path = batch_service.create_zip_download([csv_path], f"{output_name}_csv")
            
            # Clean up original image
            try:
                os.remove(image_path)
            except:
                pass
            
            progress_tracker.update_progress(task_id, 100, f"✅ Complete! Download: {os.path.basename(zip_path)}")
            
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"❌ Error: {str(e)}")
            logging.error(f"Image processing error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_image_to_csv)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})

@pdf_bp.route('/batch_image_to_csv', methods=['POST'])
def batch_image_to_csv():
    """Convert multiple images to CSV - fastest method for pre-scanned documents"""
    if 'image_files' not in request.files:
        flash('No image files selected')
        return redirect(request.url)
    
    files = request.files.getlist('image_files')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected')
        return redirect(request.url)
    
    # Validate image formats
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'}
    valid_files = []
    
    for file in files:
        if any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            valid_files.append(file)
    
    if not valid_files:
        flash('No valid image files found. Please upload PNG, JPG, TIFF, or BMP images.')
        return redirect(request.url)
    
    output_name = request.form.get('output_name', 'batch_images_output')
    if not output_name:
        output_name = 'batch_images_output'
    
    # Generate unique task ID
    task_id = progress_tracker.create_task()
    
    # Save all image files
    saved_files = {}
    for file in valid_files:
        file_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        saved_files[file.filename] = file_path
    
    def process_batch_images_to_csv():
        try:
            progress_tracker.update_progress(task_id, 2, f"Processing {len(saved_files)} images to CSV...")
            
            all_csv_files = []
            total_images = len(saved_files)
            
            # Process each image
            for img_idx, (img_filename, img_path) in enumerate(saved_files.items(), 1):
                base_progress = 5 + (img_idx - 1) * 85 / total_images
                
                progress_tracker.update_progress(task_id, base_progress, 
                                               f"Image {img_idx}/{total_images}: Processing {img_filename}...")
                
                try:
                    # Extract text using enhanced OCR
                    text, config_used = batch_service.ocr_service.extract_with_best_config(img_path)
                    
                    progress_tracker.update_progress(task_id, base_progress + 60/total_images, 
                                                   f"Image {img_idx}/{total_images}: Converting to CSV...")
                    
                    # Convert to CSV
                    csv_content = batch_service.ocr_service.convert_text_to_csv(text.split('\n'))
                    
                    # Save CSV file
                    base_name = os.path.splitext(img_filename)[0]
                    csv_path = os.path.join(Config.UPLOAD_FOLDER, f"{base_name}_extracted.csv")
                    
                    with open(csv_path, 'w', encoding='utf-8') as f:
                        f.write(csv_content)
                    
                    all_csv_files.append(csv_path)
                    
                    # Clean up image file
                    try:
                        os.remove(img_path)
                    except:
                        pass
                    
                    progress_tracker.update_progress(task_id, base_progress + 80/total_images, 
                                                   f"✅ Completed image {img_idx}/{total_images}")
                    
                except Exception as e:
                    progress_tracker.update_progress(task_id, base_progress + 80/total_images, 
                                                   f"❌ Error processing {img_filename}: {str(e)}")
                    logging.error(f"Error processing image {img_filename}: {str(e)}")
            
            progress_tracker.update_progress(task_id, 90, "📦 Creating download package...")
            
            # Create downloadable zip
            if all_csv_files:
                zip_path = batch_service.create_zip_download(all_csv_files, f"{output_name}_batch_csv")
                
                progress_tracker.update_progress(task_id, 100, 
                                               f"✅ Complete! {len(all_csv_files)} CSV files created. Download: {os.path.basename(zip_path)}")
            else:
                progress_tracker.update_progress(task_id, 0, "❌ No CSV files were created successfully")
            
        except Exception as e:
            progress_tracker.update_progress(task_id, 0, f"❌ Error: {str(e)}")
            logging.error(f"Batch image processing error: {str(e)}")
    
    # Start processing in background
    thread = threading.Thread(target=process_batch_images_to_csv)
    thread.start()
    
    return jsonify({'task_id': task_id, 'status': 'started'})
