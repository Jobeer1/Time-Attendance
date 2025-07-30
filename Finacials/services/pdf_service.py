"""
PDF processing service.
"""
import os
import logging
from pdf2image import convert_from_path
from config import Config
from utils.progress_tracker import progress_tracker

class PDFService:
    """Service for PDF processing operations"""
    
    @staticmethod
    def convert_pdf_to_images(pdf_path, output_dir=None, task_id=None):
        """
        Converts PDF pages to high-quality images for OCR processing.
        Returns list of image file paths.
        """
        if not output_dir:
            output_dir = Config.UPLOAD_FOLDER
        
        try:
            if task_id:
                progress_tracker.update_progress(task_id, 10, "Loading PDF document...")
            
            # Convert at high DPI for better OCR accuracy
            images = convert_from_path(pdf_path, dpi=Config.PDF_DPI, fmt=Config.IMAGE_FORMAT)
            total_pages = len(images)
            
            logging.info(f"Converting {total_pages} PDF pages to images...")
            
            if task_id:
                progress_tracker.update_progress(task_id, 20, f"Converting {total_pages} pages to images...")
            
            image_paths = []
            for page_num, img in enumerate(images, 1):
                logging.info(f"Converting page {page_num}/{total_pages} to image...")
                
                # Save each page as a high-quality image
                image_path = os.path.join(output_dir, f'page_{page_num:03d}.png')
                img.save(image_path, Config.IMAGE_FORMAT, quality=Config.IMAGE_QUALITY)
                image_paths.append(image_path)
                
                # Update progress
                progress_percent = 20 + (page_num / total_pages) * 60  # 20-80%
                if task_id:
                    progress_tracker.update_progress(task_id, progress_percent, 
                                                   f"Converting page {page_num}/{total_pages}...")
                
                logging.info(f"Page {page_num} saved as: {os.path.basename(image_path)}")
            
            if task_id:
                progress_tracker.update_progress(task_id, 90, "Creating download package...")
            
            logging.info(f"PDF conversion completed. {len(image_paths)} images created.")
            return image_paths
            
        except Exception as e:
            if task_id:
                progress_tracker.update_progress(task_id, 0, f"Error: {str(e)}")
            logging.error(f"Error converting PDF to images: {e}")
            raise
    
    @staticmethod
    def batch_convert_pdfs_to_images(pdf_files, output_dir=None, task_id=None):
        """
        Converts multiple PDF files to high-quality images SEQUENTIALLY.
        Processes one PDF at a time to avoid resource overload.
        Returns dict mapping PDF filename to list of image file paths.
        """
        if not output_dir:
            output_dir = Config.UPLOAD_FOLDER
        
        results = {}
        total_pdfs = len(pdf_files)
        
        try:
            if task_id:
                progress_tracker.update_progress(task_id, 2, 
                                               f"Starting sequential conversion of {total_pdfs} PDF files...")
            
            # Process each PDF sequentially (one at a time)
            for pdf_idx, (pdf_filename, pdf_path) in enumerate(pdf_files.items(), 1):
                base_progress = 5 + (pdf_idx - 1) * 85 / total_pdfs
                
                if task_id:
                    progress_tracker.update_progress(task_id, base_progress, 
                                                   f"📄 Processing PDF {pdf_idx}/{total_pdfs}: {pdf_filename}")
                
                logging.info(f"📄 Processing PDF {pdf_idx}/{total_pdfs}: {pdf_filename}")
                
                try:
                    # Load PDF and get page count
                    if task_id:
                        progress_tracker.update_progress(task_id, base_progress + 2, 
                                                       f"📖 Loading PDF {pdf_idx}: {pdf_filename}...")
                    
                    images = convert_from_path(pdf_path, dpi=Config.PDF_DPI, fmt=Config.IMAGE_FORMAT)
                    total_pages = len(images)
                    pdf_images = []
                    
                    if task_id:
                        progress_tracker.update_progress(task_id, base_progress + 5, 
                                                       f"📄 PDF {pdf_idx}: Converting {total_pages} pages...")
                    
                    # Create subfolder for each PDF
                    pdf_folder = os.path.join(output_dir, f"{os.path.splitext(pdf_filename)[0]}_images")
                    os.makedirs(pdf_folder, exist_ok=True)
                    
                    # Convert each page sequentially
                    for page_num, img in enumerate(images, 1):
                        # Update progress more frequently for better user feedback
                        page_progress = base_progress + 5 + (page_num / total_pages) * 75
                        if task_id:
                            progress_tracker.update_progress(task_id, page_progress, 
                                                           f"📄 PDF {pdf_idx}/{total_pdfs} - Page {page_num}/{total_pages}: {os.path.basename(pdf_filename)}")
                        
                        # Add a small progress update before intensive image operations
                        if task_id and page_num > 1:
                            progress_tracker.update_progress(task_id, page_progress + 0.5, 
                                                           f"💾 Saving page {page_num}/{total_pages} from {os.path.basename(pdf_filename)}...")
                        
                        image_path = os.path.join(pdf_folder, f'page_{page_num:03d}.png')
                        img.save(image_path, Config.IMAGE_FORMAT, quality=Config.IMAGE_QUALITY)
                        pdf_images.append(image_path)
                        
                        logging.info(f"  ✅ Page {page_num}/{total_pages} converted for {pdf_filename}")
                    
                    results[pdf_filename] = pdf_images
                    
                    completion_progress = base_progress + 80
                    if task_id:
                        progress_tracker.update_progress(task_id, completion_progress, 
                                                       f"✅ Completed PDF {pdf_idx}/{total_pdfs}: {len(pdf_images)} images created")
                    
                    logging.info(f"✅ Completed PDF {pdf_idx}/{total_pdfs}: {len(pdf_images)} images created")
                    
                except Exception as e:
                    error_msg = f"❌ Error processing PDF {pdf_idx} ({pdf_filename}): {str(e)}"
                    logging.error(error_msg)
                    if task_id:
                        progress_tracker.update_progress(task_id, base_progress + 80, error_msg)
                    # Continue with next PDF instead of stopping
                    results[pdf_filename] = []
            
            if task_id:
                progress_tracker.update_progress(task_id, 95, "📦 Creating download package...")
            
            success_count = len([k for k, v in results.items() if v])
            final_msg = f"🎉 Batch conversion completed! {success_count}/{total_pdfs} PDFs processed successfully."
            logging.info(final_msg)
            
            return results
            
        except Exception as e:
            error_msg = f"❌ Critical error in batch PDF conversion: {str(e)}"
            if task_id:
                progress_tracker.update_progress(task_id, 0, error_msg)
            logging.error(error_msg)
            raise
