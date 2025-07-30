"""
Dashboard stats and activity helpers
"""
from datetime import date, datetime, timedelta
from ..services.database import db

def get_dashboard_stats():
    try:
        today = date.today()
        total_employees = db.count('employees', {'employment_status': 'active'})
        clocked_in_today = db.count('attendance_records', {'date': today.isoformat(), 'status': 'active'})
        completed_today = db.count('attendance_records', {'date': today.isoformat(), 'status': 'completed'})
        active_terminals = db.count('terminals', {'is_active': True})
        online_terminals = db.count('terminals', {'is_online': True})
        week_start = today - timedelta(days=today.weekday())
        week_records = db.get_attendance_records_by_date_range(week_start.isoformat(), today.isoformat())
        total_hours_week = sum(r.total_hours or 0 for r in week_records)
        overtime_hours_week = sum(r.overtime_hours or 0 for r in week_records)
        return {
            'total_employees': total_employees,
            'clocked_in_today': clocked_in_today,
            'present_today': clocked_in_today,
            'completed_today': completed_today,
            'late_today': 0,  # TODO: Calculate late employees
            'absent_today': max(0, total_employees - clocked_in_today),
            'active_terminals': active_terminals,
            'online_terminals': online_terminals,
            'total_hours_week': round(total_hours_week, 2),
            'overtime_hours_week': round(overtime_hours_week, 2),
            'date': today.isoformat()
        }
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {}

def get_today_activity():
    try:
        today = date.today()
        records = db.find('attendance_records', {'date': today.isoformat()})
        activity_list = []
        for record in records:
            employee = db.get_by_id('employees', record.employee_id)
            if not employee:
                continue
            ip_address = 'Unknown'
            if record.clock_in_time and not record.clock_out_time:
                action_type = "Clock In"
                action_icon = "sign-in-alt"
                action_color = "success"
                timestamp = record.clock_in_time
                ip_address = record.clock_in_ip or 'Unknown'
            elif record.clock_out_time:
                action_type = "Clock Out"
                action_icon = "sign-out-alt"
                action_color = "danger"
                timestamp = record.clock_out_time
                ip_address = record.clock_out_ip or 'Unknown'
            else:
                continue
            is_late = getattr(record, 'is_late', False)
            is_early = getattr(record, 'is_early', False)
            activity_list.append({
                'employee': {
                    'name': employee.full_name or f"{employee.first_name} {employee.last_name}",
                    'employee_id': employee.employee_id,
                    'photo': getattr(employee, 'photo_url', None)
                },
                'action_type': action_type,
                'action_icon': action_icon,
                'action_color': action_color,
                'timestamp': datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp,
                'ip_address': ip_address,
                'is_late': is_late,
                'is_early': is_early
            })
        activity_list.sort(key=lambda x: x['timestamp'], reverse=True)
        return activity_list[:20]
    except Exception as e:
        print(f"Error getting today's activity: {e}")
        return []
