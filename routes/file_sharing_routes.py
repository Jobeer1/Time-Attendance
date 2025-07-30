"""
Medical File Sharing API Routes
Handles large DICOM and medical image file uploads and sharing
"""

from flask import Blueprint, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import tempfile
from typing import Dict, List

from models.medical_file_sharing import (
    MedicalFileManager, FileCategory, FileType, file_manager
)

file_sharing_bp = Blueprint('file_sharing', __name__, url_prefix='/api/files')

# Configure upload settings
UPLOAD_FOLDER = 'temp_uploads'
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@file_sharing_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a large medical file"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get form data
        uploaded_by = request.form.get('uploaded_by')
        file_category = request.form.get('file_category', 'other')
        patient_id = request.form.get('patient_id')
        study_description = request.form.get('study_description')
        access_level = request.form.get('access_level', 'restricted')
        compress_large = request.form.get('compress_large', 'true').lower() == 'true'
        
        if not uploaded_by:
            return jsonify({'success': False, 'error': 'uploaded_by is required'}), 400
        
        # Validate file category
        try:
            category = FileCategory(file_category)
        except ValueError:
            category = FileCategory.OTHER
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
        file.save(temp_path)
        
        try:
            # Upload to file manager
            success, file_id, message = file_manager.upload_file(
                file_path=temp_path,
                uploaded_by=uploaded_by,
                file_category=category,
                patient_id=patient_id,
                study_description=study_description,
                compress_large_files=compress_large,
                access_level=access_level
            )
            
            if success:
                # Get file metadata for response
                metadata = file_manager.get_file_info(file_id)
                
                response_data = {
                    'success': True,
                    'file_id': file_id,
                    'message': message,
                    'file_info': {
                        'original_filename': metadata.original_filename,
                        'file_size_mb': round(metadata.file_size / (1024 * 1024), 2),
                        'file_type': metadata.file_type.value,
                        'file_category': metadata.file_category.value,
                        'is_compressed': metadata.is_compressed,
                        'compression_ratio': metadata.compression_ratio,
                        'upload_timestamp': metadata.upload_timestamp.isoformat()
                    }
                }
                
                return jsonify(response_data)
            else:
                return jsonify({'success': False, 'error': message}), 500
                
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/share', methods=['POST'])
def create_share():
    """Create a file share link"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        file_id = data.get('file_id')
        shared_by = data.get('shared_by')
        shared_with = data.get('shared_with')  # Optional for public shares
        message_id = data.get('message_id')  # Link to message
        expires_hours = data.get('expires_hours', 168)  # Default 7 days
        download_limit = data.get('download_limit')
        password_protected = data.get('password_protected', False)
        
        if not file_id or not shared_by:
            return jsonify({
                'success': False, 
                'error': 'file_id and shared_by are required'
            }), 400
        
        success, share_id, message = file_manager.create_file_share(
            file_id=file_id,
            shared_by=shared_by,
            shared_with=shared_with,
            message_id=message_id,
            expires_hours=expires_hours,
            download_limit=download_limit,
            password_protected=password_protected
        )
        
        if success:
            # Get share and file info
            share = file_manager.get_share_info(share_id)
            metadata = file_manager.get_file_info(file_id)
            
            response_data = {
                'success': True,
                'share_id': share_id,
                'message': message,
                'share_info': {
                    'share_url': f"/api/files/download/{share_id}",
                    'expires_at': share.expires_at.isoformat() if share.expires_at else None,
                    'download_limit': share.download_limit,
                    'file_name': metadata.original_filename,
                    'file_size_mb': round(metadata.file_size / (1024 * 1024), 2)
                }
            }
            
            return jsonify(response_data)
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/download/<share_id>', methods=['GET'])
def download_file(share_id):
    """Download a shared file"""
    try:
        # Get user info from query params or headers
        accessed_by = request.args.get('user_id', 'anonymous')
        user_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        
        success, file_path, message = file_manager.download_file(
            share_id=share_id,
            accessed_by=accessed_by,
            user_ip=user_ip
        )
        
        if not success:
            return jsonify({'success': False, 'error': message}), 404
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found on disk'}), 404
        
        # Get file info for download
        share = file_manager.get_share_info(share_id)
        metadata = file_manager.get_file_info(share.file_id)
        
        # Set appropriate filename for download
        download_name = metadata.original_filename
        if metadata.is_compressed and not metadata.original_filename.endswith('.zip'):
            download_name = f"{metadata.original_filename}.zip"
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype=metadata.mime_type
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/info/<share_id>', methods=['GET'])
def get_share_info(share_id):
    """Get information about a shared file"""
    try:
        share = file_manager.get_share_info(share_id)
        
        if not share:
            return jsonify({'success': False, 'error': 'Invalid or expired share'}), 404
        
        metadata = file_manager.get_file_info(share.file_id)
        
        if not metadata:
            return jsonify({'success': False, 'error': 'File metadata not found'}), 404
        
        response_data = {
            'success': True,
            'share_info': {
                'share_id': share_id,
                'file_name': metadata.original_filename,
                'file_size_mb': round(metadata.file_size / (1024 * 1024), 2),
                'file_type': metadata.file_type.value,
                'file_category': metadata.file_category.value,
                'upload_date': metadata.upload_timestamp.isoformat(),
                'uploaded_by': metadata.uploaded_by,
                'study_description': metadata.study_description,
                'patient_id': metadata.patient_id,
                'expires_at': share.expires_at.isoformat() if share.expires_at else None,
                'download_count': len(share.access_log),
                'download_limit': share.download_limit,
                'is_compressed': metadata.is_compressed,
                'compression_ratio': metadata.compression_ratio
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/user-files/<user_id>', methods=['GET'])
def get_user_files(user_id):
    """Get all files uploaded by a user"""
    try:
        files = file_manager.get_user_files(user_id)
        
        files_data = []
        for metadata in files:
            files_data.append({
                'file_id': metadata.file_id,
                'original_filename': metadata.original_filename,
                'file_size_mb': round(metadata.file_size / (1024 * 1024), 2),
                'file_type': metadata.file_type.value,
                'file_category': metadata.file_category.value,
                'upload_date': metadata.upload_timestamp.isoformat(),
                'download_count': metadata.download_count,
                'last_accessed': metadata.last_accessed.isoformat() if metadata.last_accessed else None,
                'study_description': metadata.study_description,
                'patient_id': metadata.patient_id,
                'is_compressed': metadata.is_compressed
            })
        
        return jsonify({
            'success': True,
            'files': files_data,
            'total_files': len(files_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/shared-with-me/<user_id>', methods=['GET'])
def get_shared_files(user_id):
    """Get all files shared with a user"""
    try:
        shared_files = file_manager.get_shared_files(user_id)
        
        files_data = []
        for metadata, share in shared_files:
            files_data.append({
                'share_id': share.share_id,
                'file_id': metadata.file_id,
                'original_filename': metadata.original_filename,
                'file_size_mb': round(metadata.file_size / (1024 * 1024), 2),
                'file_type': metadata.file_type.value,
                'file_category': metadata.file_category.value,
                'upload_date': metadata.upload_timestamp.isoformat(),
                'shared_by': share.shared_by,
                'shared_date': share.created_at.isoformat(),
                'expires_at': share.expires_at.isoformat() if share.expires_at else None,
                'download_count': len(share.access_log),
                'study_description': metadata.study_description,
                'patient_id': metadata.patient_id,
                'download_url': f"/api/files/download/{share.share_id}"
            })
        
        return jsonify({
            'success': True,
            'shared_files': files_data,
            'total_files': len(files_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file"""
    try:
        deleted_by = request.args.get('user_id')
        
        if not deleted_by:
            return jsonify({'success': False, 'error': 'user_id is required'}), 400
        
        success, message = file_manager.delete_file(file_id, deleted_by)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 403
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/stats', methods=['GET'])
def get_storage_stats():
    """Get storage statistics"""
    try:
        stats = file_manager.get_storage_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@file_sharing_bp.route('/categories', methods=['GET'])
