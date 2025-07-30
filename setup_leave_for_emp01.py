#!/usr/bin/env python3
"""
Setup leave data for the actual employee who logged in (EMP01)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.leave_management import LeaveManager, LeaveType, LeaveStatus, LeaveBalance
from datetime import datetime, timedelta
import json

def setup_leave_for_emp01():
    """Setup demo leave data for employee EMP01"""
    try:
        leave_manager = LeaveManager()
        
        print("🔧 Setting up leave data for EMP01...")
        
        # Employee ID for the actual logged in user
        employee_id = "EMP01"
        
        # 1. Set up leave balances for EMP01
        leave_balances = [
            LeaveBalance(
                employee_id=employee_id,
                leave_type=LeaveType.ANNUAL,
                available_days=20,  # 20 days remaining from 21 annual
                used_days=1,
                cycle_start_date=datetime(2024, 1, 1),
                cycle_end_date=datetime(2024, 12, 31),
                last_updated=datetime.now()
            ),
            LeaveBalance(
                employee_id=employee_id,
                leave_type=LeaveType.SICK,
                available_days=36,  # 36 days remaining
                used_days=0,
                cycle_start_date=datetime(2024, 1, 1),
                cycle_end_date=datetime(2026, 12, 31),  # 3-year cycle
                last_updated=datetime.now()
            ),
            LeaveBalance(
                employee_id=employee_id,
                leave_type=LeaveType.FAMILY_RESPONSIBILITY,
                available_days=3,  # 3 days available
                used_days=0,
                cycle_start_date=datetime(2024, 1, 1),
                cycle_end_date=datetime(2024, 12, 31),
                last_updated=datetime.now()
            )
        ]
        
        # Save balances
        leave_manager.leave_balances[employee_id] = leave_balances
        print(f"✅ Set up leave balances for {employee_id}")
        
        # 2. Create some demo leave applications for EMP01
        demo_applications = [
            {
                'leave_type': LeaveType.ANNUAL,
                'start_date': datetime.now() - timedelta(days=20),
                'end_date': datetime.now() - timedelta(days=20),
                'reason': 'Personal day off',
                'status': LeaveStatus.APPROVED
            },
            {
                'leave_type': LeaveType.ANNUAL,
                'start_date': datetime.now() + timedelta(days=10),
                'end_date': datetime.now() + timedelta(days=12),
                'reason': 'Weekend getaway',
                'status': LeaveStatus.PENDING
            }
        ]
        
        # Apply for demo leave
        for app_data in demo_applications:
            app_id = leave_manager.apply_for_leave(
                employee_id=employee_id,
                leave_type=app_data['leave_type'],
                start_date=app_data['start_date'],
                end_date=app_data['end_date'],
                reason=app_data['reason']
            )
            
            # Update status if not pending
            if app_data['status'] != LeaveStatus.PENDING:
                application = leave_manager.leave_applications[app_id]
                application.status = app_data['status']
                if app_data['status'] == LeaveStatus.APPROVED:
                    application.approved_by = 'admin'
                    application.approved_date = datetime.now()
                    application.comments = 'Demo approval for EMP01'
                    print(f"✅ Created and approved leave application: {app_data['leave_type'].value}")
            else:
                print(f"✅ Created pending leave application: {app_data['leave_type'].value}")
        
        # 3. Load existing data and merge
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing balances if they exist
        balances_file = os.path.join(data_dir, 'leave_balances.json')
        existing_balances = {}
        if os.path.exists(balances_file):
            try:
                with open(balances_file, 'r') as f:
                    existing_balances = json.load(f)
            except:
                pass
        
        # Load existing applications if they exist
        applications_file = os.path.join(data_dir, 'leave_applications.json')
        existing_applications = {}
        if os.path.exists(applications_file):
            try:
                with open(applications_file, 'r') as f:
                    existing_applications = json.load(f)
            except:
                pass
        
        # Merge with existing data
        balances_data = existing_balances.copy()
        balances_data[employee_id] = []
        for balance in leave_balances:
            balances_data[employee_id].append({
                'employee_id': balance.employee_id,
                'leave_type': balance.leave_type.value,
                'available_days': balance.available_days,
                'used_days': balance.used_days,
                'cycle_start_date': balance.cycle_start_date.isoformat(),
                'cycle_end_date': balance.cycle_end_date.isoformat(),
                'last_updated': balance.last_updated.isoformat()
            })
        
        # Save balances
        with open(balances_file, 'w') as f:
            json.dump(balances_data, f, indent=2)
        
        # Merge applications
        apps_data = existing_applications.copy()
        for app_id, app in leave_manager.leave_applications.items():
            apps_data[app_id] = {
                'id': app.id,
                'employee_id': app.employee_id,
                'leave_type': app.leave_type.value,
                'start_date': app.start_date.isoformat(),
                'end_date': app.end_date.isoformat(),
                'days_requested': app.days_requested,
                'reason': app.reason,
                'status': app.status.value,
                'applied_date': app.applied_date.isoformat(),
                'approved_by': app.approved_by,
                'approved_date': app.approved_date.isoformat() if app.approved_date else None,
                'rejection_reason': app.rejection_reason,
                'proof_document': app.proof_document,
                'comments': app.comments
            }
        
        # Save applications
        with open(applications_file, 'w') as f:
            json.dump(apps_data, f, indent=2)
        
        print(f"💾 Saved leave data to {data_dir}")
        
        # 4. Display summary
        print(f"\n📊 Leave Data Summary for {employee_id}:")
        print(f"Total Applications: {len(demo_applications)}")
        print(f"Approved: {len([a for a in demo_applications if a['status'] == LeaveStatus.APPROVED])}")
        print(f"Pending: {len([a for a in demo_applications if a['status'] == LeaveStatus.PENDING])}")
        
        # Show current balances
        print(f"\n📋 Current Leave Balances for {employee_id}:")
        for balance in leave_balances:
            print(f"  {balance.leave_type.value.replace('_', ' ').title()}: {balance.available_days} days available")
        
        print(f"\n✅ Leave data setup complete for {employee_id}!")
        print("🚀 Now test the terminal login and clock in to see leave details!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up leave data for EMP01: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_leave_for_emp01()
