"""
Leave Management Models for South African BCEA Compliance
Basic Conditions of Employment Act (BCEA) compliant leave system
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
import os

class LeaveType(Enum):
    """South African BCEA Leave Types"""
    ANNUAL = "annual"
    SICK = "sick"
    FAMILY_RESPONSIBILITY = "family_responsibility"
    MATERNITY = "maternity"
    PARENTAL = "parental"
    ADOPTION = "adoption"
    COMMISSIONING_PARENTAL = "commissioning_parental"
    UNPAID = "unpaid"
    GOOD_WILL_PAID = "good_will_paid"

class LeaveStatus(Enum):
    """Leave Application Status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

@dataclass
class LeaveTypeConfig:
    """Configuration for each leave type"""
    name: str
    description: str
    is_paid: bool
    max_days_per_cycle: int
    cycle_months: int  # Length of cycle in months
    requires_proof: bool
    proof_required_after_days: int
    min_employment_months: int  # Minimum employment period to qualify
    notes: str

class LeaveEntitlements:
    """BCEA Leave Entitlements Configuration"""
    
    LEAVE_TYPES = {
        LeaveType.ANNUAL: LeaveTypeConfig(
            name="Annual Leave",
            description="Paid vacation leave as per BCEA",
            is_paid=True,
            max_days_per_cycle=15,  # 15 working days for 5-day week
            cycle_months=12,
            requires_proof=False,
            proof_required_after_days=0,
            min_employment_months=0,
            notes="21 consecutive days (15 working days for 5-day week). Accrues at 1.25 days per month."
        ),
        LeaveType.SICK: LeaveTypeConfig(
            name="Sick Leave",
            description="Paid sick leave as per BCEA",
            is_paid=True,
            max_days_per_cycle=30,  # 30 working days over 3-year cycle
            cycle_months=36,
            requires_proof=True,
            proof_required_after_days=2,
            min_employment_months=0,
            notes="30 working days over 3-year cycle. Medical certificate required after 2+ consecutive days."
        ),
        LeaveType.FAMILY_RESPONSIBILITY: LeaveTypeConfig(
            name="Family Responsibility Leave",
            description="Paid family responsibility leave as per BCEA",
            is_paid=True,
            max_days_per_cycle=3,
            cycle_months=12,
            requires_proof=True,
            proof_required_after_days=0,
            min_employment_months=4,
            notes="3 days paid per annual cycle. For birth, illness, or death in family. Must work 4+ days per week."
        ),
        LeaveType.MATERNITY: LeaveTypeConfig(
            name="Maternity Leave",
            description="Unpaid maternity leave as per BCEA",
            is_paid=False,
            max_days_per_cycle=120,  # 4 months
            cycle_months=12,
            requires_proof=True,
            proof_required_after_days=0,
            min_employment_months=0,
            notes="4 consecutive months unpaid. UIF benefits available. Cannot return within 6 weeks without medical clearance."
        ),
        LeaveType.PARENTAL: LeaveTypeConfig(
            name="Parental Leave",
            description="Unpaid parental leave as per BCEA",
            is_paid=False,
            max_days_per_cycle=10,
            cycle_months=12,
            requires_proof=True,
            proof_required_after_days=0,
            min_employment_months=0,
            notes="10 consecutive days unpaid. UIF benefits available. For fathers or adoptive parents."
        ),
        LeaveType.ADOPTION: LeaveTypeConfig(
            name="Adoption Leave",
            description="Unpaid adoption leave as per BCEA",
            is_paid=False,
            max_days_per_cycle=70,  # 10 weeks
            cycle_months=12,
            requires_proof=True,
            proof_required_after_days=0,
            min_employment_months=0,
            notes="10 consecutive weeks unpaid for adopting child under 2. UIF benefits available."
        ),
        LeaveType.COMMISSIONING_PARENTAL: LeaveTypeConfig(
            name="Commissioning Parental Leave",
            description="Unpaid commissioning parental leave as per BCEA",
            is_paid=False,
            max_days_per_cycle=70,  # 10 weeks
            cycle_months=12,
            requires_proof=True,
            proof_required_after_days=0,
            min_employment_months=0,
            notes="10 consecutive weeks unpaid for surrogate motherhood. UIF benefits available."
        ),
        LeaveType.UNPAID: LeaveTypeConfig(
            name="Unpaid Leave",
            description="Additional unpaid leave at employer discretion",
            is_paid=False,
            max_days_per_cycle=365,  # No specific limit
            cycle_months=12,
            requires_proof=False,
            proof_required_after_days=0,
            min_employment_months=0,
            notes="Discretionary unpaid leave. Subject to employer approval and operational requirements."
        ),
        LeaveType.GOOD_WILL_PAID: LeaveTypeConfig(
            name="Good Will Paid Leave",
            description="Employer discretionary paid leave",
            is_paid=True,
            max_days_per_cycle=365,  # No specific limit
            cycle_months=12,
            requires_proof=False,
            proof_required_after_days=0,
            min_employment_months=0,
            notes="Discretionary paid leave. Employer goodwill benefit beyond BCEA minimums."
        )
    }

