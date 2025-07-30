#!/usr/bin/env python3

import sys
sys.path.append('.')

from attendance.services.database import DatabaseService

def main():
    try:
        db = DatabaseService()
        employee = db.get_employee_by_employee_id('EMP01')
        
        if employee:
            print('Employee found!')
            print('Employee data:')
            for key, value in employee.__dict__.items():
                if not key.startswith('_'):
                    print(f'  {key}: {value}')
        else:
            print('Employee not found')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    main()