def get_file_categories():
    """Get available file categories"""
    try:
        categories = [
            {
                'value': category.value,
                'name': category.value.replace('_', ' ').title(),
                'description': get_category_description(category)
            }
            for category in FileCategory
        ]
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_category_description(category: FileCategory) -> str:
    """Get description for file category"""
    descriptions = {
        FileCategory.CT_SCAN: "CT Scan Images and Series",
        FileCategory.MRI_SCAN: "MRI Images and Series", 
        FileCategory.XRAY: "X-Ray Images",
        FileCategory.ULTRASOUND: "Ultrasound Images and Videos",
        FileCategory.MAMMOGRAPHY: "Mammography Images",
        FileCategory.PET_SCAN: "PET Scan Images",
        FileCategory.NUCLEAR_MEDICINE: "Nuclear Medicine Images",
        FileCategory.PATHOLOGY: "Pathology Images and Reports",
        FileCategory.REPORT: "Medical Reports and Documents",
        FileCategory.OTHER: "Other Medical Files"
    }
    
    return descriptions.get(category, "Medical File")

# Template routes for file sharing interfaces
@file_sharing_bp.route('/interface', methods=['GET'])
def file_sharing_interface():
    """File sharing interface"""
    return render_template('attendance/file_sharing.html')

@file_sharing_bp.route('/viewer/<share_id>', methods=['GET'])
def file_viewer(share_id):
    """File viewer interface"""
    return render_template('attendance/file_viewer.html', share_id=share_id)

def register_file_sharing_routes(app):
    """Register file sharing routes with the Flask app"""
    # Set maximum content length for large file uploads
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    
    app.register_blueprint(file_sharing_bp)
    return file_sharing_bp, file_manager
