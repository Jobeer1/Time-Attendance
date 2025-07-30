#!/usr/bin/env python3
"""
Create initial admin user for Time Attendance System
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from attendance.services.database import db
from attendance.models.admin import Admin
import hashlib
from datetime import datetime

def create_admin_user():
    """Create the initial admin user"""
    
    print("🔧 CREATING INITIAL ADMIN USER")
    print("=" * 40)
    
    try:
        # Check if admin users already exist
        existing_admins = db.get_all('admins')
        if existing_admins:
            print(f"ℹ Found {len(existing_admins)} existing admin user(s):")
            for admin in existing_admins:
                print(f"  - {admin.username} ({admin.role}) - {'Active' if admin.is_active else 'Inactive'}")
            
            response = input("\nCreate another admin user? (y/N): ").strip().lower()
            if response != 'y':
                print("Skipping admin creation.")
                return
        
        # Get admin details
        print("\nEnter admin user details:")
        username = input("Username: ").strip()
        if not username:
            print("❌ Username is required")
            return
            
        password = input("Password: ").strip()
        if not password or len(password) < 6:
            print("❌ Password must be at least 6 characters")
            return
            
        email = input("Email (optional): ").strip()
        full_name = input("Full Name (optional): ").strip()
        
        print("\nRole options:")
        print("1. admin - Standard administrator")
        print("2. super_admin - Super administrator (full access)")
        role_choice = input("Select role (1-2): ").strip()
        
        role = 'admin'
        if role_choice == '2':
            role = 'super_admin'
        
        # Create admin user
        admin_data = {
            'username': username,
            'email': email or '',
            'full_name': full_name or '',
            'password_hash': hashlib.sha256(password.encode()).hexdigest(),
            'role': role,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        admin = Admin(**admin_data)
        created_admin = db.create('admins', admin)
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"   Role: {role}")
        print(f"   Email: {email or 'Not provided'}")
        print(f"   Full Name: {full_name or 'Not provided'}")
        
        print(f"\n🌐 You can now login at: https://localhost:5002/admin")
        print(f"   Username: {username}")
        print(f"   Password: [the password you entered]")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin_user()
