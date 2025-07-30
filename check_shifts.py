#!/usr/bin/env python3
"""Check shifts in database"""

from attendance.services.database import db

try:
    shifts = db.get_all('shifts')
    print(f'Total shifts in database: {len(shifts)}')
    
    if shifts:
        for i, shift in enumerate(shifts[:5]):  # Show first 5
            print(f'{i+1}. ID: {shift.id}')
            print(f'   Name: {getattr(shift, "name", "N/A")}')
            print(f'   Type: {getattr(shift, "shift_type", "N/A")}')
            print(f'   Time: {getattr(shift, "start_time", "N/A")} - {getattr(shift, "end_time", "N/A")}')
            print(f'   Active: {getattr(shift, "is_active", "N/A")}')
            print(f'   All attributes: {[attr for attr in dir(shift) if not attr.startswith("_")]}')
            print('---')
    else:
        print('No shifts found in database')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
