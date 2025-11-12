"""
Utility functions for EduPortal
Helper functions for data manipulation, validation, and formatting
"""

import json
import os
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from config import DATA_DIR

def load_json(filepath):
    """Load JSON data from file"""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_json(filepath, data):
    """Save data to JSON file with backup"""
    try:
        # Create backup if file exists
        if os.path.exists(filepath):
            backup_path = f"{filepath}.backup"
            with open(filepath, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_data)
        
        # Save new data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def encrypt_password(password):
    """Encrypt password using SHA256 (same as hash_password for consistency)"""
    return hash_password(password)

def decrypt_password(encrypted_password):
    """Passwords are hashed, not encrypted - this returns the hash as-is"""
    # Note: Passwords are one-way hashed, not encrypted
    # This function is kept for API compatibility
    return encrypted_password

def generate_session_token():
    """Generate secure random session token"""
    return secrets.token_urlsafe(32)

def generate_registration_id(prefix="REG"):
    """Generate unique registration ID: REG-[YYYYMMDDHHMMSS]-[XXXX]"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"{prefix}-{timestamp}-{random_suffix}"

def generate_id(prefix):
    """Generate unique ID with prefix"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(3))
    return f"{prefix}_{timestamp}{random_suffix}"

def generate_username(name, existing_usernames):
    """Generate unique username from name"""
    # Remove special characters and spaces, convert to lowercase
    base_username = ''.join(c.lower() for c in name if c.isalnum() or c == ' ').replace(' ', '.')
    
    # If base is empty, use default
    if not base_username:
        base_username = 'user'
    
    username = base_username
    counter = 1
    
    # Ensure uniqueness
    while username in existing_usernames:
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def convert_24_to_12(time_24):
    """Convert 24-hour time to 12-hour format"""
    try:
        hour, minute = map(int, time_24.split(':'))
        period = "AM" if hour < 12 else "PM"
        hour_12 = hour if hour <= 12 else hour - 12
        if hour_12 == 0:
            hour_12 = 12
        return f"{hour_12}:{minute:02d} {period}"
    except:
        return time_24

def convert_12_to_24(time_12):
    """Convert 12-hour time to 24-hour format"""
    try:
        time_part, period = time_12.rsplit(' ', 1)
        hour, minute = map(int, time_part.split(':'))
        if period.upper() == "PM" and hour != 12:
            hour += 12
        elif period.upper() == "AM" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
    except:
        return time_12

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number (10 digits)"""
    import re
    pattern = r'^\d{10}$'
    return re.match(pattern, phone.replace('-', '').replace(' ', '')) is not None

def sanitize_input(text):
    """Sanitize user input"""
    if not isinstance(text, str):
        return str(text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Escape HTML special characters
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text

def check_time_clash(day, start_time, end_time, timetable_data, exclude_id=None, section=None):
    """Check if time slot clashes with existing entries (for same section)"""
    if day not in timetable_data:
        return None
    
    start_24 = convert_12_to_24(start_time) if ':' in start_time and ('AM' in start_time or 'PM' in start_time) else start_time
    end_24 = convert_12_to_24(end_time) if ':' in end_time and ('AM' in end_time or 'PM' in end_time) else end_time
    
    start_hour, start_min = map(int, start_24.split(':'))
    end_hour, end_min = map(int, end_24.split(':'))
    
    start_total = start_hour * 60 + start_min
    end_total = end_hour * 60 + end_min
    
    for entry in timetable_data[day]:
        if exclude_id and entry.get('id') == exclude_id:
            continue
        
        # Check section match if section is provided
        if section and entry.get('section', '').upper() != section.upper():
            continue
        
        entry_start = entry.get('start_time', '')
        entry_end = entry.get('end_time', '')
        
        entry_start_24 = convert_12_to_24(entry_start) if ':' in entry_start and ('AM' in entry_start or 'PM' in entry_start) else entry_start
        entry_end_24 = convert_12_to_24(entry_end) if ':' in entry_end and ('AM' in entry_end or 'PM' in entry_end) else entry_end
        
        try:
            e_start_hour, e_start_min = map(int, entry_start_24.split(':'))
            e_end_hour, e_end_min = map(int, entry_end_24.split(':'))
            
            e_start_total = e_start_hour * 60 + e_start_min
            e_end_total = e_end_hour * 60 + e_end_min
            
            # Check overlap: new_start < existing_end AND new_end > existing_start
            if start_total < e_end_total and end_total > e_start_total:
                return {
                    'clash': True,
                    'conflicting_class': entry.get('class_name', 'Unknown'),
                    'conflicting_time': f"{entry.get('start_time_12', entry_start)} - {entry.get('end_time_12', entry_end)}"
                }
        except:
            continue
    
    return None

def get_current_timestamp():
    """Get current timestamp in ISO format"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

def format_datetime(dt_string):
    """Format datetime string for display"""
    try:
        dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_string

def is_expired_timetable_entry(entry):
    """Check if timetable entry is expired (end time < current time)"""
    try:
        day = entry.get('day', '')
        end_time = entry.get('end_time', '')
        
        # Convert to 24-hour if needed
        end_24 = convert_12_to_24(end_time) if ':' in end_time and ('AM' in end_time or 'PM' in end_time) else end_time
        end_hour, end_min = map(int, end_24.split(':'))
        
        now = datetime.now()
        current_day = now.strftime("%A")
        
        # Only check if it's the same day
        if day == current_day:
            current_total = now.hour * 60 + now.minute
            end_total = end_hour * 60 + end_min
            return end_total < current_total
        
        return False
    except:
        return False

