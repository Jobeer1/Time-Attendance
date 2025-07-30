"""
Batch processing service that orchestrates multiple operations.
"""
import os
import zipfile
import logging
from services.pdf_service import PDFService
from services.ocr_service import OCRService
from utils.progress_tracker import progress_tracker
from utils.file_utils import cleanup_files, cleanup_directory, get_output_path
from config import Config

class BatchService:
    """Service for batch processing operations"""
    
    def __init__(self):
        self.pdf_service = PDFService()
        self.ocr_service = OCRService()
    
    def batch_pdf_to_images_with_zip(self, pdf_files, output_name, task_id=None):
        """
        Process multiple PDFs to images and create a ZIP package.
        Returns the path to the created ZIP file.
        """
        try:
            if task_id:
                progress_tracker.update_progress(task_id, 1, "Starting batch PDF conversion...")
            
            # Convert PDFs to images
            results = self.pdf_service.batch_convert_pdfs_to_images(pdf_files, task_id=task_id)
            
            # Create a master zip file with all image folders
            zip_path = get_output_path(f'{output_name}_batch_images.zip')
            
            if task_id:
                progress_tracker.update_progress(task_id, 90, "📦 Creating ZIP package...")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for pdf_name, image_paths in results.items():
                    pdf_base = os.path.splitext(pdf_name)[0]
                    for img_path in image_paths:
                        # Add to ZIP with folder structure
                        arcname = f"{pdf_base}_images/{os.path.basename(img_path)}"
                        zipf.write(img_path, arcname)
            
            # Clean up individual image files and folders
            for pdf_name, image_paths in results.items():
                cleanup_files(image_paths)
                # Remove the folder
                if image_paths:
                    pdf_folder = os.path.dirname(image_paths[0])
                    cleanup_directory(pdf_folder)
            
            if task_id:
                progress_tracker.update_progress(task_id, 100, 
                                               f"Completed! File saved to Downloads: {output_name}_batch_images.zip")
            
            return zip_path
            
        except Exception as e:
            if task_id:
                progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
            raise
    
    def batch_zip_to_text(self, zip_files, output_name, task_id=None):
        """
        Process multiple ZIP files to extract text and create combined output.
        Returns the path to the created text file.
        """
        try:
            if task_id:
                progress_tracker.update_progress(task_id, 1, "Starting batch ZIP processing...")
            
            # Extract text from ZIPs
            results = self.ocr_service.batch_extract_text_from_zips(zip_files, task_id=task_id)
            
            # Combine all text results into one file
            combined_txt_path = get_output_path(f'{output_name}_batch_text.txt')
            
            if task_id:
                progress_tracker.update_progress(task_id, 95, "📝 Creating combined text file...")
            
            with open(combined_txt_path, 'w', encoding='utf-8') as f:
                for zip_name, lines in results.items():
                    f.write(f"\n=== SOURCE: {zip_name} ===\n")
                    for line in lines:
                        f.write(line + '\n')
                    f.write("\n" + "="*50 + "\n")
            
            if task_id:
                progress_tracker.update_progress(task_id, 100, 
                                               f"Completed! File saved to Downloads: {output_name}_batch_text.txt")
            
            return combined_txt_path
            
        except Exception as e:
            if task_id:
                progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
            raise
    
    def batch_images_to_text(self, image_files, output_name, task_id=None):
        """
        Process multiple image files to extract text and create combined output.
        Returns the path to the created text file.
        """
        try:
            if task_id:
                progress_tracker.update_progress(task_id, 1, "Starting batch image processing...")
            
            # Extract text from images
            results = self.ocr_service.batch_extract_text_from_images(image_files, task_id=task_id)
            
            # Combine all text results into one file
            combined_txt_path = get_output_path(f'{output_name}_batch_text.txt')
            
            if task_id:
                progress_tracker.update_progress(task_id, 95, "📝 Creating combined text file...")
            
            with open(combined_txt_path, 'w', encoding='utf-8') as f:
                for img_name, lines in results.items():
                    f.write(f"\n=== SOURCE: {img_name} ===\n")
                    for line in lines:
                        f.write(line + '\n')
                    f.write("\n" + "="*50 + "\n")
            
            if task_id:
                progress_tracker.update_progress(task_id, 100, 
                                               f"Completed! File saved to Downloads: {output_name}_batch_text.txt")
            
            return combined_txt_path
            
        except Exception as e:
            if task_id:
                progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
            raise
    
    def single_pdf_to_images_with_zip(self, pdf_path, output_name, task_id=None):
        """
        Process a single PDF to images and create a ZIP package.
        Returns the path to the created ZIP file.
        """
        try:
            if task_id:
                progress_tracker.update_progress(task_id, 5, "Starting PDF conversion...")
            
            # Convert PDF to images
            image_paths = self.pdf_service.convert_pdf_to_images(pdf_path, task_id=task_id)
            
            # Create a zip file with all images
            zip_path = get_output_path(f'{output_name}_images.zip')
            
            if task_id:
                progress_tracker.update_progress(task_id, 95, "📦 Creating ZIP package...")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for img_path in image_paths:
                    zipf.write(img_path, os.path.basename(img_path))
            
            # Clean up individual image files
            cleanup_files(image_paths)
            
            if task_id:
                progress_tracker.update_progress(task_id, 100, 
                                               f"Completed! File saved to Downloads: {output_name}_images.zip")
            
            return zip_path
            
        except Exception as e:
            if task_id:
                progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
            raise
        
    def create_zip_download(self, file_paths, zip_name):
        """
        Create a ZIP file containing multiple files for download.
        
        Args:
            file_paths (list): List of file paths to include in the ZIP
            zip_name (str): Name for the ZIP file (without extension)
            
        Returns:
            str: Path to the created ZIP file
        """
        try:
            zip_path = get_output_path(f'{zip_name}.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        # Add file to ZIP with just the filename (no directory structure)
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)
                        logging.info(f"Added {file_path} to ZIP as {arcname}")
                    else:
                        logging.warning(f"File not found: {file_path}")
            
            # Clean up original files after adding to ZIP
            cleanup_files(file_paths)
            
            logging.info(f"Created ZIP download: {zip_path}")
            return zip_path
            
        except Exception as e:
            logging.error(f"Error creating ZIP download: {str(e)}")
            raise

    def batch_pdf_to_csv(self, pdf_files, output_name, task_id=None):
        """
        Process multiple PDFs to CSV files and create a ZIP package.
        Returns the path to the created ZIP file.
        """
        try:
            if task_id:
                progress_tracker.update_progress(task_id, 1, "Starting batch PDF to CSV conversion...")
            
            csv_files = []
            total_pdfs = len(pdf_files)
            
            for i, pdf_file in enumerate(pdf_files):
                if task_id:
                    progress = int(10 + (i / total_pdfs) * 80)  # 10-90% for processing
                    progress_tracker.update_progress(task_id, progress, 
                                                   f"Processing PDF {i+1}/{total_pdfs}: {pdf_file.filename}")
                
                # Convert PDF to images first
                image_paths = self.pdf_service.convert_pdf_to_images(pdf_file)
                
                # Process images to CSV using OCR
                csv_lines = []
                for img_path in image_paths:
                    lines = self.ocr_service.extract_text_from_image(img_path)
                    csv_lines.extend(lines)
                
                # Create CSV file
                pdf_name = os.path.splitext(pdf_file.filename)[0]
                csv_path = get_output_path(f'{pdf_name}.csv')
                
                with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                    for line in csv_lines:
                        f.write(line + '\n')
                
                csv_files.append(csv_path)
                
                # Clean up image files
                cleanup_files(image_paths)
            
            if task_id:
                progress_tracker.update_progress(task_id, 90, "📦 Creating ZIP package...")
            
            # Create ZIP with all CSV files
            zip_path = self.create_zip_download(csv_files, f'{output_name}_batch_csv')
            
            if task_id:
                progress_tracker.update_progress(task_id, 100, 
                                               f"Completed! ZIP file saved to Downloads: {output_name}_batch_csv.zip")
            
            return zip_path
            
        except Exception as e:
            if task_id:
                progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
            raise