@dataclass
class LeaveBalance:
    """Employee leave balance for a specific leave type"""
    employee_id: str
    leave_type: LeaveType
    available_days: float
    used_days: float
    cycle_start_date: datetime
    cycle_end_date: datetime
    last_updated: datetime

@dataclass
class LeaveApplication:
    """Leave application record"""
    id: str
    employee_id: str
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    days_requested: float
    reason: str
    status: LeaveStatus
    applied_date: datetime
    reviewed_by: Optional[str] = None
    reviewed_date: Optional[datetime] = None
    notes: Optional[str] = None
    approved_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    proof_document: Optional[str] = None
    comments: Optional[str] = None

class LeaveCalculator:
    """Calculate leave entitlements and balances"""
    
    @staticmethod
    def calculate_annual_leave_accrual(employment_start_date: datetime, 
                                     working_days_per_week: int = 5) -> float:
        """Calculate annual leave accrual based on employment period"""
        today = datetime.now()
        employment_months = (today - employment_start_date).days / 30.44  # Average days per month
        
        if working_days_per_week == 5:
            monthly_accrual = 1.25  # 15 days / 12 months
        elif working_days_per_week == 6:
            monthly_accrual = 1.5   # 18 days / 12 months
        else:
            monthly_accrual = 1.25  # Default to 5-day week
        
        return min(employment_months * monthly_accrual, 15)  # Max 15 days for 5-day week
    
    @staticmethod
    def calculate_sick_leave_accrual(employment_start_date: datetime,
                                   working_days_per_week: int = 5) -> float:
        """Calculate sick leave accrual based on employment period"""
        today = datetime.now()
        employment_months = (today - employment_start_date).days / 30.44
        
        if employment_months < 6:
            # First 6 months: 1 day per 26 days worked
            days_worked = (today - employment_start_date).days
            return min(days_worked / 26, 30)
        else:
            # After 6 months: Full entitlement over 3-year cycle
            cycle_progress = min(employment_months / 36, 1.0)  # 3 years = 36 months
            if working_days_per_week == 5:
                return cycle_progress * 30
            elif working_days_per_week == 6:
                return cycle_progress * 36
            else:
                return cycle_progress * 30
    
    @staticmethod
    def is_eligible_for_leave(leave_type: LeaveType, 
                            employment_start_date: datetime,
                            working_days_per_week: int = 5) -> bool:
        """Check if employee is eligible for specific leave type"""
        today = datetime.now()
        employment_months = (today - employment_start_date).days / 30.44
        
        config = LeaveEntitlements.LEAVE_TYPES[leave_type]
        
        # Check minimum employment period
        if employment_months < config.min_employment_months:
            return False
        
        # Special check for family responsibility leave
        if leave_type == LeaveType.FAMILY_RESPONSIBILITY:
            return employment_months >= 4 and working_days_per_week >= 4
        
        return True

