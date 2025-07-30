#!/usr/bin/env python3

import sys
sys.path.append('.')

from attendance.services.database import DatabaseService
from datetime import date

def main():
    try:
        db = DatabaseService()
        
        print('Checking attendance records...')
        
        # Get all attendance records
        records = db.get_all('attendance_records')
        print(f'Total attendance records: {len(records)}')
        
        # Get today's date
        today = date.today().isoformat()
        print(f'Today is: {today}')
        
        # Get today's records
        today_records = [r for r in records if r.date == today]
        print(f'Today records: {len(today_records)}')
        
        # Get present employees (clocked in but not clocked out)
        present = [r for r in today_records if r.clock_in_time and not r.clock_out_time]
        print(f'Present employees: {len(present)}')
        
        if present:
            print('Present employees:')
            for r in present:
                print(f'- {r.employee_name} ({r.employee_id}) - clocked in at {r.clock_in_time}')
        else:
            print('No employees currently clocked in today.')
            
        # Check if we have any records at all for today
        if today_records:
            print('\nAll today records:')
            for r in today_records:
                status = 'Present' if (r.clock_in_time and not r.clock_out_time) else 'Completed'
                print(f'- {r.employee_name} ({r.employee_id}) - {status} - in: {r.clock_in_time}, out: {r.clock_out_time}')
                
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
