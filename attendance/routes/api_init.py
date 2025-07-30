from .admin_dashboard import bp_dashboard
from .employee_management import bp_employee
from .shift_management import bp_shift
from .camera_management import bp_camera
from .reports import bp_reports
from .user_management import bp_user
from .human_detection import bp_human_detection
from .absent_employees import bp_absent

# New modular blueprints
from .terminal_api import bp_terminal
from .network_discovery_api import bp_network_discovery
from .device_cache_api import bp_device_cache

def register_blueprints(app):
    # Original blueprints
    app.register_blueprint(bp_dashboard, url_prefix='/admin')
    app.register_blueprint(bp_employee, url_prefix='/admin')
    app.register_blueprint(bp_shift, url_prefix='/admin')
    app.register_blueprint(bp_camera, url_prefix='/admin')
    app.register_blueprint(bp_reports, url_prefix='/admin')
    app.register_blueprint(bp_user, url_prefix='/admin')
    app.register_blueprint(bp_human_detection, url_prefix='/admin')
    app.register_blueprint(bp_absent, url_prefix='/admin')
    
    # New modular blueprints (replacing terminal_management)
    app.register_blueprint(bp_terminal)  # Already has url_prefix in blueprint definition
    app.register_blueprint(bp_network_discovery)  # Already has url_prefix in blueprint definition
    app.register_blueprint(bp_device_cache)  # Already has url_prefix in blueprint definition
