#!/usr/bin/env python3
"""
Quick script to check admin user credentials
"""

from attendance.services.database import db

def main():
    try:
        admin_users = db.get_collection('admin_users')
        print("Admin users found:")
        for user in admin_users:
            print(f"Username: {user.get('username')}")
            print(f"Password: {user.get('password')}")
            print(f"Role: {user.get('role')}")
            print(f"Status: {user.get('status')}")
            print("---")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
