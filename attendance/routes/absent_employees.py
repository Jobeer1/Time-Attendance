"""
Absent employees: API for absent today, with last clock-in and absence reason
"""
from flask import Blueprint, jsonify
from datetime import date, datetime
from ..services.database import db
from ..utils.auth import is_admin_authenticated

bp_absent = Blueprint('absent_employees', __name__)

# /api/absent-employees endpoint will be implemented here
# ...existing code...
