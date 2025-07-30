"""
Enterprise LAN Large File/Folder Sharing API Routes
Optimized for multi-gigabyte files and folder sharing within corporate LAN
Complements the medical imaging system with enterprise-focused features
"""

from flask import Blueprint, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import tempfile
from typing import Dict, List

from models.lan_file_sharing import (
    LANFileManager, LANFileType, LANAccessLevel, lan_file_manager
)

lan_sharing_bp = Blueprint('lan_sharing', __name__, url_prefix='/api/lan-sharing')

# Configure upload settings for enterprise large files
MAX_CONTENT_LENGTH = 50 * 1024 * 1024 * 1024  # 50GB max file size for enterprise
ALLOWED_EXTENSIONS = {
    # Database & Backup Files
    'db', 'sql', 'bak', 'backup',
    
    # Virtual Machine Files
    'vmdk', 'vdi', 'qcow2', 'vhd',
    
    # ISO Images
    'iso', 'img',
    
    # Large Media Files (professional/uncompressed)
    'mov', 'avi', 'mkv', 'raw', 'dng', 'tiff', 'tif',
    'wav', 'flac', 'aiff',
    
    # Engineering/CAD Files
    'asm', 'prt', 'catpart', 'sldprt', 'dwg', 'dxf',
    'las', 'e57', 'ply', 'shp', 'geotiff',
    
    # Software/Development
    'tar', 'gz', 'xz', 'git',
    
    # Large Archives
    '7z', 'rar', 'zip',
    
    # Project Files
    'prproj', 'aep', 'blend', 'max', 'ma', 'mb',
    
    # General large files
    'bin', 'exe', 'msi', 'dmg', 'pkg'
}

