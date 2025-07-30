# filepath: attendance/models/leave_request.py
"""
Leave Request model for HR leave management
"""
from .base import BaseModel

class LeaveRequest(BaseModel):
    """Leave request model"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.employee_id = kwargs.get('employee_id', '')
        self.start_date = kwargs.get('start_date', '')
        self.end_date = kwargs.get('end_date', '')
        self.leave_type = kwargs.get('leave_type', '')  # vacation, sick, etc.
        self.status = kwargs.get('status', 'pending')  # pending, approved, rejected
        self.reason = kwargs.get('reason', '')
        self.approved_by = kwargs.get('approved_by', '')

    def validate(self) -> bool:
        """Validate required leave request fields"""
        return bool(self.employee_id and self.start_date and self.end_date and self.leave_type)

class LeaveManager:
    def get_all_applications(self):
        """Fetch all leave applications from the database"""
        # This is a placeholder implementation. Replace with actual database query.
        return [
            LeaveRequest(
                id="LA20250713120944P001",
                employee_id="EMP001",
                leave_type="Good Will Paid Leave",
                start_date="2025-07-14",
                end_date="2025-07-15",
                status="rejected",
                reason="personal reasons",
                approved_by="admin",
                rejection_reason="apply for paternity leave"
            ),
            LeaveRequest(
                id="LA20250713122502P001",
                employee_id="EMP002",
                leave_type="Annual Leave",
                start_date="2025-07-20",
                end_date="2025-07-25",
                status="approved",
                reason="family vacation",
                approved_by="admin"
            )
        ]