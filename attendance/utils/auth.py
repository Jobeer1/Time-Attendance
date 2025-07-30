"""
Authentication helpers for admin
"""
def is_admin_authenticated():
    from flask import session
    return 'admin_id' in session
