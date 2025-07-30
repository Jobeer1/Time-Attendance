"""
Folder Sharing API Routes
Handles large folder uploads, processing, and sharing between employees
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import tempfile
import json
from typing import Dict, List

from models.folder_sharing import (
    FolderSharingManager, folder_manager, CompressionLevel, FolderStatus
)

folder_sharing_bp = Blueprint('folder_sharing', __name__, url_prefix='/api/folder-sharing')

@folder_sharing_bp.route('/start-upload', methods=['POST'])
def start_folder_upload():
    """Start a new folder upload session"""
    try:
        data = request.get_json()
        
        folder_name = data.get('folder_name')
        uploaded_by = data.get('uploaded_by')
        expected_files = data.get('expected_files', 0)
        
        if not folder_name or not uploaded_by:
            return jsonify({
                'success': False,
                'error': 'folder_name and uploaded_by are required'
            }), 400
        
        folder_id = folder_manager.create_folder_upload_session(
            folder_name=folder_name,
            uploaded_by=uploaded_by,
            expected_files=expected_files
        )
        
        return jsonify({
            'success': True,
            'folder_id': folder_id,
            'message': 'Folder upload session created'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error starting folder upload: {str(e)}'
        }), 500

@folder_sharing_bp.route('/upload-file/<folder_id>', methods=['POST'])
def upload_file_to_folder(folder_id):
    """Upload a single file to a folder"""
    try:
        # Validate folder_id
        if folder_id not in folder_manager.folder_metadata:
            return jsonify({'success': False, 'error': 'Invalid folder_id'}), 404

        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get relative path (maintains folder structure)
        relative_path = request.form.get('relative_path', file.filename)
        
        # Upload file to folder
        success, result = folder_manager.upload_file_to_folder(
            folder_id=folder_id,
            file_data=file,
            relative_path=relative_path
        )
        
        if not success:
            return jsonify({'success': False, 'error': result}), 400

        return jsonify({'success': True, 'message': 'File uploaded successfully'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@folder_sharing_bp.route('/batch-upload/<folder_id>', methods=['POST'])
def batch_upload_files(folder_id):
    """Upload multiple files to a folder in batch"""
    try:
        # Validate folder_id
        if folder_id not in folder_manager.folder_metadata:
            return jsonify({'success': False, 'error': 'Invalid folder_id'}), 404

        uploaded_files = []
        errors = []

        # Process all uploaded files
        for key, file in request.files.items():
            if file.filename == '':
                continue

            # Get relative path from form data
            relative_path_key = f"{key}_path"
            relative_path = request.form.get(relative_path_key, file.filename)

            # Upload file
            success, result = folder_manager.upload_file_to_folder(
                folder_id=folder_id,
                file_data=file,
                relative_path=relative_path
            )

            if success:
                uploaded_files.append(result)
            else:
                errors.append({"file": file.filename, "error": result})

        return jsonify({
            'success': True,
            'uploaded_files': uploaded_files,
            'errors': errors
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@folder_sharing_bp.route('/finalize/<folder_id>', methods=['POST'])
def finalize_folder_upload(folder_id):
    """Finalize folder upload and start processing"""
    try:
        data = request.get_json() or {}
        
        # Get compression level
        compression_level_str = data.get('compression_level', 'balanced')
        compression_level = CompressionLevel(compression_level_str)
        
        success, result = folder_manager.finalize_folder_upload(
            folder_id=folder_id,
            compression_level=compression_level
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error finalizing folder: {str(e)}'
        }), 500

@folder_sharing_bp.route('/info/<folder_id>', methods=['GET'])
def get_folder_info(folder_id):
    """Get folder information and processing status"""
    try:
        folder_info = folder_manager.get_folder_info(folder_id)
        
        if folder_info:
            return jsonify({
                'success': True,
                'folder': folder_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Folder not found'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting folder info: {str(e)}'
        }), 500

@folder_sharing_bp.route('/share', methods=['POST'])
def share_folder():
    """Share a folder with employees"""
    try:
        data = request.get_json()
        
        folder_id = data.get('folder_id')
        shared_by = data.get('shared_by')
        shared_with = data.get('shared_with')  # List of employee IDs or None for broadcast
        message_id = data.get('message_id')
        expires_days = data.get('expires_days', 7)
        
        if not folder_id or not shared_by:
            return jsonify({
                'success': False,
                'error': 'folder_id and shared_by are required'
            }), 400
        
        success, result = folder_manager.share_folder(
            folder_id=folder_id,
            shared_by=shared_by,
            shared_with=shared_with,
            message_id=message_id,
            expires_days=expires_days
        )
        
        if success:
            return jsonify({
                'success': True,
                'share_id': result,
                'message': 'Folder shared successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error sharing folder: {str(e)}'
        }), 500

@folder_sharing_bp.route('/download/<share_id>', methods=['GET'])
def download_folder(share_id):
    """Download folder as ZIP archive"""
    try:
        employee_id = request.args.get('employee_id')
        
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'employee_id is required'
            }), 400
        
        success, archive_path, folder_name = folder_manager.download_folder_archive(
            share_id=share_id,
            employee_id=employee_id
        )
        
        if success:
            return send_file(
                archive_path,
                as_attachment=True,
                download_name=f"{folder_name}.zip",
                mimetype='application/zip'
            )
        else:
            return jsonify({
                'success': False,
                'error': folder_name  # Error message is in folder_name when success=False
            }), 403
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error downloading folder: {str(e)}'
        }), 500

@folder_sharing_bp.route('/my-folders/<employee_id>', methods=['GET'])
def get_employee_folders(employee_id):
    """Get folders shared with an employee"""
    try:
        folders = folder_manager.get_employee_shared_folders(employee_id)
        
        return jsonify({
            'success': True,
            'folders': folders
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting employee folders: {str(e)}'
        }), 500

@folder_sharing_bp.route('/upload-status/<folder_id>', methods=['GET'])
def get_upload_status(folder_id):
    """Get real-time upload and processing status"""
    try:
        folder_info = folder_manager.get_folder_info(folder_id)
        
        if not folder_info:
            return jsonify({
                'success': False,
                'error': 'Folder not found'
            }), 404
        
        return jsonify({
            'success': True,
            'status': folder_info['status'],
            'processing_progress': folder_info['processing_progress'],
            'total_files': folder_info['total_files'],
            'total_size': folder_info['total_size'],
            'compressed_size': folder_info['compressed_size'],
            'compression_ratio': folder_info['compression_ratio']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting upload status: {str(e)}'
        }), 500

@folder_sharing_bp.route('/cancel-upload/<folder_id>', methods=['POST'])
def cancel_folder_upload(folder_id):
    """Cancel an ongoing folder upload"""
    try:
        # This would cancel the upload and clean up
        folder_manager._cleanup_folder(folder_id)
        
        return jsonify({
            'success': True,
            'message': 'Folder upload cancelled'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error cancelling upload: {str(e)}'
        }), 500

@folder_sharing_bp.route('/folder-structure/<folder_id>', methods=['GET'])
def get_folder_structure(folder_id):
    """Get detailed folder structure"""
    try:
        folder_info = folder_manager.get_folder_info(folder_id)
        
        if not folder_info:
            return jsonify({
                'success': False,
                'error': 'Folder not found'
            }), 404
        
        return jsonify({
            'success': True,
            'structure': folder_info['folder_structure'],
            'folder_name': folder_info['folder_name'],
            'total_files': folder_info['total_files'],
            'total_size': folder_info['total_size']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting folder structure: {str(e)}'
        }), 500

@folder_sharing_bp.route('/compress/<folder_id>', methods=['POST'])
def recompress_folder(folder_id):
    """Recompress folder with different compression level"""
    try:
        data = request.get_json() or {}
        compression_level_str = data.get('compression_level', 'balanced')
        compression_level = CompressionLevel(compression_level_str)
        
        if folder_id not in folder_manager.folder_metadata:
            return jsonify({
                'success': False,
                'error': 'Folder not found'
            }), 404
        
        metadata = folder_manager.folder_metadata[folder_id]
        metadata.compression_level = compression_level
        metadata.status = FolderStatus.PROCESSING
        metadata.processing_progress = 0.0
        
        # Start reprocessing
        import threading
        threading.Thread(
            target=folder_manager._process_folder_async,
            args=(folder_id,),
            daemon=True
        ).start()
        
        return jsonify({
            'success': True,
            'message': 'Folder recompression started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error recompressing folder: {str(e)}'
        }), 500

@folder_sharing_bp.route('/validate-metadata', methods=['POST'])
def validate_metadata():
    """Validate and repair folder metadata JSON file."""
    try:
        metadata_path = current_app.config.get('FOLDER_METADATA_PATH', 'folder_metadata.json')

        # Check if metadata file exists
        if not os.path.exists(metadata_path):
            return jsonify({
                'success': False,
                'error': 'Metadata file not found.'
            }), 404

        # Load and validate JSON
        with open(metadata_path, 'r') as f:
            try:
                metadata = json.load(f)
            except json.JSONDecodeError:
                return jsonify({
                    'success': False,
                    'error': 'Metadata file is corrupted.'
                }), 500

        # Check for required keys
        if not isinstance(metadata, dict):
            return jsonify({
                'success': False,
                'error': 'Invalid metadata structure.'
            }), 500

        return jsonify({
            'success': True,
            'message': 'Metadata file is valid.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error validating metadata: {str(e)}'
        }), 500

@folder_sharing_bp.route('/repair-metadata', methods=['POST'])
def repair_metadata():
    """Repair corrupted folder metadata JSON file."""
    try:
        metadata_path = current_app.config.get('FOLDER_METADATA_PATH', 'folder_metadata.json')

        # Create a new metadata file if it doesn't exist or is corrupted
        default_metadata = {
            'folders': {},
            'shared_folders': {}
        }

        with open(metadata_path, 'w') as f:
            json.dump(default_metadata, f, indent=4)

        return jsonify({
            'success': True,
            'message': 'Metadata file has been repaired.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error repairing metadata: {str(e)}'
        }), 500

# Error handlers
@folder_sharing_bp.errorhandler(413)
def file_too_large(error):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 500MB per file.'
    }), 413

@folder_sharing_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

@folder_sharing_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
