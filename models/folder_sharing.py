"""
Advanced Folder Sharing System for Employee Messaging
Handles large folder uploads, maintains folder structure, and enables efficient sharing
"""

import os
import hashlib
import shutil
import zipfile
import tempfile
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import json
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import mimetypes

class FolderStatus(Enum):
    """Folder processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    EXPIRED = "expired"

class CompressionLevel(Enum):
    """Compression levels for folder archives"""
    NONE = "none"
    FAST = "fast"
    BALANCED = "balanced"
    MAXIMUM = "maximum"

@dataclass
class FolderFile:
    """Individual file within a folder"""
    file_id: str
    relative_path: str  # Path relative to folder root
    original_name: str
    file_size: int
    mime_type: str
    md5_hash: str
    upload_timestamp: datetime
    is_processed: bool = False
    processing_error: Optional[str] = None

@dataclass
class FolderMetadata:
    """Metadata for shared folders"""
    folder_id: str
    folder_name: str
    total_files: int
    total_size: int
    uploaded_by: str
    upload_timestamp: datetime
    status: FolderStatus
    files: List[FolderFile] = field(default_factory=list)
    folder_structure: Dict = field(default_factory=dict)  # Nested structure representation
    compression_level: CompressionLevel = CompressionLevel.BALANCED
    compressed_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    download_count: int = 0
    last_accessed: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    processing_progress: float = 0.0
    error_message: Optional[str] = None

@dataclass
class FolderShare:
    """Folder sharing record"""
    share_id: str
    folder_id: str
    shared_by: str
    shared_with: Optional[List[str]] = None  # List of employee IDs, None for broadcast
    message_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    download_limit: Optional[int] = None
    password_protected: bool = False
    access_log: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    allow_individual_file_download: bool = True
    require_folder_download: bool = False

class FolderSharingManager:
    """Manages large folder uploads, processing, and sharing between employees"""
    
    def __init__(self, base_storage_path: str = "folder_storage"):
        self.base_path = Path(base_storage_path)
        self.metadata_file = self.base_path / "folder_metadata.json"
        self.shares_file = self.base_path / "folder_shares.json"
        
        # Create directory structure
        self.folders_path = self.base_path / "folders"
        self.archives_path = self.base_path / "archives"
        self.temp_path = self.base_path / "temp"
        
        for path in [self.folders_path, self.archives_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self.folder_metadata: Dict[str, FolderMetadata] = self._load_metadata()
        self.folder_shares: Dict[str, FolderShare] = self._load_shares()
        
        # Processing settings
        self.max_folder_size = 5 * 1024 * 1024 * 1024  # 5GB max folder size
        self.max_files_per_folder = 10000  # Maximum files per folder
        self.processing_threads = 4  # Number of parallel processing threads
        self.cleanup_interval = 3600  # Cleanup expired folders every hour
        
        # Supported file types
        self.allowed_extensions = {
            # Medical/Scientific files
            '.dcm', '.dicom', '.nii', '.nii.gz', '.tif', '.tiff',
            # Images
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz',
            # Text files
            '.txt', '.csv', '.json', '.xml', '.yaml', '.yml', '.md', '.rst',
            # Code files
            '.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx',
            '.py', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb',
            '.go', '.rs', '.kt', '.swift', '.sql', '.sh', '.bat', '.ps1',
            '.vue', '.angular', '.scss', '.sass', '.less', '.styl',
            # Config files
            '.ini', '.conf', '.config', '.properties', '.env',
            '.gitignore', '.gitattributes', '.editorconfig',
            # Other
            '.log', '.bak', '.tmp'
        }
        
        # Start background tasks
        self._start_cleanup_thread()

    def _load_metadata(self) -> Dict[str, FolderMetadata]:
        """Load folder metadata from JSON"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = {}
            for folder_id, meta_dict in data.items():
                # Convert datetime strings back to datetime objects
                meta_dict['upload_timestamp'] = datetime.fromisoformat(meta_dict['upload_timestamp'])
                if meta_dict.get('last_accessed'):
                    meta_dict['last_accessed'] = datetime.fromisoformat(meta_dict['last_accessed'])
                if meta_dict.get('expires_at'):
                    meta_dict['expires_at'] = datetime.fromisoformat(meta_dict['expires_at'])
                
                # Convert file timestamps
                for file_info in meta_dict.get('files', []):
                    file_info['upload_timestamp'] = datetime.fromisoformat(file_info['upload_timestamp'])
                
                # Convert enums
                meta_dict['status'] = FolderStatus(meta_dict['status'])
                meta_dict['compression_level'] = CompressionLevel(meta_dict['compression_level'])
                
                # Create FolderFile objects
                files = []
                for file_info in meta_dict.get('files', []):
                    files.append(FolderFile(**file_info))
                meta_dict['files'] = files
                
                metadata[folder_id] = FolderMetadata(**meta_dict)
            
            return metadata
        except Exception as e:
            print(f"Error loading folder metadata: {e}")
            return {}

    def _save_metadata(self):
        """Save folder metadata to JSON"""
        try:
            data = {}
            for folder_id, metadata in self.folder_metadata.items():
                meta_dict = asdict(metadata)
                
                # Convert datetime objects to strings
                meta_dict['upload_timestamp'] = metadata.upload_timestamp.isoformat()
                if metadata.last_accessed:
                    meta_dict['last_accessed'] = metadata.last_accessed.isoformat()
                if metadata.expires_at:
                    meta_dict['expires_at'] = metadata.expires_at.isoformat()
                
                # Convert file timestamps
                for file_info in meta_dict['files']:
                    file_info['upload_timestamp'] = file_info['upload_timestamp'].isoformat()
                
                # Convert enums to strings
                meta_dict['status'] = metadata.status.value
                meta_dict['compression_level'] = metadata.compression_level.value
                
                data[folder_id] = meta_dict
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving folder metadata: {e}")

    def _load_shares(self) -> Dict[str, FolderShare]:
        """Load folder shares from JSON"""
        if not self.shares_file.exists():
            return {}
        
        try:
            with open(self.shares_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            shares = {}
            for share_id, share_dict in data.items():
                # Convert datetime strings back to datetime objects
                share_dict['created_at'] = datetime.fromisoformat(share_dict['created_at'])
                if share_dict.get('expires_at'):
                    share_dict['expires_at'] = datetime.fromisoformat(share_dict['expires_at'])
                
                shares[share_id] = FolderShare(**share_dict)
            
            return shares
        except Exception as e:
            print(f"Error loading folder shares: {e}")
            return {}

    def _save_shares(self):
        """Save folder shares to JSON"""
        try:
            data = {}
            for share_id, share in self.folder_shares.items():
                share_dict = asdict(share)
                
                # Convert datetime objects to strings
                share_dict['created_at'] = share.created_at.isoformat()
                if share.expires_at:
                    share_dict['expires_at'] = share.expires_at.isoformat()
                
                data[share_id] = share_dict
            
            with open(self.shares_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving folder shares: {e}")

    def create_folder_upload_session(self, folder_name: str, uploaded_by: str, 
                                   expected_files: int = None) -> str:
        """Create a new folder upload session"""
        folder_id = str(uuid.uuid4())
        
        # Create folder metadata
        metadata = FolderMetadata(
            folder_id=folder_id,
            folder_name=folder_name,
            total_files=expected_files or 0,
            total_size=0,
            uploaded_by=uploaded_by,
            upload_timestamp=datetime.now(),
            status=FolderStatus.UPLOADING,
            expires_at=datetime.now() + timedelta(days=30)  # Default 30-day expiration
        )
        
        self.folder_metadata[folder_id] = metadata
        
        # Create folder directory
        folder_path = self.folders_path / folder_id
        folder_path.mkdir(parents=True, exist_ok=True)
        
        self._save_metadata()
        
        return folder_id

    def upload_file_to_folder(self, folder_id: str, file_data, relative_path: str) -> Tuple[bool, str]:
        """Upload a single file to a folder, maintaining folder structure"""
        try:
            if folder_id not in self.folder_metadata:
                return False, "Folder session not found"
            
            metadata = self.folder_metadata[folder_id]
            
            if metadata.status != FolderStatus.UPLOADING:
                return False, "Folder is not in uploading state"
            
            # Validate file
            file_size = len(file_data) if isinstance(file_data, bytes) else file_data.content_length
            
            if file_size > 500 * 1024 * 1024:  # 500MB per file limit
                return False, "File too large (max 500MB per file)"
            
            # Check folder size limit
            current_size = sum(f.file_size for f in metadata.files)
            if current_size + file_size > self.max_folder_size:
                return False, "Folder size limit exceeded (max 5GB)"
            
            # Check file count limit
            if len(metadata.files) >= self.max_files_per_folder:
                return False, "Too many files in folder (max 10,000 files)"
            
            # Validate file extension
            file_ext = Path(relative_path).suffix.lower()
            
            # Block dangerous executable files for security
            dangerous_extensions = {'.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.ws', '.wsf'}
            if file_ext in dangerous_extensions:
                return False, f"File type {file_ext} not allowed for security reasons"
            
            # Allow files without extensions (common in code projects)
            if file_ext == '':
                # Additional check for common extensionless files
                filename = Path(relative_path).name.lower()
                common_files = {'readme', 'license', 'dockerfile', 'makefile', 'gitignore', 'manifest'}
                if filename not in common_files:
                    # Allow if it's likely a text file (simple heuristic)
                    pass
            elif file_ext not in self.allowed_extensions:
                return False, f"File type {file_ext} not allowed"
            
            # Generate file ID and calculate hash
            file_id = str(uuid.uuid4())
            
            if isinstance(file_data, bytes):
                file_content = file_data
            else:
                file_content = file_data.read()
            
            md5_hash = hashlib.md5(file_content).hexdigest()
            
            # Create full path maintaining folder structure
            full_relative_path = Path(relative_path)
            target_path = self.folders_path / folder_id / full_relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            with open(target_path, 'wb') as f:
                f.write(file_content)
            
            # Create file metadata
            folder_file = FolderFile(
                file_id=file_id,
                relative_path=relative_path,
                original_name=full_relative_path.name,
                file_size=len(file_content),
                mime_type=mimetypes.guess_type(relative_path)[0] or 'application/octet-stream',
                md5_hash=md5_hash,
                upload_timestamp=datetime.now(),
                is_processed=True
            )
            
            # Add to folder metadata
            metadata.files.append(folder_file)
            metadata.total_size += len(file_content)
            
            # Update folder structure
            self._update_folder_structure(metadata, relative_path)
            
            self._save_metadata()
            
            return True, file_id
            
        except Exception as e:
            return False, f"Error uploading file: {str(e)}"

    def _update_folder_structure(self, metadata: FolderMetadata, relative_path: str):
        """Update the folder structure representation"""
        path_parts = Path(relative_path).parts
        current_level = metadata.folder_structure
        
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:  # It's a file
                if 'files' not in current_level:
                    current_level['files'] = []
                current_level['files'].append({
                    'name': part,
                    'path': relative_path,
                    'size': metadata.files[-1].file_size if metadata.files else 0
                })
            else:  # It's a folder
                if 'folders' not in current_level:
                    current_level['folders'] = {}
                if part not in current_level['folders']:
                    current_level['folders'][part] = {}
                current_level = current_level['folders'][part]

    def finalize_folder_upload(self, folder_id: str, compression_level: CompressionLevel = CompressionLevel.BALANCED) -> Tuple[bool, str]:
        """Finalize folder upload and start processing"""
        try:
            if folder_id not in self.folder_metadata:
                return False, "Folder not found"
            
            metadata = self.folder_metadata[folder_id]
            
            if metadata.status != FolderStatus.UPLOADING:
                return False, "Folder is not in uploading state"
            
            # Update metadata
            metadata.status = FolderStatus.PROCESSING
            metadata.compression_level = compression_level
            metadata.total_files = len(metadata.files)
            
            self._save_metadata()
            
            # Start background processing
            threading.Thread(
                target=self._process_folder_async,
                args=(folder_id,),
                daemon=True
            ).start()
            
            return True, "Folder processing started"
            
        except Exception as e:
            return False, f"Error finalizing folder: {str(e)}"

    def _process_folder_async(self, folder_id: str):
        """Process folder in background (compression, optimization)"""
        try:
            metadata = self.folder_metadata[folder_id]
            folder_path = self.folders_path / folder_id
            
            # Create archive
            archive_path = self.archives_path / f"{folder_id}.zip"
            
            compression_map = {
                CompressionLevel.NONE: zipfile.ZIP_STORED,
                CompressionLevel.FAST: zipfile.ZIP_DEFLATED,
                CompressionLevel.BALANCED: zipfile.ZIP_DEFLATED,
                CompressionLevel.MAXIMUM: zipfile.ZIP_BZIP2
            }
            
            compression = compression_map[metadata.compression_level]
            compress_level = {
                CompressionLevel.NONE: 0,
                CompressionLevel.FAST: 1,
                CompressionLevel.BALANCED: 6,
                CompressionLevel.MAXIMUM: 9
            }[metadata.compression_level]
            
            with zipfile.ZipFile(archive_path, 'w', compression=compression, compresslevel=compress_level) as zipf:
                total_files = len(metadata.files)
                processed_files = 0
                
                for folder_file in metadata.files:
                    file_path = folder_path / folder_file.relative_path
                    if file_path.exists():
                        zipf.write(file_path, folder_file.relative_path)
                        processed_files += 1
                        metadata.processing_progress = (processed_files / total_files) * 100
                        self._save_metadata()
            
            # Calculate compression statistics
            original_size = metadata.total_size
            compressed_size = archive_path.stat().st_size
            
            metadata.compressed_size = compressed_size
            metadata.compression_ratio = (original_size - compressed_size) / original_size if original_size > 0 else 0
            metadata.status = FolderStatus.READY
            metadata.processing_progress = 100.0
            
            self._save_metadata()
            
        except Exception as e:
            # Mark as error
            if folder_id in self.folder_metadata:
                self.folder_metadata[folder_id].status = FolderStatus.ERROR
                self.folder_metadata[folder_id].error_message = str(e)
                self._save_metadata()

    def share_folder(self, folder_id: str, shared_by: str, shared_with: Optional[List[str]] = None,
                    message_id: Optional[str] = None, expires_days: int = 7) -> Tuple[bool, str]:
        """Share a folder with specific employees or broadcast"""
        try:
            if folder_id not in self.folder_metadata:
                return False, "Folder not found"
            
            metadata = self.folder_metadata[folder_id]
            
            if metadata.status != FolderStatus.READY:
                return False, "Folder is not ready for sharing"
            
            share_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(days=expires_days)
            
            folder_share = FolderShare(
                share_id=share_id,
                folder_id=folder_id,
                shared_by=shared_by,
                shared_with=shared_with,
                message_id=message_id,
                expires_at=expires_at
            )
            
            self.folder_shares[share_id] = folder_share
            self._save_shares()
            
            return True, share_id
            
        except Exception as e:
            return False, f"Error sharing folder: {str(e)}"

    def get_folder_info(self, folder_id: str) -> Optional[Dict]:
        """Get folder information"""
        if folder_id not in self.folder_metadata:
            return None
        
        metadata = self.folder_metadata[folder_id]
        
        return {
            'folder_id': folder_id,
            'folder_name': metadata.folder_name,
            'total_files': metadata.total_files,
            'total_size': metadata.total_size,
            'compressed_size': metadata.compressed_size,
            'compression_ratio': metadata.compression_ratio,
            'uploaded_by': metadata.uploaded_by,
            'upload_timestamp': metadata.upload_timestamp.isoformat(),
            'status': metadata.status.value,
            'processing_progress': metadata.processing_progress,
            'folder_structure': metadata.folder_structure,
            'download_count': metadata.download_count,
            'expires_at': metadata.expires_at.isoformat() if metadata.expires_at else None
        }

    def download_folder_archive(self, share_id: str, employee_id: str) -> Tuple[bool, Optional[Path], str]:
        """Download folder as ZIP archive"""
        try:
            if share_id not in self.folder_shares:
                return False, None, "Share not found"
            
            share = self.folder_shares[share_id]
            
            if not share.is_active:
                return False, None, "Share is inactive"
            
            if share.expires_at and datetime.now() > share.expires_at:
                return False, None, "Share has expired"
            
            if share.shared_with and employee_id not in share.shared_with:
                return False, None, "Access denied"
            
            folder_id = share.folder_id
            if folder_id not in self.folder_metadata:
                return False, None, "Folder not found"
            
            metadata = self.folder_metadata[folder_id]
            
            if metadata.status != FolderStatus.READY:
                return False, None, "Folder is not ready for download"
            
            archive_path = self.archives_path / f"{folder_id}.zip"
            
            if not archive_path.exists():
                return False, None, "Archive file not found"
            
            # Log access
            share.access_log.append({
                'employee_id': employee_id,
                'access_time': datetime.now().isoformat(),
                'action': 'download_archive'
            })
            
            metadata.download_count += 1
            metadata.last_accessed = datetime.now()
            
            self._save_shares()
            self._save_metadata()
            
            return True, archive_path, metadata.folder_name
            
        except Exception as e:
            return False, None, f"Error downloading folder: {str(e)}"

    def get_employee_shared_folders(self, employee_id: str) -> List[Dict]:
        """Get folders shared with an employee"""
        shared_folders = []
        
        for share_id, share in self.folder_shares.items():
            # Check if employee has access
            if share.shared_with is None or employee_id in share.shared_with:
                if share.is_active and (not share.expires_at or datetime.now() < share.expires_at):
                    folder_info = self.get_folder_info(share.folder_id)
                    if folder_info:
                        folder_info['share_id'] = share_id
                        folder_info['shared_by'] = share.shared_by
                        folder_info['message_id'] = share.message_id
                        shared_folders.append(folder_info)
        
        return shared_folders

    def _start_cleanup_thread(self):
        """Start background cleanup thread for expired folders"""
        def cleanup_expired():
            while True:
                try:
                    current_time = datetime.now()
                    expired_folders = []
                    
                    # Find expired folders
                    for folder_id, metadata in self.folder_metadata.items():
                        if metadata.expires_at and current_time > metadata.expires_at:
                            expired_folders.append(folder_id)
                    
                    # Clean up expired folders
                    for folder_id in expired_folders:
                        self._cleanup_folder(folder_id)
                    
                except Exception as e:
                    print(f"Error in cleanup thread: {e}")
                
                time.sleep(self.cleanup_interval)
        
        cleanup_thread = threading.Thread(target=cleanup_expired, daemon=True)
        cleanup_thread.start()

    def _cleanup_folder(self, folder_id: str):
        """Clean up an expired folder"""
        try:
            # Remove folder files
            folder_path = self.folders_path / folder_id
            if folder_path.exists():
                shutil.rmtree(folder_path)
            
            # Remove archive
            archive_path = self.archives_path / f"{folder_id}.zip"
            if archive_path.exists():
                archive_path.unlink()
            
            # Update metadata
            if folder_id in self.folder_metadata:
                self.folder_metadata[folder_id].status = FolderStatus.EXPIRED
            
            # Remove associated shares
            expired_shares = [
                share_id for share_id, share in self.folder_shares.items()
                if share.folder_id == folder_id
            ]
            
            for share_id in expired_shares:
                del self.folder_shares[share_id]
            
            self._save_metadata()
            self._save_shares()
            
        except Exception as e:
            print(f"Error cleaning up folder {folder_id}: {e}")

# Global instance
folder_manager = FolderSharingManager()
