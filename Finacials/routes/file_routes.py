"""
File handling routes (downloads, progress).
"""
import os
from flask import Blueprint, send_file, flash, redirect, url_for, jsonify
from utils.progress_tracker import progress_tracker
from config import Config

file_bp = Blueprint('file', __name__)

@file_bp.route('/progress/<task_id>')
def progress_status(task_id):
    """Get progress status for a task"""
    progress_data = progress_tracker.get_progress(task_id)
    return jsonify(progress_data)

@file_bp.route('/download/<filename>')
def download_file(filename):
    """Download a file from the Downloads folder"""
    file_path = os.path.join(Config.OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found')
        return redirect(url_for('main.index'))
