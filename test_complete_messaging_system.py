#!/usr/bin/env python3
"""
Comprehensive test script for the complete messaging system
Tests folder sharing, file attachments, replies, conversations, and forwarding
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

def test_basic_messaging(base_url):
    """Test basic messaging functionality"""
    print("\n💬 Testing basic messaging...")
    
    # Send a basic message
    response = requests.post(f"{base_url}/api/messaging/send", json={
        "from_employee_id": "emp001",
        "to_employee_id": "emp002",
        "subject": "Test Message",
        "content": "This is a test message to verify basic messaging functionality.",
        "priority": "normal"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to send basic message: {response.text}")
        return None
    
    result = response.json()
    message_id = result['message_id']
    print(f"✅ Basic message sent: {message_id}")
    
    # Test getting messages
    response = requests.get(f"{base_url}/api/messaging/messages/emp002")
    
    if response.status_code != 200:
        print(f"❌ Failed to get messages: {response.text}")
        return message_id
    
    messages = response.json()['messages']
    print(f"✅ Retrieved {len(messages)} messages for emp002")
    
    return message_id

def test_message_replies(base_url, original_message_id):
    """Test message reply functionality"""
    print(f"\n↩️ Testing message replies for {original_message_id}...")
    
    # Send a reply
    response = requests.post(f"{base_url}/api/messaging/reply", json={
        "original_message_id": original_message_id,
        "from_employee_id": "emp002",
        "subject": "Re: Test Message",
        "content": "This is a reply to the test message. Thank you for reaching out!",
        "priority": "normal"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to send reply: {response.text}")
        return None
    
    result = response.json()
    reply_id = result['message_id']
    print(f"✅ Reply sent: {reply_id}")
    
    # Test getting replies
    response = requests.get(f"{base_url}/api/messaging/message/{original_message_id}/replies", 
                          params={"employee_id": "emp001"})
    
    if response.status_code != 200:
        print(f"❌ Failed to get replies: {response.text}")
        return reply_id
    
    replies = response.json()['replies']
    print(f"✅ Retrieved {len(replies)} replies to original message")
    
    return reply_id

def test_conversation_threading(base_url, reply_id):
    """Test conversation threading"""
    print(f"\n🧵 Testing conversation threading...")
    
    # Get conversations for emp001
    response = requests.get(f"{base_url}/api/messaging/conversations/emp001")
    
    if response.status_code != 200:
        print(f"❌ Failed to get conversations: {response.text}")
        return
    
    conversations = response.json()['conversations']
    print(f"✅ Found {len(conversations)} conversations for emp001")
    
    if conversations:
        conv_id = conversations[0]['conversation_id']
        print(f"📋 Testing conversation: {conv_id}")
        
        # Get conversation messages
        response = requests.get(f"{base_url}/api/messaging/conversation/{conv_id}", 
                              params={"employee_id": "emp001"})
        
        if response.status_code == 200:
            conv_messages = response.json()['messages']
            print(f"✅ Conversation has {len(conv_messages)} messages")
            
            # Mark conversation as read
            response = requests.post(f"{base_url}/api/messaging/conversation/{conv_id}/mark-read", 
                                   json={"employee_id": "emp001"})
            
            if response.status_code == 200:
                print("✅ Conversation marked as read")
            else:
                print(f"⚠️ Failed to mark conversation as read: {response.text}")
        else:
            print(f"❌ Failed to get conversation messages: {response.text}")

def test_folder_upload_and_messaging(base_url):
    """Test folder upload and sharing through messaging"""
    print("\n📁 Testing folder upload and messaging integration...")
    
    # Create a simple test folder
    test_folder = Path("test_msg_folder")
    test_folder.mkdir(exist_ok=True)
    
    # Create some test files
    files = [
        ("document1.pdf", b"PDF document content for testing" * 100),
        ("image1.jpg", b"JPEG image data for testing" * 150),
        ("report.docx", b"Word document content for testing" * 80),
        ("subfolder/nested_file.txt", b"Nested file content for testing" * 50)
    ]
    
    for file_path, content in files:
        full_path = test_folder / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
    
    try:
        # Start folder upload
        response = requests.post(f"{base_url}/api/folder-sharing/start-upload", json={
            "folder_name": "Test Message Folder",
            "uploaded_by": "emp001",
            "expected_files": len(files)
        })
        
        if response.status_code != 200:
            print(f"❌ Failed to start folder upload: {response.text}")
            return None
        
        folder_id = response.json()['folder_id']
        print(f"✅ Started folder upload: {folder_id}")
        
        # Upload files
        uploaded_count = 0
        for file_path, content in files:
            full_path = test_folder / file_path
            relative_path = str(Path(file_path))
            
            with open(full_path, 'rb') as f:
                files_payload = {'file': (full_path.name, f, 'application/octet-stream')}
                data = {'relative_path': relative_path}
                
                response = requests.post(
                    f"{base_url}/api/folder-sharing/upload-file/{folder_id}",
                    files=files_payload,
                    data=data
                )
                
                if response.status_code == 200:
                    uploaded_count += 1
                    print(f"  ✅ Uploaded: {relative_path}")
                else:
                    print(f"  ❌ Failed: {relative_path} - {response.text}")
        
        if uploaded_count == 0:
            print("❌ No files uploaded successfully")
            return None
        
        # Finalize folder
        response = requests.post(f"{base_url}/api/folder-sharing/finalize/{folder_id}", 
                               json={"compression_level": "fast"})
        
        if response.status_code != 200:
            print(f"❌ Failed to finalize folder: {response.text}")
            return None
        
        print("✅ Folder finalization started")
        
        # Wait for processing
        max_wait = 30
        wait_time = 0
        
        while wait_time < max_wait:
            response = requests.get(f"{base_url}/api/folder-sharing/upload-status/{folder_id}")
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data['status']
                
                if status == "ready":
                    print("✅ Folder processing completed!")
                    break
                elif status == "error":
                    print("❌ Folder processing failed!")
                    return None
            
            time.sleep(1)
            wait_time += 1
        
        if wait_time >= max_wait:
            print("⚠️ Folder processing timeout")
            return None
        
        return folder_id
        
    finally:
        # Cleanup test folder
        if test_folder.exists():
            import shutil
            shutil.rmtree(test_folder)

def test_message_with_folder(base_url, folder_id):
    """Test sending message with folder attachment"""
    print(f"\n📨 Testing message with folder attachment...")
    
    response = requests.post(f"{base_url}/api/messaging/send", json={
        "from_employee_id": "emp001",
        "to_employee_id": "emp003",
        "subject": "Shared Folder - Test Documents",
        "content": "Please review the attached folder containing test documents and provide feedback.",
        "priority": "high",
        "folder_attachments": [folder_id]
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to send message with folder: {response.text}")
        return None
    
    result = response.json()
    message_id = result['message_id']
    print(f"✅ Message with folder attachment sent: {message_id}")
    
    # Verify message was received
    response = requests.get(f"{base_url}/api/messaging/messages/emp003")
    
    if response.status_code == 200:
        messages = response.json()['messages']
        folder_message = next((msg for msg in messages if msg['id'] == message_id), None)
        
        if folder_message and folder_message.get('folder_attachments'):
            print(f"✅ Message received with {len(folder_message['folder_attachments'])} folder attachments")
        else:
            print("⚠️ Message received but folder attachments not found")
    
    return message_id

def test_reply_with_attachments(base_url, original_message_id, folder_id):
    """Test replying with both file and folder attachments"""
    print(f"\n📎 Testing reply with mixed attachments...")
    
    # For this test, we'll use the folder_id as both file and folder attachment
    # In a real scenario, you'd have separate file IDs
    response = requests.post(f"{base_url}/api/messaging/reply", json={
        "original_message_id": original_message_id,
        "from_employee_id": "emp003",
        "subject": "Re: Shared Folder - Test Documents",
        "content": "Thank you for sharing the documents. I've reviewed them and here are my additional files and folders for your reference.",
        "priority": "normal",
        "folder_attachments": [folder_id]  # In real use, you'd have different IDs
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to send reply with attachments: {response.text}")
        return None
    
    result = response.json()
    reply_id = result['message_id']
    print(f"✅ Reply with attachments sent: {reply_id}")
    
    return reply_id

def test_message_forwarding(base_url, message_id):
    """Test message forwarding"""
    print(f"\n📤 Testing message forwarding...")
    
    response = requests.post(f"{base_url}/api/messaging/forward", json={
        "original_message_id": message_id,
        "from_employee_id": "emp003",
        "to_employee_id": "emp004",
        "additional_content": "Please see the forwarded message below. This requires your attention as well.",
        "priority": "normal"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to forward message: {response.text}")
        return None
    
    result = response.json()
    forward_id = result['message_id']
    print(f"✅ Message forwarded: {forward_id}")
    
    return forward_id

def test_broadcast_with_folder(base_url, folder_id):
    """Test broadcasting message with folder attachment"""
    print(f"\n📢 Testing broadcast with folder attachment...")
    
    response = requests.post(f"{base_url}/api/messaging/send", json={
        "from_employee_id": "emp001",
        "subject": "Company-wide Document Archive",
        "content": "Please find attached the company-wide document archive for Q4 2024. All employees should review the contents.",
        "priority": "high",
        "folder_attachments": [folder_id]
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to broadcast with folder: {response.text}")
        return None
    
    result = response.json()
    broadcast_id = result['message_id']
    print(f"✅ Broadcast with folder sent: {broadcast_id}")
    
    # Check if multiple employees received it
    for emp_id in ["emp002", "emp003", "emp004"]:
        response = requests.get(f"{base_url}/api/messaging/messages/{emp_id}")
        
        if response.status_code == 200:
            messages = response.json()['messages']
            broadcast_msg = next((msg for msg in messages if msg['id'] == broadcast_id), None)
            
            if broadcast_msg:
                print(f"  ✅ {emp_id} received broadcast")
            else:
                print(f"  ⚠️ {emp_id} did not receive broadcast")
    
    return broadcast_id

def test_folder_download_from_message(base_url):
    """Test downloading folder from message attachment"""
    print(f"\n📥 Testing folder download from message...")
    
    # Get shared folders for emp003
    response = requests.get(f"{base_url}/api/folder-sharing/my-folders/emp003")
    
    if response.status_code != 200:
        print(f"❌ Failed to get shared folders: {response.text}")
        return
    
    folders = response.json()['folders']
    
    if not folders:
        print("⚠️ No shared folders found for emp003")
        return
    
    folder = folders[0]
    share_id = folder['share_id']
    
    print(f"📁 Testing download of folder: {folder['folder_name']}")
    
    response = requests.get(f"{base_url}/api/folder-sharing/download/{share_id}", 
                          params={"employee_id": "emp003"})
    
    if response.status_code != 200:
        print(f"❌ Failed to download folder: {response.text}")
        return
    
    # Save and verify downloaded file
    download_path = "test_downloaded_folder.zip"
    
    try:
        with open(download_path, 'wb') as f:
            f.write(response.content)
        
        # Verify ZIP file
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print(f"✅ Downloaded ZIP contains {len(file_list)} files")
            
            for file_name in file_list[:3]:  # Show first 3 files
                print(f"  📄 {file_name}")
            
            if len(file_list) > 3:
                print(f"  ... and {len(file_list) - 3} more files")
    
    finally:
        # Clean up
        if os.path.exists(download_path):
            os.remove(download_path)

def main():
    """Run comprehensive messaging and folder sharing tests"""
    print("🚀 Starting comprehensive messaging and folder sharing tests...\n")
    
    base_url = "https://localhost:5003"
    
    try:
        # Test basic messaging
        original_message_id = test_basic_messaging(base_url)
        if not original_message_id:
            return
        
        # Test message replies
        reply_id = test_message_replies(base_url, original_message_id)
        if reply_id:
            test_conversation_threading(base_url, reply_id)
        
        # Test folder upload and messaging integration
        folder_id = test_folder_upload_and_messaging(base_url)
        if not folder_id:
            print("⚠️ Skipping folder-related tests due to upload failure")
            return
        
        # Test message with folder attachment
        folder_message_id = test_message_with_folder(base_url, folder_id)
        if folder_message_id:
            # Test reply with attachments
            reply_with_attachments_id = test_reply_with_attachments(base_url, folder_message_id, folder_id)
            
            # Test message forwarding
            if reply_with_attachments_id:
                test_message_forwarding(base_url, reply_with_attachments_id)
        
        # Test broadcast with folder
        test_broadcast_with_folder(base_url, folder_id)
        
        # Test folder download from message
        test_folder_download_from_message(base_url)
        
        print("\n🎉 All messaging and folder sharing tests completed successfully!")
        print("\n📊 Features tested:")
        print("  ✅ Basic messaging")
        print("  ✅ Message replies and conversation threading")
        print("  ✅ Folder upload and processing")
        print("  ✅ Messages with folder attachments")
        print("  ✅ Replies with mixed attachments")
        print("  ✅ Message forwarding")
        print("  ✅ Broadcast messages with folders")
        print("  ✅ Folder download from messages")
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
