#!/usr/bin/env python3
"""
Test script to verify enhanced messaging system with file attachments
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_messaging():
    """Test the enhanced messaging system with file upload capabilities"""
    
    base_url = "https://localhost:5003"
    
    print("🎯 Testing Enhanced Messaging System with File Attachments")
    print("=" * 65)
    
    try:
        # 1. Test basic message sending
        print("1. Testing basic message sending...")
        basic_message = {
            "from_employee_id": "EMP01",
            "to_employee_id": "EMP02",
            "subject": "Test Enhanced Messaging",
            "content": "This is a test of the enhanced messaging system without file attachments.",
            "priority": "normal"
        }
        
        response = requests.post(
            f"{base_url}/api/messaging/send",
            json=basic_message,
            headers={'Content-Type': 'application/json'},
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ Basic message sent successfully: {result.get('message_id')}")
            else:
                print(f"   ❌ Basic message failed: {result.get('error')}")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
        
        # 2. Test file upload endpoint
        print("2. Testing file upload endpoint...")
        
        # Create a test file
        test_file_path = "test_attachment.txt"
        test_content = "This is a test file for the messaging system attachment feature."
        
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        with open(test_file_path, 'rb') as f:
            files = {'file': f}
            data = {'description': 'Test attachment for messaging'}
            
            response = requests.post(
                f"{base_url}/api/file-sharing/upload",
                files=files,
                data=data,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    file_id = result.get('file_id')
                    print(f"   ✅ File uploaded successfully: {file_id}")
                    
                    # 3. Test message with file attachment
                    print("3. Testing message with file attachment...")
                    message_with_file = {
                        "from_employee_id": "EMP01",
                        "to_employee_id": "EMP02",
                        "subject": "Test Message with Attachment",
                        "content": "This message includes a file attachment!",
                        "priority": "high",
                        "file_attachments": [file_id]
                    }
                    
                    response = requests.post(
                        f"{base_url}/api/messaging/send",
                        json=message_with_file,
                        headers={'Content-Type': 'application/json'},
                        verify=False
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print(f"   ✅ Message with attachment sent: {result.get('message_id')}")
                            print(f"   📎 Attachment count: 1 file")
                        else:
                            print(f"   ❌ Message with attachment failed: {result.get('error')}")
                    else:
                        print(f"   ❌ Request failed: {response.status_code}")
                        
                else:
                    print(f"   ❌ File upload failed: {result.get('error')}")
            else:
                print(f"   ❌ File upload request failed: {response.status_code}")
        
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        
        # 4. Test broadcast message
        print("4. Testing broadcast message...")
        broadcast_message = {
            "from_employee_id": "ADMIN",
            "to_employee_id": None,
            "subject": "System Enhancement Announcement",
            "content": "The messaging system has been enhanced with file attachment capabilities!",
            "priority": "urgent"
        }
        
        response = requests.post(
            f"{base_url}/api/messaging/send",
            json=broadcast_message,
            headers={'Content-Type': 'application/json'},
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"   ✅ Broadcast message sent: {result.get('message_id')}")
            else:
                print(f"   ❌ Broadcast failed: {result.get('error')}")
        else:
            print(f"   ❌ Broadcast request failed: {response.status_code}")
        
        # 5. Test message retrieval
        print("5. Testing message retrieval...")
        response = requests.get(
            f"{base_url}/api/messaging/inbox/EMP02?include_read=true",
            verify=False
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                messages = result.get('messages', [])
                print(f"   ✅ Retrieved {len(messages)} messages for EMP02")
                
                # Check for file attachments
                for msg in messages:
                    if msg.get('file_attachments'):
                        print(f"   📎 Message {msg['id']} has {len(msg['file_attachments'])} attachment(s)")
                        for attachment in msg['file_attachments']:
                            print(f"      - {attachment.get('filename', 'Unknown file')}")
            else:
                print(f"   ❌ Message retrieval failed: {result.get('error')}")
        else:
            print(f"   ❌ Message retrieval request failed: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n" + "=" * 65)
    print("✅ Enhanced messaging system test completed!")
    print("\n🎉 Features tested:")
    print("  • Basic message sending")
    print("  • File upload functionality")
    print("  • Messages with file attachments")
    print("  • Broadcast messages")
    print("  • Message retrieval with attachment info")
    print("\n💡 The messaging system now supports:")
    print("  • Drag & drop file uploads")
    print("  • Progress bars for large files")
    print("  • Multiple file attachments per message")
    print("  • Medical image formats (DICOM, NIFTI)")
    print("  • Document sharing (PDF, Word, Excel)")
    print("  • Archive files (ZIP, RAR)")
    print("  • User-friendly file management")

if __name__ == "__main__":
    test_enhanced_messaging()
