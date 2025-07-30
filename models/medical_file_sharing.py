"""
Large File Sharing System for Medical Images (DICOM)
Specialized for CT scans, MRIs, and other large medical imaging files
"""

import os
import hashlib
import mimetypes
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from pathlib import Path
import zipfile
import tempfile

class FileType(Enum):
    """Supported file types for medical imaging"""
    DICOM = "dicom"              # .dcm, .dicom files
    NIFTI = "nifti"              # .nii, .nii.gz files  
    TIFF = "tiff"                # .tif, .tiff files
    PNG = "png"                  # .png files
    JPEG = "jpeg"                # .jpg, .jpeg files
    PDF = "pdf"                  # .pdf files
    ZIP = "zip"                  # .zip archives
    RAR = "rar"                  # .rar archives
    GENERIC = "generic"          # Other files

class FileCategory(Enum):
    """Medical file categories"""
    CT_SCAN = "ct_scan"
    MRI_SCAN = "mri_scan"
    XRAY = "xray"
    ULTRASOUND = "ultrasound"
    MAMMOGRAPHY = "mammography"
    PET_SCAN = "pet_scan"
    NUCLEAR_MEDICINE = "nuclear_medicine"
    PATHOLOGY = "pathology"
    REPORT = "report"
    OTHER = "other"

@dataclass
class FileMetadata:
    """Medical file metadata"""
    file_id: str
    original_filename: str
    stored_filename: str
    file_size: int
    file_type: FileType
    file_category: FileCategory
    mime_type: str
    md5_hash: str
    upload_timestamp: datetime
    uploaded_by: str
    patient_id: Optional[str] = None
    study_date: Optional[str] = None
    modality: Optional[str] = None
    study_description: Optional[str] = None
    series_description: Optional[str] = None
    institution_name: Optional[str] = None
    is_compressed: bool = False
    compression_ratio: Optional[float] = None
    access_level: str = "restricted"  # public, internal, restricted, confidential
    retention_days: int = 365
    virus_scan_status: str = "pending"  # pending, clean, infected, error
    download_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class FileShare:
    """File sharing record"""
    share_id: str
    file_id: str
    shared_by: str
    shared_with: Optional[str] = None  # None for public shares
    message_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    download_limit: Optional[int] = None
    password_protected: bool = False
    access_log: List[Dict] = None
    created_at: datetime = None
    is_active: bool = True

    def __post_init__(self):
        if self.access_log is None:
            self.access_log = []
        if self.created_at is None:
            self.created_at = datetime.now()

