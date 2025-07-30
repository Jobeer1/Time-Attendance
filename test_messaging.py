#!/usr/bin/env python3
"""
Quick test for employee messaging system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from models.employee_messaging import EmployeeMessagingManager
    
    print("✅ Successfully imported EmployeeMessagingManager")
    
    # Test basic functionality
    manager = EmployeeMessagingManager()
    print("✅ Successfully created EmployeeMessagingManager instance")
    
    # Test sending a message
    message_id = manager.send_message("EMP01", "EMP02", "Test Subject", "Test message content")
    print(f"✅ Successfully sent message with ID: {message_id}")
    
    # Test getting messages
    messages = manager.get_employee_messages("EMP02")
    print(f"✅ Successfully retrieved {len(messages)} messages for EMP02")
    
    # Test broadcast
    broadcast_id = manager.broadcast_message("ADMIN", "Broadcast Test", "This is a test broadcast")
    print(f"✅ Successfully sent broadcast with ID: {broadcast_id}")
    
    print("\n🎉 All messaging tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
