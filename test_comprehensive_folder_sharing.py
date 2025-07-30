#!/usr/bin/env python3
"""
Comprehensive test script for large folder sharing functionality
Tests folder upload, processing, sharing, and messaging integration
"""

import sys
import os
import requests
import json
import time
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_folder_structure():
    """Create a comprehensive test folder structure"""
    base_dir = Path("test_large_folder")
    
    # Remove existing test folder
    if base_dir.exists():
        import shutil
        shutil.rmtree(base_dir)
    
    # Create complex folder structure
    folders = [
        "medical_scans/ct_scans/patient_001",
        "medical_scans/ct_scans/patient_002", 
        "medical_scans/mri_scans/brain",
        "medical_scans/mri_scans/spine",
        "medical_scans/xray/chest",
        "medical_scans/xray/orthopedic",
        "reports/radiology",
        "reports/pathology",
        "documents/policies",
        "documents/procedures",
        "training_materials/videos",
        "training_materials/presentations"
    ]
    
    files = [
        # CT Scans
        ("medical_scans/ct_scans/patient_001/scan_001.dcm", b"DICOM CT scan data for patient 001 scan 001" * 100),
        ("medical_scans/ct_scans/patient_001/scan_002.dcm", b"DICOM CT scan data for patient 001 scan 002" * 120),
        ("medical_scans/ct_scans/patient_001/report.pdf", b"PDF report for CT scan patient 001" * 50),
        ("medical_scans/ct_scans/patient_002/scan_001.dcm", b"DICOM CT scan data for patient 002 scan 001" * 110),
        ("medical_scans/ct_scans/patient_002/scan_002.dcm", b"DICOM CT scan data for patient 002 scan 002" * 130),
        
        # MRI Scans
        ("medical_scans/mri_scans/brain/brain_001.nii", b"NIFTI brain MRI scan data 001" * 200),
        ("medical_scans/mri_scans/brain/brain_002.nii", b"NIFTI brain MRI scan data 002" * 180),
        ("medical_scans/mri_scans/spine/spine_001.nii", b"NIFTI spine MRI scan data 001" * 150),
        ("medical_scans/mri_scans/spine/spine_002.nii", b"NIFTI spine MRI scan data 002" * 170),
        
        # X-rays
        ("medical_scans/xray/chest/chest_001.tiff", b"TIFF chest X-ray image 001" * 80),
        ("medical_scans/xray/chest/chest_002.tiff", b"TIFF chest X-ray image 002" * 90),
        ("medical_scans/xray/orthopedic/bone_001.tiff", b"TIFF orthopedic X-ray 001" * 75),
        ("medical_scans/xray/orthopedic/bone_002.tiff", b"TIFF orthopedic X-ray 002" * 85),
        
        # Reports
        ("reports/radiology/report_001.pdf", b"Radiology report 001 content" * 30),
        ("reports/radiology/report_002.pdf", b"Radiology report 002 content" * 35),
        ("reports/pathology/pathology_001.pdf", b"Pathology report 001 content" * 25),
        ("reports/pathology/pathology_002.pdf", b"Pathology report 002 content" * 28),
        
        # Documents
        ("documents/policies/imaging_policy.docx", b"Medical imaging policy document" * 20),
        ("documents/policies/privacy_policy.docx", b"Patient privacy policy document" * 22),
        ("documents/procedures/ct_procedure.docx", b"CT scan procedure documentation" * 18),
        ("documents/procedures/mri_procedure.docx", b"MRI scan procedure documentation" * 19),
        
        # Training Materials
        ("training_materials/presentations/ct_training.pdf", b"CT scan training presentation" * 40),
        ("training_materials/presentations/mri_training.pdf", b"MRI scan training presentation" * 45),
        ("training_materials/videos/safety_video.txt", b"Safety training video placeholder" * 10),
        
        # Root files
        ("README.md", b"# Medical Imaging Archive\\n\\nThis folder contains medical imaging data and related documentation."),
        ("manifest.json", b'{"version": "1.0", "type": "medical_archive", "created": "' + datetime.now().isoformat().encode() + b'"}')
    ]
    
    # Create directories
    for folder in folders:
        folder_path = base_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
    
    # Create files
    for file_path, content in files:
        full_path = base_dir / file_path
        full_path.write_bytes(content)
    
    print(f"✅ Created test folder structure with {len(files)} files in {len(folders)} folders")
    return base_dir

