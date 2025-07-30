#!/usr/bin/env python3
"""
Quick test to verify that HTML files can now be uploaded through the folder sharing system
"""

import requests
import tempfile
import os

def test_html_upload():
    """Test uploading an HTML file"""
    base_url = "https://localhost:5003"
    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Test HTML File</title>
</head>
<body>
    <h1>Hello World!</h1>
    <p>This is a test HTML file for the folder sharing system.</p>
</body>
</html>""")
        temp_file = f.name
    
    try:
        print("🧪 Testing HTML file upload...")
        
        # Step 1: Start folder upload session
        print("📁 Starting folder upload session...")
        response = requests.post(f"{base_url}/api/folder-sharing/start-upload", 
                               json={
                                   "folder_name": "test_html_upload",
                                   "uploaded_by": "test_user",
                                   "expected_files": 1
                               }, verify=False)
        
        if response.status_code != 200:
            print(f"❌ Failed to start upload session: {response.status_code}")
            print(response.text)
            return False
        
        folder_id = response.json()['folder_id']
        print(f"✅ Folder session created: {folder_id}")
        
        # Step 2: Upload HTML file
        print("📤 Uploading HTML file...")
        with open(temp_file, 'rb') as file_data:
            files = {'file': ('test.html', file_data, 'text/html')}
            response = requests.post(f"{base_url}/api/folder-sharing/upload-file/{folder_id}",
                                   files=files, verify=False)
        
        if response.status_code != 200:
            print(f"❌ Failed to upload HTML file: {response.status_code}")
            print(response.text)
            return False
        
        print("✅ HTML file uploaded successfully!")
        
        # Step 3: Finalize upload
        print("🏁 Finalizing upload...")
        response = requests.post(f"{base_url}/api/folder-sharing/finalize/{folder_id}",
                               json={"compression_level": "balanced"}, verify=False)
        
        if response.status_code != 200:
            print(f"❌ Failed to finalize upload: {response.status_code}")
            print(response.text)
            return False
        
        print("✅ Upload finalized successfully!")
        print("🎉 HTML file upload test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)

if __name__ == "__main__":
    print("🚀 Testing HTML file upload capability...")
    success = test_html_upload()
    if success:
        print("\n✅ HTML files are now supported for folder sharing!")
    else:
        print("\n❌ HTML file upload test failed.")
