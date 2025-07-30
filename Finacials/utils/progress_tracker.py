"""
Progress tracking utilities for long-running tasks.
"""
import time
import uuid
from config import Config

class ProgressTracker:
    """Manages progress tracking for background tasks"""
    
    def __init__(self):
        self.tracker = {}
    
    def create_task(self):
        """Create a new task and return its ID"""
        task_id = str(uuid.uuid4())
        self.tracker[task_id] = {
            'progress': 0,
            'message': 'Starting...',
            'timestamp': time.time()
        }
        return task_id
    
    def update_progress(self, task_id, progress, message):
        """Update progress for a task"""
        self.tracker[task_id] = {
            'progress': progress,
            'message': message,
            'timestamp': time.time()
        }
        # Small delay to ensure proper updates
        time.sleep(Config.PROGRESS_UPDATE_DELAY)
    
    def get_progress(self, task_id):
        """Get current progress for a task"""
        return self.tracker.get(task_id, {
            'progress': 0, 
            'message': 'Starting...', 
            'timestamp': time.time()
        })
    
    def cleanup_task(self, task_id):
        """Remove completed task from tracker"""
        if task_id in self.tracker:
            del self.tracker[task_id]
    
    def cleanup_old_tasks(self, max_age_hours=24):
        """Clean up tasks older than specified hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        old_tasks = [
            task_id for task_id, data in self.tracker.items()
            if current_time - data['timestamp'] > max_age_seconds
        ]
        
        for task_id in old_tasks:
            del self.tracker[task_id]

# Global progress tracker instance
progress_tracker = ProgressTracker()