class LeaveManager:
    """Main leave management system"""
    
    def __init__(self):
        self.leave_applications: Dict[str, LeaveApplication] = {}
        self.leave_balances: Dict[str, List[LeaveBalance]] = {}
        self._load_leave_requests()
    
    def _validate_and_repair_leave_requests(self, db_path):
        """Validate and repair the leave requests JSON file."""
        default_data = []

        # Check if the file exists
        if not os.path.exists(db_path):
            print(f"[WARNING] Leave requests file not found. Creating a new one at: {db_path}")
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4)
            return default_data

        # Validate the JSON structure
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Invalid JSON structure: Expected a list.")
                return data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Corrupted leave requests file: {e}")
            print(f"[INFO] Repairing the leave requests file at: {db_path}")
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=4)
            return default_data

    def _load_leave_requests(self):
        """Load leave requests from the JSON database."""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'attendance_data', 'leave_requests.json')
        db_path = os.path.abspath(db_path)
        print(f"[INFO] Attempting to load leave requests from: {db_path}")

        # Validate and repair the file if necessary
        data = self._validate_and_repair_leave_requests(db_path)

        for entry in data:
            # Robust status handling
            status_str = entry.get('status', 'PENDING').upper()
            try:
                status_enum = LeaveStatus[status_str]
            except KeyError:
                status_enum = LeaveStatus.PENDING
            
            # Robust leave_type handling
            leave_type_str = entry.get('leave_type', 'annual')
            try:
                leave_type_enum = LeaveType(leave_type_str)
            except ValueError:
                leave_type_enum = LeaveType.ANNUAL
            
            leave_application = LeaveApplication(
                id=entry['id'],
                employee_id=entry['employee_id'],
                leave_type=leave_type_enum,
                start_date=datetime.fromisoformat(entry['start_date']),
                end_date=datetime.fromisoformat(entry['end_date']),
                days_requested=(datetime.fromisoformat(entry['end_date']) - datetime.fromisoformat(entry['start_date'])).days + 1,
                reason=entry['reason'],
                status=status_enum,
                applied_date=datetime.fromisoformat(entry['applied_date']),
                approved_by=entry.get('reviewed_by', ''),
                approved_date=datetime.fromisoformat(entry['reviewed_date']) if entry.get('reviewed_date') else None,
                notes=entry.get('notes', '')
            )
            self.leave_applications[leave_application.id] = leave_application
        print(f"[INFO] Successfully loaded {len(self.leave_applications)} leave requests.")
    
    def get_employee_leave_balance(self, employee_id: str, leave_type: LeaveType) -> Optional[LeaveBalance]:
        """Get current leave balance for employee and leave type"""
        if employee_id not in self.leave_balances:
            return None
        
        for balance in self.leave_balances[employee_id]:
            if balance.leave_type == leave_type:
                return balance
        
        return None
    
    def apply_for_leave(self, employee_id: str, leave_type: LeaveType,
                       start_date: datetime, end_date: datetime,
                       reason: str, proof_document: Optional[str] = None) -> str:
        """Submit leave application"""
        
        # Calculate working days
        days_requested = self._calculate_working_days(start_date, end_date)
        
        # Generate application ID
        app_id = f"LA{datetime.now().strftime('%Y%m%d%H%M%S')}{employee_id[-4:]}"
        
        application = LeaveApplication(
            id=app_id,
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=reason,
            status=LeaveStatus.PENDING,
            applied_date=datetime.now(),
            proof_document=proof_document
        )
        
        self.leave_applications[app_id] = application
        self._save_leave_requests()  # Save to disk immediately
        return app_id
    
    def _save_leave_requests(self):
        """Save leave requests to the JSON database."""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'attendance_data', 'leave_requests.json')
        db_path = os.path.abspath(db_path)
        try:
            data = []
            for app in self.leave_applications.values():
                # Handle both enum and string values
                leave_type_value = app.leave_type.value if hasattr(app.leave_type, 'value') else str(app.leave_type)
                status_value = app.status.value if hasattr(app.status, 'value') else str(app.status)
                
                data.append({
                    'id': app.id,
                    'employee_id': app.employee_id,
                    'leave_type': leave_type_value,
                    'start_date': app.start_date.isoformat(),
                    'end_date': app.end_date.isoformat(),
                    'reason': app.reason,
                    'status': status_value,
                    'applied_date': app.applied_date.isoformat(),
                    'reviewed_by': app.reviewed_by or '',
                    'reviewed_date': app.reviewed_date.isoformat() if app.reviewed_date else '',
                    'notes': app.notes or ''
                })
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"[INFO] Saved {len(data)} leave requests to file.")
        except Exception as e:
            print(f"[ERROR] Failed to save leave requests: {e}")
            import traceback
            traceback.print_exc()

    def approve_leave(self, application_id: str, approved_by: str,
                     comments: str = "") -> bool:
        """Approve leave application"""
        if application_id not in self.leave_applications:
            return False
        
        application = self.leave_applications[application_id]
        
        # Check if employee has sufficient leave balance
        balance = self.get_employee_leave_balance(application.employee_id, application.leave_type)
        if balance and balance.available_days < application.days_requested:
            return False  # Insufficient balance
        
        # Approve application
        application.status = LeaveStatus.APPROVED
        application.approved_by = approved_by
        application.approved_date = datetime.now()
        application.comments = comments
        
        # Update leave balance (if balance tracking is implemented)
        if balance:
            balance.available_days -= application.days_requested
            balance.used_days += application.days_requested
            balance.last_updated = datetime.now()
        
        # Save to file
        self._save_leave_requests()
        return True
    
    def reject_leave(self, application_id: str, rejected_by: str,
                    rejection_reason: str) -> bool:
        """Reject leave application"""
        if application_id not in self.leave_applications:
            return False
        
        application = self.leave_applications[application_id]
        application.status = LeaveStatus.REJECTED
        application.approved_by = rejected_by
        application.rejection_reason = rejection_reason
        application.reviewed_date = datetime.now()
        
        # Save to file
        self._save_leave_requests()
        return True
    
    def get_pending_applications(self) -> List[LeaveApplication]:
        """Get all pending leave applications"""
        return [app for app in self.leave_applications.values() 
                if app.status == LeaveStatus.PENDING]
    
    def get_employee_applications(self, employee_id: str) -> List[LeaveApplication]:
        """Get all leave applications for an employee"""
        return [app for app in self.leave_applications.values() 
                if app.employee_id == employee_id]
    
    def get_all_applications(self) -> List[dict]:
        """Return all leave applications from the JSON database."""
        db_path = os.path.join(os.path.dirname(__file__), '..', 'attendance_data', 'leave_requests.json')
        db_path = os.path.abspath(db_path)
        if not os.path.exists(db_path):
            return []
        with open(db_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Ensure each entry has a status field
                for entry in data:
                    if 'status' not in entry:
                        entry['status'] = 'PENDING'
                return data
            except Exception:
                return []
    
    def get_all_leave_requests(self):
        """Return all leave requests as a list of dicts for API responses."""
        result = []
        for app in self.leave_applications.values():
            leave_type_value = app.leave_type.value if hasattr(app.leave_type, 'value') else str(app.leave_type)
            status_value = app.status.value if hasattr(app.status, 'value') else str(app.status)
            result.append({
                'id': app.id,
                'employee_id': app.employee_id,
                'leave_type': leave_type_value,
                'start_date': app.start_date.isoformat(),
                'end_date': app.end_date.isoformat(),
                'days_requested': app.days_requested,
                'reason': app.reason,
                'status': status_value,
                'applied_date': app.applied_date.isoformat() if app.applied_date else None,
                'reviewed_by': getattr(app, 'reviewed_by', ''),
                'reviewed_date': app.reviewed_date.isoformat() if getattr(app, 'reviewed_date', None) else None,
                'notes': getattr(app, 'notes', ''),
                'proof_document': getattr(app, 'proof_document', None),
                'rejection_reason': getattr(app, 'rejection_reason', None),
                'approved_by': getattr(app, 'approved_by', None)
            })
        return result
    
    def _calculate_working_days(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate working days between two dates (excluding weekends)"""
        current_date = start_date
        working_days = 0
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days

# Global leave manager instance
leave_manager = LeaveManager()
