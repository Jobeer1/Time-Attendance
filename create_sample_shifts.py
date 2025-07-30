#!/usr/bin/env python3
"""
Create sample shifts for the shift management system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from attendance.services.database import db
from attendance.models.shift import Shift
from datetime import datetime

def create_sample_shifts():
    """Create sample shifts"""
    try:
        # Check if shifts already exist
        existing_shifts = db.get_all('shifts')
        if existing_shifts:
            print(f"Found {len(existing_shifts)} existing shifts")
            for shift in existing_shifts:
                print(f"  - {shift.name}: {shift.start_time} - {shift.end_time}")
            return
        
        print("Creating sample shifts...")
        
        # Morning Shift
        morning_shift = Shift(
            name='Morning Shift',
            description='Standard morning work shift',
            start_time='06:00:00',
            end_time='14:00:00',
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            overtime_threshold=8.0,
            break_duration=30,
            late_grace_period=10,
            color='#e74c3c',
            is_active=True
        )
        
        # Day Shift
        day_shift = Shift(
            name='Day Shift',
            description='Standard day work shift',
            start_time='09:00:00',
            end_time='17:00:00',
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            overtime_threshold=8.0,
            break_duration=60,
            late_grace_period=15,
            color='#3498db',
            is_active=True
        )
        
        # Evening Shift
        evening_shift = Shift(
            name='Evening Shift',
            description='Standard evening work shift',
            start_time='14:00:00',
            end_time='22:00:00',
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            overtime_threshold=8.0,
            break_duration=30,
            late_grace_period=10,
            color='#f39c12',
            is_active=True
        )
        
        # Night Shift
        night_shift = Shift(
            name='Night Shift',
            description='Overnight work shift',
            start_time='22:00:00',
            end_time='06:00:00',
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            overtime_threshold=8.0,
            break_duration=45,
            late_grace_period=15,
            color='#9b59b6',
            is_active=True
        )
        
        # Weekend Shift
        weekend_shift = Shift(
            name='Weekend Shift',
            description='Weekend work shift',
            start_time='10:00:00',
            end_time='18:00:00',
            days_of_week=[5, 6],  # Saturday and Sunday
            overtime_threshold=8.0,
            break_duration=60,
            late_grace_period=20,
            color='#27ae60',
            is_active=True
        )
        
        # Create shifts in database
        shifts_to_create = [morning_shift, day_shift, evening_shift, night_shift, weekend_shift]
        
        for shift in shifts_to_create:
            created_shift = db.create('shifts', shift)
            print(f"Created shift: {created_shift.name} ({created_shift.id})")
        
        print(f"\n✅ Successfully created {len(shifts_to_create)} sample shifts!")
        
    except Exception as e:
        print(f"❌ Error creating sample shifts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_sample_shifts()
