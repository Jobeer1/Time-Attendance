#!/usr/bin/env python3
"""
Setup demo leave data for testing the terminal leave details functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.leave_management import LeaveManager, LeaveType, LeaveStatus, LeaveBalance
from datetime import datetime, timedelta
import json

def setup_demo_leave_data():
    """Setup demo leave data for employee DEMO001"""
    try:
        leave_manager = LeaveManager()
        
        print("🔧 Setting up demo leave data...")
        
        # Employee ID for demo
        employee_id = "DEMO001"
        
        # 1. Set up leave balances for the demo employee
        leave_balances = [
            LeaveBalance(
                employee_id=employee_id,
                leave_type=LeaveType.ANNUAL,
                available_days=18,  # 18 days remaining from 21 annual
                used_days=3,
                cycle_start_date=datetime(2024, 1, 1),
                cycle_end_date=datetime(2024, 12, 31),
                last_updated=datetime.now()
            ),
            LeaveBalance(
                employee_id=employee_id,
                leave_type=LeaveType.SICK,
                available_days=35,  # 35 days remaining from 36 sick
                used_days=1,
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
        
        # 2. Create some demo leave applications
        demo_applications = [
            {
                'leave_type': LeaveType.ANNUAL,
                'start_date': datetime.now() - timedelta(days=30),
                'end_date': datetime.now() - timedelta(days=28),
                'reason': 'Family vacation',
                'status': LeaveStatus.APPROVED
            },
            {
                'leave_type': LeaveType.SICK,
                'start_date': datetime.now() - timedelta(days=10),
                'end_date': datetime.now() - timedelta(days=10),
                'reason': 'Flu symptoms',
                'status': LeaveStatus.APPROVED
            },
            {
                'leave_type': LeaveType.ANNUAL,
                'start_date': datetime.now() + timedelta(days=15),
                'end_date': datetime.now() + timedelta(days=19),
                'reason': 'Holiday break',
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
                    application.comments = 'Demo approval'
                    print(f"✅ Created and approved leave application: {app_data['leave_type'].value}")
                elif app_data['status'] == LeaveStatus.REJECTED:
                    application.approved_by = 'admin'
                    application.approved_date = datetime.now()
                    application.rejection_reason = 'Demo rejection'
                    print(f"✅ Created and rejected leave application: {app_data['leave_type'].value}")
            else:
                print(f"✅ Created pending leave application: {app_data['leave_type'].value}")
        
        # 3. Save data to file for persistence
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Save balances
        balances_file = os.path.join(data_dir, 'leave_balances.json')
        balances_data = {}
        for emp_id, balances in leave_manager.leave_balances.items():
            balances_data[emp_id] = []
            for balance in balances:
                balances_data[emp_id].append({
                    'employee_id': balance.employee_id,
                    'leave_type': balance.leave_type.value,
                    'available_days': balance.available_days,
                    'used_days': balance.used_days,
                    'cycle_start_date': balance.cycle_start_date.isoformat(),
                    'cycle_end_date': balance.cycle_end_date.isoformat(),
                    'last_updated': balance.last_updated.isoformat()
                })
        
        with open(balances_file, 'w') as f:
            json.dump(balances_data, f, indent=2)
        
        # Save applications
        applications_file = os.path.join(data_dir, 'leave_applications.json')
        with open(applications_file, 'w') as f:
            # Convert applications to JSON-serializable format
            apps_data = {}
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
            json.dump(apps_data, f, indent=2)
        
        print(f"💾 Saved leave data to {data_dir}")
        
        # 4. Display summary
        print("\n📊 Demo Leave Data Summary:")
        print(f"Employee: {employee_id}")
        print(f"Total Applications: {len(demo_applications)}")
        print(f"Approved: {len([a for a in demo_applications if a['status'] == LeaveStatus.APPROVED])}")
        print(f"Pending: {len([a for a in demo_applications if a['status'] == LeaveStatus.PENDING])}")
        print(f"Rejected: {len([a for a in demo_applications if a['status'] == LeaveStatus.REJECTED])}")
        
        # Show current balances
        print(f"\n📋 Current Leave Balances:")
        for balance in leave_balances:
            print(f"  {balance.leave_type.value.replace('_', ' ').title()}: {balance.available_days} days available")
        
        print("\n✅ Demo leave data setup complete!")
        print("🚀 Now test the terminal login with employee DEMO001 to see leave details!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up demo leave data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    setup_demo_leave_data()
