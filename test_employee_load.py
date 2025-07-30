#!/usr/bin/env python3
"""Test script to check employee loading"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from attendance.services.database import DatabaseService
import traceback

try:
    db_service = DatabaseService()
    employees = db_service.get_all_employees()
    print(f'Found {len(employees)} employees:')
    for emp in employees[:5]:  # Show first 5
        print(f'  - {emp.employee_id}: {emp.first_name} {emp.last_name} ({emp.department})')
        print(f'    Status: {emp.employment_status}')
        print(f'    Email: {emp.email}')
        print('---')
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()