class MedicalFileManager:
    """Manages large medical file uploads, storage, and sharing"""
    
    def __init__(self, base_storage_path: str = "file_storage"):
        self.base_path = Path(base_storage_path)
        self.metadata_file = self.base_path / "file_metadata.json"
        self.shares_file = self.base_path / "file_shares.json"
        
        # Create directory structure
        self.uploads_path = self.base_path / "uploads"
        self.temp_path = self.base_path / "temp"
        self.compressed_path = self.base_path / "compressed"
        
        for path in [self.uploads_path, self.temp_path, self.compressed_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self.file_metadata: Dict[str, FileMetadata] = self._load_metadata()
        self.file_shares: Dict[str, FileShare] = self._load_shares()
        
        # File type mappings
        self.file_type_mappings = {
            '.dcm': FileType.DICOM,
            '.dicom': FileType.DICOM,
            '.nii': FileType.NIFTI,
            '.nii.gz': FileType.NIFTI,
            '.tif': FileType.TIFF,
            '.tiff': FileType.TIFF,
            '.png': FileType.PNG,
            '.jpg': FileType.JPEG,
            '.jpeg': FileType.JPEG,
            '.pdf': FileType.PDF,
            '.zip': FileType.ZIP,
            '.rar': FileType.RAR
        }
        
        # Maximum file sizes (in bytes)
        self.max_file_sizes = {
            FileType.DICOM: 2 * 1024 * 1024 * 1024,  # 2GB for DICOM
            FileType.NIFTI: 1 * 1024 * 1024 * 1024,  # 1GB for NIFTI
            FileType.ZIP: 5 * 1024 * 1024 * 1024,    # 5GB for ZIP archives
            FileType.GENERIC: 500 * 1024 * 1024      # 500MB for other files
        }

    def _validate_and_repair_metadata(self):
        """Validate and repair the file metadata JSON file."""
        default_data = {}

        # Check if the file exists
        if not self.metadata_file.exists():
            print(f"[WARNING] File metadata not found. Creating a new one at: {self.metadata_file}")
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data

        # Validate the JSON structure
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure: Expected a dictionary.")
                return data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Corrupted file metadata: {e}")
            print(f"[INFO] Repairing the file metadata at: {self.metadata_file}")
            
            # Debugging: Log the corrupted data
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    corrupted_data = f.read()
                print(f"[DEBUG] Corrupted metadata content: {corrupted_data}")
            except Exception as debug_e:
                print(f"[DEBUG] Failed to read corrupted metadata: {debug_e}")
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data

    def _load_metadata(self) -> Dict[str, FileMetadata]:
        """Load file metadata from JSON"""
        data = self._validate_and_repair_metadata()

        metadata = {}
        for file_id, meta_dict in data.items():
            # Convert datetime strings back to datetime objects
            meta_dict['upload_timestamp'] = datetime.fromisoformat(meta_dict['upload_timestamp'])
            if meta_dict.get('last_accessed'):
                meta_dict['last_accessed'] = datetime.fromisoformat(meta_dict['last_accessed'])

            # Convert enums
            meta_dict['file_type'] = FileType(meta_dict['file_type'])
            meta_dict['file_category'] = FileCategory(meta_dict['file_category'])

            metadata[file_id] = FileMetadata(**meta_dict)

        return metadata
            
    def _save_metadata(self):
        """Save file metadata to JSON"""
        try:
            data = {}
            for file_id, metadata in self.file_metadata.items():
                meta_dict = asdict(metadata)
                # Convert datetime objects to strings
                meta_dict['upload_timestamp'] = metadata.upload_timestamp.isoformat()
                if metadata.last_accessed:
                    meta_dict['last_accessed'] = metadata.last_accessed.isoformat()
                
                # Convert enums to strings
                meta_dict['file_type'] = metadata.file_type.value
                meta_dict['file_category'] = metadata.file_category.value
                
                data[file_id] = meta_dict
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[ERROR] Failed to save file metadata: {e}")

    def _validate_and_repair_shares(self):
        """Validate and repair the file shares JSON file."""
        default_data = {}

        # Check if the file exists
        if not self.shares_file.exists():
            print(f"[WARNING] File shares not found. Creating a new one at: {self.shares_file}")
            with open(self.shares_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data

        # Validate the JSON structure
        try:
            with open(self.shares_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure: Expected a dictionary.")
                return data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Corrupted file shares: {e}")
            print(f"[INFO] Repairing the file shares at: {self.shares_file}")
            with open(self.shares_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            return default_data

    def _load_shares(self) -> Dict[str, FileShare]:
        """Load file shares from JSON"""
        data = self._validate_and_repair_shares()

        shares = {}
        for share_id, share_dict in data.items():
            # Convert datetime strings back to datetime objects
            if share_dict.get('created_at'):
                share_dict['created_at'] = datetime.fromisoformat(share_dict['created_at'])
            if share_dict.get('expires_at'):
                share_dict['expires_at'] = datetime.fromisoformat(share_dict['expires_at'])

            # Convert access log timestamps
            if share_dict.get('access_log'):
                for log_entry in share_dict['access_log']:
                    if 'timestamp' in log_entry:
                        log_entry['timestamp'] = datetime.fromisoformat(log_entry['timestamp'])

            shares[share_id] = FileShare(**share_dict)

        return shares
            
    def _save_shares(self):
        """Save file shares to JSON"""
        try:
            data = {}
            for share_id, share in self.file_shares.items():
                share_dict = asdict(share)
                
                # Convert datetime objects to strings
                if share.created_at:
                    share_dict['created_at'] = share.created_at.isoformat()
                if share.expires_at:
                    share_dict['expires_at'] = share.expires_at.isoformat()
                
                # Convert access log timestamps
                if share.access_log:
                    for log_entry in share_dict['access_log']:
                        if 'timestamp' in log_entry and isinstance(log_entry['timestamp'], datetime):
                            log_entry['timestamp'] = log_entry['timestamp'].isoformat()
                
                data[share_id] = share_dict
            
            with open(self.shares_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[ERROR] Failed to save file shares: {e}")

    def _get_file_type(self, filename: str) -> FileType:
        """Determine file type from filename"""
        filename_lower = filename.lower()
        
        # Check for compound extensions first (.nii.gz)
        if filename_lower.endswith('.nii.gz'):
            return FileType.NIFTI
        
        # Check single extensions
        ext = Path(filename).suffix.lower()
        return self.file_type_mappings.get(ext, FileType.GENERIC)

    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _compress_file(self, source_path: Path, target_path: Path) -> Tuple[bool, float]:
        """Compress file using ZIP compression"""
        try:
            original_size = source_path.stat().st_size
            
            with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                zipf.write(source_path, source_path.name)
            
            compressed_size = target_path.stat().st_size
            compression_ratio = (original_size - compressed_size) / original_size
            
            return True, compression_ratio
            
        except Exception as e:
            print(f"[ERROR] Failed to compress file: {e}")
            return False, 0.0

    def upload_file(self, file_path: str, uploaded_by: str, 
                   file_category: FileCategory = FileCategory.OTHER,
                   patient_id: Optional[str] = None,
                   study_description: Optional[str] = None,
                   compress_large_files: bool = True,
                   access_level: str = "restricted") -> Tuple[bool, str, str]:
        """
        Upload a large medical file
        
        Returns: (success, file_id, message)
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False, "", "File not found"
            
            # Check file size
            file_size = source_path.stat().st_size
            file_type = self._get_file_type(source_path.name)
            
            max_size = self.max_file_sizes.get(file_type, self.max_file_sizes[FileType.GENERIC])
            if file_size > max_size:
                return False, "", f"File too large. Maximum size: {max_size / (1024*1024):.0f}MB"
            
            # Generate unique file ID
            file_id = f"FILE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Determine storage filename
            file_extension = ''.join(source_path.suffixes)
            stored_filename = f"{file_id}{file_extension}"
            target_path = self.uploads_path / stored_filename
            
            # Copy file to storage
            shutil.copy2(source_path, target_path)
            
            # Calculate hash
            md5_hash = self._calculate_md5(target_path)
            
            # Check for compression
            is_compressed = False
            compression_ratio = None
            
            if compress_large_files and file_size > 100 * 1024 * 1024:  # 100MB threshold
                compressed_path = self.compressed_path / f"{file_id}.zip"
                success, ratio = self._compress_file(target_path, compressed_path)
                
                if success and ratio > 0.1:  # Only use compression if >10% reduction
                    # Use compressed version
                    target_path.unlink()  # Remove uncompressed
                    target_path = compressed_path
                    stored_filename = f"{file_id}.zip"
                    is_compressed = True
                    compression_ratio = ratio
                    file_size = compressed_path.stat().st_size
                else:
                    # Remove failed compression
                    if compressed_path.exists():
                        compressed_path.unlink()
            
            # Get MIME type
            mime_type = mimetypes.guess_type(source_path.name)[0] or 'application/octet-stream'
            
            # Create metadata
            metadata = FileMetadata(
                file_id=file_id,
                original_filename=source_path.name,
                stored_filename=stored_filename,
                file_size=file_size,
                file_type=file_type,
                file_category=file_category,
                mime_type=mime_type,
                md5_hash=md5_hash,
                upload_timestamp=datetime.now(),
                uploaded_by=uploaded_by,
                patient_id=patient_id,
                study_description=study_description,
                is_compressed=is_compressed,
                compression_ratio=compression_ratio,
                access_level=access_level
            )
            
            # Store metadata
            self.file_metadata[file_id] = metadata
            self._save_metadata()
            
            print(f"[INFO] File uploaded successfully: {file_id}")
            return True, file_id, f"File uploaded successfully. Size: {file_size / (1024*1024):.1f}MB"
            
        except Exception as e:
            print(f"[ERROR] File upload failed: {e}")
            return False, "", f"Upload failed: {str(e)}"

    def create_file_share(self, file_id: str, shared_by: str,
                         shared_with: Optional[str] = None,
                         message_id: Optional[str] = None,
                         expires_hours: Optional[int] = None,
                         download_limit: Optional[int] = None,
                         password_protected: bool = False) -> Tuple[bool, str, str]:
        """
        Create a file share link
        
        Returns: (success, share_id, message)
        """
        try:
            if file_id not in self.file_metadata:
                return False, "", "File not found"
            
            # Generate share ID
            share_id = f"SHARE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Calculate expiration
            expires_at = None
            if expires_hours:
                expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            # Create share record
            share = FileShare(
                share_id=share_id,
                file_id=file_id,
                shared_by=shared_by,
                shared_with=shared_with,
                message_id=message_id,
                expires_at=expires_at,
                download_limit=download_limit,
                password_protected=password_protected
            )
            
            # Store share
            self.file_shares[share_id] = share
            self._save_shares()
            
            print(f"[INFO] File share created: {share_id}")
            return True, share_id, "File share created successfully"
            
        except Exception as e:
            print(f"[ERROR] Failed to create file share: {e}")
            return False, "", f"Share creation failed: {str(e)}"

    def get_file_info(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata"""
        return self.file_metadata.get(file_id)

    def get_share_info(self, share_id: str) -> Optional[FileShare]:
        """Get share information"""
        share = self.file_shares.get(share_id)
        
        # Check if share is still valid
        if share and share.is_active:
            if share.expires_at and datetime.now() > share.expires_at:
                share.is_active = False
                self._save_shares()
                return None
            
            if share.download_limit and len(share.access_log) >= share.download_limit:
                share.is_active = False
                self._save_shares()
                return None
        
        return share if share and share.is_active else None

    def download_file(self, share_id: str, accessed_by: str, 
                     user_ip: str = "unknown") -> Tuple[bool, str, str]:
        """
        Get file path for download
        
        Returns: (success, file_path, message)
        """
        try:
            share = self.get_share_info(share_id)
            if not share:
                return False, "", "Invalid or expired share link"
            
            # Check permissions
            if share.shared_with and share.shared_with != accessed_by:
                return False, "", "Access denied"
            
            # Get file metadata
            metadata = self.file_metadata.get(share.file_id)
            if not metadata:
                return False, "", "File not found"
            
            # Update access log
            share.access_log.append({
                'timestamp': datetime.now(),
                'accessed_by': accessed_by,
                'user_ip': user_ip
            })
            
            # Update download count
            metadata.download_count += 1
            metadata.last_accessed = datetime.now()
            
            # Save updates
            self._save_shares()
            self._save_metadata()
            
            # Determine file path
            if metadata.is_compressed:
                file_path = str(self.compressed_path / metadata.stored_filename)
            else:
                file_path = str(self.uploads_path / metadata.stored_filename)
            
            print(f"[INFO] File download initiated: {share_id} by {accessed_by}")
            return True, file_path, "Download authorized"
            
        except Exception as e:
            print(f"[ERROR] Download failed: {e}")
            return False, "", f"Download failed: {str(e)}"

    def get_user_files(self, user_id: str) -> List[FileMetadata]:
        """Get all files uploaded by a user"""
        return [metadata for metadata in self.file_metadata.values() 
                if metadata.uploaded_by == user_id]

    def get_shared_files(self, user_id: str) -> List[Tuple[FileMetadata, FileShare]]:
        """Get all files shared with a user"""
        shared_files = []
        
        for share in self.file_shares.values():
            if not share.is_active:
                continue
            
            # Check if shared with this user or public
            if share.shared_with is None or share.shared_with == user_id:
                if share.file_id in self.file_metadata:
                    metadata = self.file_metadata[share.file_id]
                    shared_files.append((metadata, share))
        
        return shared_files

    def delete_file(self, file_id: str, deleted_by: str) -> Tuple[bool, str]:
        """Delete a file and all its shares"""
        try:
            if file_id not in self.file_metadata:
                return False, "File not found"
            
            metadata = self.file_metadata[file_id]
            
            # Check permissions (only uploader or admin can delete)
            if metadata.uploaded_by != deleted_by and deleted_by != "ADMIN":
                return False, "Access denied"
            
            # Delete physical file
            if metadata.is_compressed:
                file_path = self.compressed_path / metadata.stored_filename
            else:
                file_path = self.uploads_path / metadata.stored_filename
            
            if file_path.exists():
                file_path.unlink()
            
            # Remove metadata
            del self.file_metadata[file_id]
            
            # Remove all shares for this file
            shares_to_remove = [share_id for share_id, share in self.file_shares.items() 
                               if share.file_id == file_id]
            
            for share_id in shares_to_remove:
                del self.file_shares[share_id]
            
            # Save changes
            self._save_metadata()
            self._save_shares()
            
            print(f"[INFO] File deleted: {file_id} by {deleted_by}")
            return True, "File deleted successfully"
            
        except Exception as e:
            print(f"[ERROR] File deletion failed: {e}")
            return False, f"Deletion failed: {str(e)}"

    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            total_files = len(self.file_metadata)
            total_size = sum(metadata.file_size for metadata in self.file_metadata.values())
            total_downloads = sum(metadata.download_count for metadata in self.file_metadata.values())
            
            # File type breakdown
            type_counts = {}
            for metadata in self.file_metadata.values():
                file_type = metadata.file_type.value
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            # Category breakdown
            category_counts = {}
            for metadata in self.file_metadata.values():
                category = metadata.file_category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            return {
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_downloads': total_downloads,
                'active_shares': len([s for s in self.file_shares.values() if s.is_active]),
                'file_types': type_counts,
                'file_categories': category_counts,
                'storage_path': str(self.base_path.absolute())
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to get storage stats: {e}")
            return {}

# Global file manager instance
file_manager = MedicalFileManager()
