"""
Enterprise LAN Large File/Folder Sharing System
Optimized for multi-gigabyte files and folder sharing within corporate LAN
Complements medical imaging system with enterprise-focused features:
- Batch folder sharing for large datasets
- Multi-gigabyte file support (up to 50GB per file)
- LAN-optimized transfers with resume capability
- Network folder mounting for seamless integration
- Bulk operations for large file collections
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
import socket
import ipaddress

class LANFileType(Enum):
    """Enterprise file types for large file/folder sharing"""
    # Large Data Files
    DATABASE = "database"           # .db, .sql, .bak files
    BACKUP = "backup"              # .bak, .backup files
    VIRTUAL_MACHINE = "vm"         # .vmdk, .vdi, .qcow2
    ISO_IMAGE = "iso"              # .iso, .img files
    
    # Large Media Files
    RAW_VIDEO = "raw_video"        # .mov, .avi, .mkv (uncompressed)
    HIGH_RES_IMAGE = "hires_image" # .tiff, .raw, .dng (high resolution)
    AUDIO_MULTITRACK = "audio_pro" # .wav, .flac (professional audio)
    
    # Engineering/CAD Files
    CAD_ASSEMBLY = "cad_large"     # .asm, .prt, .catpart (large assemblies)
    POINT_CLOUD = "point_cloud"   # .las, .e57, .ply (3D scanning data)
    GIS_DATA = "gis"               # .shp, .geotiff (geographic data)
    
    # Software/Development
    BUILD_ARTIFACTS = "builds"     # Compiled software, installers
    SOURCE_REPOS = "repositories" # Git repos, source code collections
    CONTAINER_IMAGES = "containers" # Docker images, VMs
    
    # Archive Collections
    DATASET = "dataset"            # Research data, collections
    FOLDER_ARCHIVE = "folder"      # Entire folder structures
    COMPRESSED_LARGE = "archive"   # .7z, .rar, .tar.gz (multi-GB)
    
    # Document Collections
    DOCUMENT_BATCH = "doc_batch"   # Large document collections
    MULTIMEDIA_PROJECT = "project" # Video/audio project files
    
    OTHER = "other"                # Everything else

class LANAccessLevel(Enum):
    """Access levels for enterprise large file sharing"""
    DEPARTMENT_ONLY = "department"       # Only department members
    TEAM_PROJECT = "team_project"        # Project team members
    COMPANY_WIDE = "company"             # All company employees
    ENGINEERING_ONLY = "engineering"     # Engineering/technical teams
    MANAGEMENT_ONLY = "management"       # Management access only
    RESTRICTED = "restricted"            # Specific users only
    TEMPORARY_PROJECT = "temp_project"   # Time-limited project access
    EXTERNAL_SECURE = "external"         # Secure external sharing

@dataclass
class LANFileMetadata:
    """Enterprise large file metadata optimized for multi-gigabyte files"""
    file_id: str
    original_filename: str
    stored_filename: str
    file_size: int  # In bytes (supports up to 50GB+)
    file_type: LANFileType
    mime_type: str
    md5_hash: str
    upload_timestamp: datetime
    uploaded_by: str
    uploaded_by_name: str
    department: str
    project_name: Optional[str] = None  # For project-based organization
    access_level: LANAccessLevel = LANAccessLevel.DEPARTMENT_ONLY
    description: Optional[str] = None
    tags: List[str] = None
    is_confidential: bool = False
    is_folder_archive: bool = False  # True if this is a compressed folder
    original_folder_path: Optional[str] = None  # Original folder structure
    compression_ratio: Optional[float] = None  # If compressed
    chunk_count: int = 1  # For large file chunking
    resume_supported: bool = True  # For resumable downloads
    retention_days: int = 365  # Longer retention for enterprise files
    download_count: int = 0
    last_accessed: Optional[datetime] = None
    version: int = 1
    is_latest_version: bool = True
    parent_file_id: Optional[str] = None  # For versioning
    network_path: Optional[str] = None  # For network mounted access
    checksum_verified: bool = False  # Integrity verification
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @property
    def file_size_gb(self) -> float:
        """Get file size in GB"""
        return self.file_size / (1024 * 1024 * 1024)
    
    @property
    def is_large_file(self) -> bool:
        """Check if file is considered large (>1GB)"""
        return self.file_size > 1024 * 1024 * 1024

@dataclass
class LANFileShare:
    """Enterprise large file sharing record with advanced features"""
    share_id: str
    file_id: str
    shared_by: str
    shared_by_name: str
    shared_with_users: List[str] = None  # Specific employee IDs
    shared_with_departments: List[str] = None  # Department names
    shared_with_projects: List[str] = None  # Project teams
    expires_at: Optional[datetime] = None
    download_limit: Optional[int] = None
    bandwidth_limit_mbps: Optional[int] = None  # Bandwidth throttling
    require_approval: bool = False
    approval_status: str = "approved"  # pending, approved, rejected
    access_log: List[Dict] = None
    created_at: datetime = None
    is_active: bool = True
    share_message: Optional[str] = None
    lan_only: bool = True  # Force LAN-only access
    enable_resume: bool = True  # Enable resumable downloads
    enable_streaming: bool = False  # For large media files
    notification_sent: bool = False  # Track if users were notified
    
    def __post_init__(self):
        if self.shared_with_users is None:
            self.shared_with_users = []
        if self.shared_with_departments is None:
            self.shared_with_departments = []
        if self.shared_with_projects is None:
            self.shared_with_projects = []
        if self.access_log is None:
            self.access_log = []
        if self.created_at is None:
            self.created_at = datetime.now()

class LANNetworkValidator:
    """Validates that requests come from LAN IP addresses only"""
    
    def __init__(self):
        # Define common LAN IP ranges
        self.lan_networks = [
            ipaddress.IPv4Network('10.0.0.0/8'),      # Class A private
            ipaddress.IPv4Network('172.16.0.0/12'),   # Class B private
            ipaddress.IPv4Network('192.168.0.0/16'),  # Class C private
            ipaddress.IPv4Network('127.0.0.0/8'),     # Loopback
        ]
    
    def is_lan_ip(self, ip_address: str) -> bool:
        """Check if IP address is from LAN"""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            return any(ip in network for network in self.lan_networks)
        except (ipaddress.AddressValueError, ValueError):
            return False
    
    def validate_request_source(self, request_ip: str) -> bool:
        """Validate that request comes from LAN"""
        if not self.is_lan_ip(request_ip):
            return False
        return True

class LANFileManager:
    """Manages enterprise large file/folder sharing optimized for LAN networks"""
    
    def __init__(self, base_storage_path: str = "enterprise_lan_storage"):
        self.base_path = Path(base_storage_path)
        self.metadata_file = self.base_path / "enterprise_file_metadata.json"
        self.shares_file = self.base_path / "enterprise_file_shares.json"
        self.network_validator = LANNetworkValidator()
        
        # Create directories for enterprise storage
        self.base_path.mkdir(exist_ok=True)
        (self.base_path / "files").mkdir(exist_ok=True)
        (self.base_path / "temp").mkdir(exist_ok=True)
        (self.base_path / "chunks").mkdir(exist_ok=True)  # For large file chunking
        (self.base_path / "folders").mkdir(exist_ok=True)  # For folder archives
        (self.base_path / "network_mounts").mkdir(exist_ok=True)  # For network sharing
        
        # Initialize data files
        self._init_data_files()
        
        # File type mappings optimized for enterprise large files
        self.type_mappings = {
            # Database Files
            '.db': LANFileType.DATABASE,
            '.sql': LANFileType.DATABASE,
            '.bak': LANFileType.BACKUP,
            '.backup': LANFileType.BACKUP,
            
            # Virtual Machine Files
            '.vmdk': LANFileType.VIRTUAL_MACHINE,
            '.vdi': LANFileType.VIRTUAL_MACHINE,
            '.qcow2': LANFileType.VIRTUAL_MACHINE,
            '.vhd': LANFileType.VIRTUAL_MACHINE,
            
            # ISO Images
            '.iso': LANFileType.ISO_IMAGE,
            '.img': LANFileType.ISO_IMAGE,
            
            # Large Media Files (uncompressed/professional)
            '.mov': LANFileType.RAW_VIDEO,  # Often uncompressed
            '.avi': LANFileType.RAW_VIDEO,
            '.mkv': LANFileType.RAW_VIDEO,
            '.raw': LANFileType.HIGH_RES_IMAGE,
            '.dng': LANFileType.HIGH_RES_IMAGE,
            '.tiff': LANFileType.HIGH_RES_IMAGE,
            '.tif': LANFileType.HIGH_RES_IMAGE,
            '.wav': LANFileType.AUDIO_MULTITRACK,
            '.flac': LANFileType.AUDIO_MULTITRACK,
            
            # Engineering/CAD
            '.asm': LANFileType.CAD_ASSEMBLY,
            '.prt': LANFileType.CAD_ASSEMBLY,
            '.catpart': LANFileType.CAD_ASSEMBLY,
            '.sldprt': LANFileType.CAD_ASSEMBLY,
            '.las': LANFileType.POINT_CLOUD,
            '.e57': LANFileType.POINT_CLOUD,
            '.ply': LANFileType.POINT_CLOUD,
            '.shp': LANFileType.GIS_DATA,
            '.geotiff': LANFileType.GIS_DATA,
            
            # Software/Development
            '.tar': LANFileType.BUILD_ARTIFACTS,
            '.tar.gz': LANFileType.BUILD_ARTIFACTS,
            '.tar.xz': LANFileType.BUILD_ARTIFACTS,
            '.git': LANFileType.SOURCE_REPOS,
            
            # Large Archives
            '.7z': LANFileType.COMPRESSED_LARGE,
            '.rar': LANFileType.COMPRESSED_LARGE,
            '.zip': LANFileType.COMPRESSED_LARGE,  # If large
            
            # Project Files
            '.prproj': LANFileType.MULTIMEDIA_PROJECT,  # Premiere Pro
            '.aep': LANFileType.MULTIMEDIA_PROJECT,     # After Effects
            '.blend': LANFileType.MULTIMEDIA_PROJECT,   # Blender
        }
    
    def _init_data_files(self):
        """Initialize data files if they don't exist"""
        if not self.metadata_file.exists():
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)
        
        if not self.shares_file.exists():
            with open(self.shares_file, 'w') as f:
                json.dump({}, f)
    
    def _get_file_type(self, filename: str) -> LANFileType:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        return self.type_mappings.get(ext, LANFileType.OTHER)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def validate_lan_access(self, request_ip: str) -> bool:
        """Validate that request comes from LAN"""
        return self.network_validator.validate_request_source(request_ip)
    
    def upload_file(self, file_obj, uploaded_by: str, uploaded_by_name: str, 
                   department: str, access_level: LANAccessLevel = LANAccessLevel.DEPARTMENT_ONLY,
                   description: str = None, tags: List[str] = None,
                   is_confidential: bool = False) -> Tuple[bool, str, str]:
        """Upload a file to LAN storage"""
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Get file info
            original_filename = file_obj.filename
            file_size = 0
            
            # Save file temporarily to get size and hash
            temp_path = self.base_path / "temp" / f"{file_id}_{original_filename}"
            file_obj.save(temp_path)
            
            file_size = temp_path.stat().st_size
            file_hash = self._calculate_file_hash(temp_path)
            
            # Check for duplicates by hash
            metadata = self._load_metadata()
            for existing_id, existing_meta in metadata.items():
                if existing_meta.get('md5_hash') == file_hash:
                    # Remove temp file
                    temp_path.unlink()
                    return False, existing_id, "File already exists (duplicate detected)"
            
            # Determine file type
            file_type = self._get_file_type(original_filename)
            mime_type, _ = mimetypes.guess_type(original_filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Generate stored filename  
            stored_filename = f"{file_id}_{original_filename}"
            final_path = self.base_path / "files" / stored_filename
            
            # Move file to final location
            shutil.move(temp_path, final_path)
            
            # Create metadata
            file_metadata = LANFileMetadata(
                file_id=file_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                file_type=file_type,
                mime_type=mime_type,
                md5_hash=file_hash,
                upload_timestamp=datetime.now(),
                uploaded_by=uploaded_by,
                uploaded_by_name=uploaded_by_name,
                department=department,
                access_level=access_level,
                description=description,
                tags=tags or [],
                is_confidential=is_confidential
            )
            
            # Save metadata
            metadata[file_id] = asdict(file_metadata)
            self._save_metadata(metadata)
            
            return True, file_id, "File uploaded successfully"
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path and temp_path.exists():
                temp_path.unlink()
            return False, "", f"Upload failed: {str(e)}"
    
    def create_lan_share(self, file_id: str, shared_by: str, shared_by_name: str,
                        shared_with_users: List[str] = None,
                        shared_with_departments: List[str] = None,
                        expires_hours: int = 24,
                        download_limit: int = None,
                        share_message: str = None) -> Tuple[bool, str, str]:
        """Create a LAN-only file share"""
        try:
            # Verify file exists
            metadata = self._load_metadata()
            if file_id not in metadata:
                return False, "", "File not found"
            
            # Generate share ID
            share_id = str(uuid.uuid4())
            
            # Calculate expiration
            expires_at = datetime.now() + timedelta(hours=expires_hours) if expires_hours else None
            
            # Create share record
            share = LANFileShare(
                share_id=share_id,
                file_id=file_id,
                shared_by=shared_by,
                shared_by_name=shared_by_name,
                shared_with_users=shared_with_users or [],
                shared_with_departments=shared_with_departments or [],
                expires_at=expires_at,
                download_limit=download_limit,
                share_message=share_message,
                lan_only=True
            )
            
            # Save share
            shares = self._load_shares()
            shares[share_id] = asdict(share)
            self._save_shares(shares)
            
            return True, share_id, "LAN share created successfully"
            
        except Exception as e:
            return False, "", f"Share creation failed: {str(e)}"
    
    def get_file_for_download(self, share_id: str, requesting_user: str,
                             request_ip: str) -> Tuple[bool, Optional[Path], Optional[Dict], str]:
        """Get file for download with LAN validation"""
        try:
            # Validate LAN access
            if not self.validate_lan_access(request_ip):
                return False, None, None, "Access denied: Not from LAN network"
            
            # Get share info
            shares = self._load_shares()
            if share_id not in shares:
                return False, None, None, "Share not found"
            
            share_data = shares[share_id]
            share = LANFileShare(**share_data)
            
            # Check if share is active
            if not share.is_active:
                return False, None, None, "Share is no longer active"
            
            # Check expiration
            if share.expires_at and datetime.now() > share.expires_at:
                return False, None, None, "Share has expired"
            
            # Check download limit
            current_downloads = len(share.access_log)
            if share.download_limit and current_downloads >= share.download_limit:
                return False, None, None, "Download limit exceeded"
            
            # Check access permissions
            has_access = False
            
            # Check if user is specifically shared with
            if requesting_user in share.shared_with_users:
                has_access = True
            
            # Check department access
            if share.shared_with_departments:
                # Get user's department
                from attendance.models.employee import Employee
                employees = Employee.get_all_employees()
                user_dept = None
                for emp in employees:
                    if emp.employee_id == requesting_user:
                        user_dept = emp.department
                        break
                
                if user_dept and user_dept in share.shared_with_departments:
                    has_access = True
            
            # If no specific users/departments, check access level
            if not share.shared_with_users and not share.shared_with_departments:
                has_access = True  # Open to all LAN users
            
            if not has_access:
                return False, None, None, "Access denied: Insufficient permissions"
            
            # Get file metadata
            metadata = self._load_metadata()
            if share.file_id not in metadata:
                return False, None, None, "File not found"
            
            file_meta = metadata[share.file_id]
            file_path = self.base_path / "files" / file_meta['stored_filename']
            
            if not file_path.exists():
                return False, None, None, "File not found on disk"
            
            # Log access
            share.access_log.append({
                'user': requesting_user,
                'ip_address': request_ip,
                'timestamp': datetime.now().isoformat(),
                'action': 'download'
            })
            
            # Update download count
            metadata[share.file_id]['download_count'] += 1
            metadata[share.file_id]['last_accessed'] = datetime.now().isoformat()
            
            # Save updated data
            shares[share_id] = asdict(share)
            self._save_shares(shares)
            self._save_metadata(metadata)
            
            return True, file_path, file_meta, "Access granted"
            
        except Exception as e:
            return False, None, None, f"Download failed: {str(e)}"
    
    def list_lan_files(self, user_id: str, user_department: str) -> List[Dict]:
        """List files accessible to user on LAN"""
        try:
            metadata = self._load_metadata()
            shares = self._load_shares()
            accessible_files = []
            
            for file_id, file_meta in metadata.items():
                # Check if user has access based on access level
                access_level = LANAccessLevel(file_meta.get('access_level', 'department'))
                
                has_access = False
                
                if access_level == LANAccessLevel.COMPANY_WIDE:
                    has_access = True
                elif access_level == LANAccessLevel.DEPARTMENT_ONLY:
                    if file_meta.get('department') == user_department:
                        has_access = True
                elif access_level == LANAccessLevel.RESTRICTED:
                    # Check if there are active shares for this user
                    for share_id, share_data in shares.items():
                        share = LANFileShare(**share_data)
                        if (share.file_id == file_id and share.is_active and
                            (user_id in share.shared_with_users or 
                             user_department in share.shared_with_departments)):
                            has_access = True
                            break
                
                if has_access:
                    file_info = {
                        'file_id': file_id,
                        'filename': file_meta['original_filename'],
                        'file_size': file_meta['file_size'],
                        'file_type': file_meta['file_type'],
                        'uploaded_by': file_meta['uploaded_by_name'],
                        'upload_date': file_meta['upload_timestamp'],
                        'description': file_meta.get('description'),
                        'tags': file_meta.get('tags', []),
                        'download_count': file_meta.get('download_count', 0),
                        'is_confidential': file_meta.get('is_confidential', False)
                    }
                    accessible_files.append(file_info)
            
            return accessible_files
            
        except Exception as e:
            return []
    
    def _load_metadata(self) -> Dict:
        """Load file metadata"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_metadata(self, metadata: Dict):
        """Save file metadata"""
        # Convert datetime objects to strings
        for file_id, file_meta in metadata.items():
            if isinstance(file_meta.get('upload_timestamp'), datetime):
                file_meta['upload_timestamp'] = file_meta['upload_timestamp'].isoformat()
            if isinstance(file_meta.get('last_accessed'), datetime):
                file_meta['last_accessed'] = file_meta['last_accessed'].isoformat()
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def _load_shares(self) -> Dict:
        """Load file shares"""
        try:
            with open(self.shares_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_shares(self, shares: Dict):
        """Save file shares"""
        # Convert datetime objects to strings
        for share_id, share_data in shares.items():
            if isinstance(share_data.get('expires_at'), datetime):
                share_data['expires_at'] = share_data['expires_at'].isoformat()
            if isinstance(share_data.get('created_at'), datetime):
                share_data['created_at'] = share_data['created_at'].isoformat()
        
        with open(self.shares_file, 'w') as f:
            json.dump(shares, f, indent=2, default=str)

# Global LAN file manager instance
lan_file_manager = LANFileManager()
