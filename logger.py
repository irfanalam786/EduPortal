"""
Logging system for EduPortal
Handles activity logging and error logging
"""

import json
import os
from datetime import datetime
from config import ACTIVITIES_FILE, MAX_ACTIVITY_LOGS
from utils import load_json, save_json

class Logger:
    """Activity and error logger"""
    
    @staticmethod
    def log_activity(user, action, entity_type=None, entity_id=None, description="", status="success", details=None):
        """Log user activity"""
        activities = load_json(ACTIVITIES_FILE)
        
        if not isinstance(activities, list):
            activities = []
        
        activity = {
            "id": f"ACT_{len(activities) + 1:06d}",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user": user,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "description": description,
            "status": status,
            "details": details or {}
        }
        
        activities.append(activity)
        
        # Keep only last MAX_ACTIVITY_LOGS entries
        if len(activities) > MAX_ACTIVITY_LOGS:
            activities = activities[-MAX_ACTIVITY_LOGS:]
        
        save_json(ACTIVITIES_FILE, activities)
        return activity
    
    @staticmethod
    def log_error(error_message, user=None, details=None):
        """Log error to error log file"""
        error_log_path = os.path.join(os.path.dirname(ACTIVITIES_FILE), 'errors.log')
        
        error_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user": user or "SYSTEM",
            "error": error_message,
            "details": details or {}
        }
        
        try:
            with open(error_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_entry) + '\n')
        except:
            pass  # Silently fail if logging fails
    
    @staticmethod
    def get_activities(user=None, action=None, limit=100):
        """Get activity logs with optional filters"""
        activities = load_json(ACTIVITIES_FILE)
        
        if not isinstance(activities, list):
            return []
        
        # Filter by user if provided
        if user:
            activities = [a for a in activities if a.get('user') == user]
        
        # Filter by action if provided
        if action:
            activities = [a for a in activities if a.get('action') == action]
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit results
        return activities[:limit]

