"""
User management: admin user CRUD (create, edit, delete)
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime
from ..services.database import db
from ..models import Admin
from ..utils.auth import is_admin_authenticated

bp_user = Blueprint('user_management', __name__)

# Admin user CRUD routes go here

@bp_user.route('/manage_users')
def manage_users():
    """Manage admin users"""
    if not is_admin_authenticated():
        return redirect(url_for('admin_dashboard.login'))
    return render_template('attendance/admin_users.html', users=[])

# ...existing code...