def get_client_ip():
    """Get client IP address with proper handling for proxies"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@lan_sharing_bp.route('/upload', methods=['POST'])
def upload_lan_file():
    """Upload a file for LAN sharing"""
    try:
        # Validate LAN access
        client_ip = get_client_ip()
        if not lan_file_manager.validate_lan_access(client_ip):
            return jsonify({
                'success': False,
                'error': 'Access denied: Must be connected to company LAN'
            }), 403
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
            }), 400
        
        # Get form data
        uploaded_by = request.form.get('uploaded_by')
        uploaded_by_name = request.form.get('uploaded_by_name')
        department = request.form.get('department')
        access_level = request.form.get('access_level', 'department')
        description = request.form.get('description')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
        is_confidential = request.form.get('is_confidential', 'false').lower() == 'true'
        
        # Validate required fields
        if not uploaded_by or not uploaded_by_name or not department:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: uploaded_by, uploaded_by_name, department'
            }), 400
        
        # Validate access level
        try:
            access_level_enum = LANAccessLevel(access_level)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid access level. Valid options: {[e.value for e in LANAccessLevel]}'
            }), 400
        
        # Upload file
        success, file_id, message = lan_file_manager.upload_file(
            file_obj=file,
            uploaded_by=uploaded_by,
            uploaded_by_name=uploaded_by_name,
            department=department,
            access_level=access_level_enum,
            description=description,
            tags=[tag.strip() for tag in tags if tag.strip()],
            is_confidential=is_confidential
        )
        
        if success:
            return jsonify({
                'success': True,
                'file_id': file_id,
                'message': message,
                'filename': file.filename
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500

@lan_sharing_bp.route('/share', methods=['POST'])
def create_lan_share():
    """Create a LAN file share"""
    try:
        # Validate LAN access
        client_ip = get_client_ip()
        if not lan_file_manager.validate_lan_access(client_ip):
            return jsonify({
                'success': False,
                'error': 'Access denied: Must be connected to company LAN'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Required fields
        file_id = data.get('file_id')
        shared_by = data.get('shared_by')
        shared_by_name = data.get('shared_by_name')
        
        if not file_id or not shared_by or not shared_by_name:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: file_id, shared_by, shared_by_name'
            }), 400
        
        # Optional fields
        shared_with_users = data.get('shared_with_users', [])
        shared_with_departments = data.get('shared_with_departments', [])
        expires_hours = data.get('expires_hours', 24)
        download_limit = data.get('download_limit')
        share_message = data.get('share_message')
        
        # Create share
        success, share_id, message = lan_file_manager.create_lan_share(
            file_id=file_id,
            shared_by=shared_by,
            shared_by_name=shared_by_name,
            shared_with_users=shared_with_users,
            shared_with_departments=shared_with_departments,
            expires_hours=expires_hours,
            download_limit=download_limit,
            share_message=share_message
        )
        
        if success:
            return jsonify({
                'success': True,
                'share_id': share_id,
                'message': message,
                'share_url': f'/api/lan-sharing/download/{share_id}',
                'expires_hours': expires_hours
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Share creation failed: {str(e)}'
        }), 500

@lan_sharing_bp.route('/download/<share_id>', methods=['GET'])
def download_lan_file(share_id):
    """Download a shared file (LAN only)"""
    try:
        # Validate LAN access
        client_ip = get_client_ip()
        if not lan_file_manager.validate_lan_access(client_ip):
            return jsonify({
                'success': False,
                'error': 'Access denied: Must be connected to company LAN'
            }), 403
        
        # Get requesting user from query params or headers
        requesting_user = request.args.get('user_id') or request.headers.get('X-User-ID')
        if not requesting_user:
            return jsonify({
                'success': False,
                'error': 'User ID required for download'
            }), 400
        
        # Get file for download
        success, file_path, file_meta, message = lan_file_manager.get_file_for_download(
            share_id=share_id,
            requesting_user=requesting_user,
            request_ip=client_ip
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': message
            }), 403 if 'Access denied' in message else 404
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_meta['original_filename'],
            mimetype=file_meta['mime_type']
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500

@lan_sharing_bp.route('/files', methods=['GET'])
def list_lan_files():
    """List files accessible to user on LAN"""
    try:
        # Validate LAN access
        client_ip = get_client_ip()
        if not lan_file_manager.validate_lan_access(client_ip):
            return jsonify({
                'success': False,
                'error': 'Access denied: Must be connected to company LAN'
            }), 403
        
        # Get user info
        user_id = request.args.get('user_id') or request.headers.get('X-User-ID')
        user_department = request.args.get('department') or request.headers.get('X-User-Department')
        
        if not user_id or not user_department:
            return jsonify({
                'success': False,
                'error': 'User ID and department required'
            }), 400
        
        # Get accessible files
        files = lan_file_manager.list_lan_files(user_id, user_department)
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to list files: {str(e)}'
        }), 500

@lan_sharing_bp.route('/stats', methods=['GET'])
def get_lan_stats():
    """Get LAN file sharing statistics"""
    try:
        # Validate LAN access
        client_ip = get_client_ip()
        if not lan_file_manager.validate_lan_access(client_ip):
            return jsonify({
                'success': False,
                'error': 'Access denied: Must be connected to company LAN'
            }), 403
        
        metadata = lan_file_manager._load_metadata()
        shares = lan_file_manager._load_shares()
        
        # Calculate stats
        total_files = len(metadata)
        total_shares = len(shares)
        total_size = sum(file_meta.get('file_size', 0) for file_meta in metadata.values())
        
        # File type distribution
        file_types = {}
        for file_meta in metadata.values():
            file_type = file_meta.get('file_type', 'other')
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # Department distribution
        departments = {}
        for file_meta in metadata.values():
            dept = file_meta.get('department', 'Unknown')
            departments[dept] = departments.get(dept, 0) + 1
        
        # Active shares
        active_shares = sum(1 for share in shares.values() if share.get('is_active', True))
        
        return jsonify({
            'success': True,
            'stats': {
                'total_files': total_files,
                'total_shares': total_shares,
                'active_shares': active_shares,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': file_types,
                'departments': departments
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get stats: {str(e)}'
        }), 500

# Template routes for LAN sharing interfaces
@lan_sharing_bp.route('/interface', methods=['GET'])
def lan_sharing_interface():
    """LAN file sharing interface"""
    return render_template('attendance/lan_file_sharing.html')

@lan_sharing_bp.route('/admin-interface', methods=['GET'])
def lan_admin_interface():
    """LAN file sharing admin interface"""
    return render_template('attendance/lan_file_admin.html')

@lan_sharing_bp.route('/help', methods=['GET'])
def lan_sharing_help():
    """LAN file sharing help page"""
    return render_template('attendance/lan_file_help.html')
