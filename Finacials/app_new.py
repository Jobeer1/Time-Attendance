"""
Main Flask application for PDF to Excel/CSV Converter.
Modular architecture with separated concerns.
"""
import logging
from flask import Flask, render_template

# Import configuration
from config import Config

# Import blueprints
from routes.pdf_routes import pdf_bp
from routes.text_routes import text_bp
from routes.batch_routes import batch_bp
from routes.file_routes import file_bp

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Ensure required directories exist
    Config.ensure_directories_exist()
    
    # Register blueprints
    app.register_blueprint(pdf_bp)
    app.register_blueprint(text_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(file_bp)
    
    # Main route
    @app.route('/')
    def index():
        return render_template('index_new.html')
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)