def test_folder_upload_session(base_url, folder_path):
    """Test creating and using a folder upload session"""
    print("\n🔄 Testing folder upload session...")
    
    # Start folder upload session
    response = requests.post(f"{base_url}/api/folder-sharing/start-upload", json={
        "folder_name": "Medical Imaging Archive",
        "uploaded_by": "emp001",
        "expected_files": len(list(folder_path.rglob("*"))) if folder_path.exists() else 25
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to start upload session: {response.text}")
        return None
    
    result = response.json()
    folder_id = result['folder_id']
    print(f"✅ Created folder upload session: {folder_id}")
    
    return folder_id

def test_file_uploads(base_url, folder_id, folder_path):
    """Test uploading files to the folder"""
    print(f"\n📤 Testing file uploads to folder {folder_id}...")
    
    uploaded_count = 0
    failed_count = 0
    
    # Upload all files in the folder
    for file_path in folder_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(folder_path)
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {'relative_path': str(relative_path)}
                
                response = requests.post(
                    f"{base_url}/api/folder-sharing/upload-file/{folder_id}",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    uploaded_count += 1
                    print(f"  ✅ Uploaded: {relative_path}")
                else:
                    failed_count += 1
                    print(f"  ❌ Failed: {relative_path} - {response.text}")
    
    print(f"\n📊 Upload Summary: {uploaded_count} successful, {failed_count} failed")
    return uploaded_count > 0

def test_folder_finalization(base_url, folder_id):
    """Test finalizing the folder upload"""
    print(f"\n🏁 Testing folder finalization for {folder_id}...")
    
    response = requests.post(f"{base_url}/api/folder-sharing/finalize/{folder_id}", json={
        "compression_level": "balanced"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to finalize folder: {response.text}")
        return False
    
    print("✅ Folder finalization started")
    return True

def test_processing_status(base_url, folder_id):
    """Test monitoring folder processing status"""
    print(f"\n⏳ Monitoring processing status for {folder_id}...")
    
    max_wait = 60  # Maximum wait time in seconds
    wait_time = 0
    
    while wait_time < max_wait:
        response = requests.get(f"{base_url}/api/folder-sharing/upload-status/{folder_id}")
        
        if response.status_code != 200:
            print(f"❌ Failed to get status: {response.text}")
            return False
        
        status_data = response.json()
        status = status_data['status']
        progress = status_data['processing_progress']
        
        print(f"  📊 Status: {status}, Progress: {progress:.1f}%")
        
        if status == "ready":
            print("✅ Folder processing completed!")
            return True
        elif status == "error":
            print("❌ Folder processing failed!")
            return False
        
        time.sleep(2)
        wait_time += 2
    
    print("⚠️ Folder processing timeout")
    return False

def test_folder_sharing(base_url, folder_id):
    """Test sharing the folder"""
    print(f"\n🤝 Testing folder sharing for {folder_id}...")
    
    response = requests.post(f"{base_url}/api/folder-sharing/share", json={
        "folder_id": folder_id,
        "shared_by": "emp001",
        "shared_with": ["emp002", "emp003"],  # Share with specific employees
        "expires_days": 7
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to share folder: {response.text}")
        return None
    
    result = response.json()
    share_id = result['share_id']
    print(f"✅ Folder shared successfully: {share_id}")
    
    return share_id

def test_folder_info(base_url, folder_id):
    """Test getting folder information"""
    print(f"\n📋 Testing folder info retrieval for {folder_id}...")
    
    response = requests.get(f"{base_url}/api/folder-sharing/info/{folder_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get folder info: {response.text}")
        return False
    
    folder_info = response.json()['folder']
    
    print(f"✅ Folder Info:")
    print(f"  📁 Name: {folder_info['folder_name']}")
    print(f"  📊 Files: {folder_info['total_files']}")
    print(f"  💾 Size: {folder_info['total_size'] / (1024*1024):.1f} MB")
    if folder_info['compressed_size']:
        print(f"  🗜️ Compressed: {folder_info['compressed_size'] / (1024*1024):.1f} MB")
        print(f"  📉 Compression Ratio: {folder_info['compression_ratio']*100:.1f}%")
    print(f"  📅 Uploaded: {folder_info['upload_timestamp']}")
    print(f"  🔄 Status: {folder_info['status']}")
    
    return True

def test_folder_structure(base_url, folder_id):
    """Test getting folder structure"""
    print(f"\n🌳 Testing folder structure retrieval for {folder_id}...")
    
    response = requests.get(f"{base_url}/api/folder-sharing/folder-structure/{folder_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get folder structure: {response.text}")
        return False
    
    structure_data = response.json()
    structure = structure_data['structure']
    
    def print_structure(structure, level=0):
        indent = "  " * level
        
        # Print folders
        if 'folders' in structure:
            for folder_name, folder_content in structure['folders'].items():
                print(f"{indent}📁 {folder_name}/")
                print_structure(folder_content, level + 1)
        
        # Print files
        if 'files' in structure:
            for file_info in structure['files']:
                size_mb = file_info['size'] / (1024*1024)
                print(f"{indent}📄 {file_info['name']} ({size_mb:.2f} MB)")
    
    print("✅ Folder Structure:")
    print_structure(structure)
    
    return True

def test_employee_folder_access(base_url):
    """Test employee access to shared folders"""
    print(f"\n👤 Testing employee folder access...")
    
    response = requests.get(f"{base_url}/api/folder-sharing/my-folders/emp002")
    
    if response.status_code != 200:
        print(f"❌ Failed to get employee folders: {response.text}")
        return False
    
    folders = response.json()['folders']
    
    print(f"✅ Employee emp002 has access to {len(folders)} folders:")
    for folder in folders:
        print(f"  📁 {folder['folder_name']} - {folder['total_files']} files")
        print(f"     Shared by: {folder['shared_by']}")
        print(f"     Size: {folder['total_size'] / (1024*1024):.1f} MB")
    
    return len(folders) > 0

def test_folder_download(base_url, share_id):
    """Test downloading folder as archive"""
    print(f"\n📥 Testing folder download for share {share_id}...")
    
    response = requests.get(f"{base_url}/api/folder-sharing/download/{share_id}", 
                          params={"employee_id": "emp002"})
    
    if response.status_code != 200:
        print(f"❌ Failed to download folder: {response.text}")
        return False
    
    # Save downloaded file
    download_path = "downloaded_folder.zip"
    with open(download_path, 'wb') as f:
        f.write(response.content)
    
    # Verify ZIP file
    try:
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"✅ Downloaded ZIP contains {len(file_list)} files")
            
            # Show some files
            for file_name in file_list[:5]:
                print(f"  📄 {file_name}")
            if len(file_list) > 5:
                print(f"  ... and {len(file_list) - 5} more files")
    
        # Clean up
        os.remove(download_path)
        return True
        
    except Exception as e:
        print(f"❌ Invalid ZIP file: {e}")
        return False

def test_messaging_integration(base_url, folder_id):
    """Test integration with messaging system"""
    print(f"\n💬 Testing messaging integration for folder {folder_id}...")
    
    # Send message with folder attachment
    response = requests.post(f"{base_url}/api/messaging/send", json={
        "from_employee_id": "emp001",
        "to_employee_id": "emp002",
        "subject": "Medical Imaging Archive",
        "content": "Please review the attached medical imaging archive for the recent cases.",
        "priority": "high",
        "folder_attachments": [folder_id]
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to send message with folder: {response.text}")
        return False
    
    print("✅ Message with folder attachment sent successfully")
    return True

def main():
    """Run comprehensive folder sharing tests"""
    print("🚀 Starting comprehensive folder sharing tests...\n")
    
    base_url = "http://localhost:5003"
    
    # Create test folder structure
    folder_path = create_test_folder_structure()
    
    try:
        # Test folder upload session
        folder_id = test_folder_upload_session(base_url, folder_path)
        if not folder_id:
            return
        
        # Test file uploads
        if not test_file_uploads(base_url, folder_id, folder_path):
            return
        
        # Test folder finalization
        if not test_folder_finalization(base_url, folder_id):
            return
        
        # Monitor processing status
        if not test_processing_status(base_url, folder_id):
            return
        
        # Test folder info
        test_folder_info(base_url, folder_id)
        
        # Test folder structure
        test_folder_structure(base_url, folder_id)
        
        # Test folder sharing
        share_id = test_folder_sharing(base_url, folder_id)
        if not share_id:
            return
        
        # Test employee access
        test_employee_folder_access(base_url)
        
        # Test folder download
        test_folder_download(base_url, share_id)
        
        # Test messaging integration
        test_messaging_integration(base_url, folder_id)
        
        print("\n🎉 All folder sharing tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup test folder
        if folder_path.exists():
            import shutil
            shutil.rmtree(folder_path)
            print(f"\n🧹 Cleaned up test folder: {folder_path}")

if __name__ == "__main__":
    main()
