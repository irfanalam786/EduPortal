"""
EduPortal - Main Flask Application
Educational Management System Backend
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime, timedelta
from config import *
from utils import *
from logger import Logger

# Import generate_username
from utils import generate_username

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = os.urandom(32)  # Change in production
CORS(app, supports_credentials=True)

# In-memory session storage (in production, use Redis or database)
active_sessions = {}

ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_PHOTO_SIZE_MB = 5
MAX_PHOTO_SIZE_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024


def resolve_username_key(users, username):
    """Return the exact key for a username (case-insensitive)."""
    if not username:
        return None
    if username in users:
        return username
    lower = username.lower()
    for key in users.keys():
        if key.lower() == lower:
            return key
    return None


def get_profile_photo_url(user_record):
    """Return absolute static path for stored profile photo."""
    profile = user_record.get('profile') or {}
    photo_rel = profile.get('photo')
    if not photo_rel:
        return None
    normalized = photo_rel.lstrip('/').replace('\\', '/')
    return f"/static/{normalized}"


def delete_profile_photo_file(photo_rel_path):
    """Remove existing profile photo file from disk."""
    if not photo_rel_path:
        return
    abs_path = os.path.join(STATIC_DIR, photo_rel_path.replace('/', os.sep))
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except OSError:
            pass


def allowed_photo(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS

# Initialize default admin user
def initialize_default_admin():
    """Create default admin user if not exists"""
    users = load_json(USERS_FILE)
    # Always ensure ADMIN user exists and has default password (useful to reset to DEFAULT_ADMIN_PASSWORD)
    if 'ADMIN' not in users:
        users['ADMIN'] = {
            "id": "ADMIN",
            "username": "ADMIN",
            "password": hash_password(DEFAULT_ADMIN_PASSWORD),
            "role": "Admin",
            "registration_id": generate_registration_id(),
            "status": "active",
            "profile_completed": True,
            "profile": {
                "first_name": "System",
                "last_name": "Administrator",
                "dob": "1990-01-01",
                "gender": "Other",
                "marital_status": "Single",
                "email": "admin@eduportal.com",
                "father_name": "N/A",
                "mother_name": "N/A"
            },
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp(),
            "last_login": None,
            "login_count": 0,
            "failed_login_attempts": 0,
            "account_locked": False,
            "locked_until": None
            ,"password_encrypted": encrypt_password(DEFAULT_ADMIN_PASSWORD),
            "password_plain": DEFAULT_ADMIN_PASSWORD
        }
        save_json(USERS_FILE, users)
    else:
        # If ADMIN exists but password isn't the configured default, update it so admin password matches DEFAULT_ADMIN_PASSWORD
        try:
            expected = hash_password(DEFAULT_ADMIN_PASSWORD)
            if users.get('ADMIN', {}).get('password') != expected:
                users['ADMIN']['password'] = expected
                users['ADMIN']['password_changed'] = False
                # Update encrypted copy as well
                try:
                    users['ADMIN']['password_encrypted'] = encrypt_password(DEFAULT_ADMIN_PASSWORD)
                except Exception:
                    pass
                users['ADMIN']['updated_at'] = get_current_timestamp()
                users['ADMIN']['account_locked'] = False
                users['ADMIN']['failed_login_attempts'] = 0
                users['ADMIN']['locked_until'] = None
                users['ADMIN']['password_plain'] = DEFAULT_ADMIN_PASSWORD
                save_json(USERS_FILE, users)
        except Exception:
            # If anything goes wrong, don't crash initialization
            pass

# Initialize timetable structure
def initialize_timetable():
    """Initialize timetable structure if not exists"""
    timetable = load_json(TIMETABLE_FILE)
    if not timetable:
        timetable = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": []
        }
        save_json(TIMETABLE_FILE, timetable)
    return timetable

# Initialize data files
initialize_default_admin()
initialize_timetable()

# Session management helpers
def create_session(username, role):
    """Create new session"""
    token = generate_session_token()
    now = datetime.now()
    active_sessions[token] = {
        'username': username,
        'role': role,
        'created_at': now,
        'last_activity': now,
        'expires_at': now + timedelta(seconds=SESSION_TIMEOUT_SECONDS)
    }
    return token

def validate_session(token):
    """Validate session token"""
    if token not in active_sessions:
        return None
    
    session_data = active_sessions[token]
    now = datetime.now()
    expires_at = session_data.get('expires_at')
    if not expires_at:
        created_at = session_data.get('created_at', now)
        expires_at = created_at + timedelta(seconds=SESSION_TIMEOUT_SECONDS)
        session_data['expires_at'] = expires_at
    
    # Check if session expired
    if now > expires_at:
        del active_sessions[token]
        return None
    
    # Update last activity
    session_data['last_activity'] = now
    return session_data

def destroy_session(token):
    """Destroy session"""
    if token in active_sessions:
        del active_sessions[token]

def require_auth(f):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            token = request.json.get('session_token') if request.is_json else None
        
        session_data = validate_session(token)
        if not session_data:
            return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401
        
        request.session_data = session_data
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Routes
@app.route('/')
def index():
    """Redirect to login"""
    return redirect('/login')

@app.route('/login')
def login_page():
    """Serve login page"""
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    """Serve dashboard page"""
    return render_template('dashboard.html')

@app.route('/academics')
def academics_page():
    """Serve academics page"""
    return render_template('dashboard.html')

@app.route('/students')
def students_page():
    """Serve students page"""
    return render_template('dashboard.html')

@app.route('/events')
def events_page():
    """Serve events page"""
    return render_template('dashboard.html')

@app.route('/timetable')
def timetable_page():
    """Serve timetable page"""
    return render_template('dashboard.html')

@app.route('/profile')
def profile_page():
    """Serve profile page"""
    return render_template('dashboard.html')

@app.route('/change-password')
def change_password_page():
    """Serve change password page (for first-time login)"""
    return render_template('dashboard.html')

@app.route('/users')
def users_page():
    """Serve users page"""
    return render_template('dashboard.html')

@app.route('/activities')
def activities_page():
    """Serve activities page"""
    return render_template('dashboard.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400
    
    users = load_json(USERS_FILE)

    user_key = resolve_username_key(users, username)

    if not user_key:
        # Don't log login attempts
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    user = users[user_key]
    
    # Check if account is locked
    if user.get('account_locked') and user.get('locked_until'):
        locked_until = datetime.strptime(user['locked_until'], "%Y-%m-%dT%H:%M:%SZ")
        if datetime.now() < locked_until:
            return jsonify({'success': False, 'message': 'Account is locked. Please try again later.'}), 403
    
    # Check status
    if user.get('status') != 'active':
        # Don't log login attempts
        # Logger.log_activity(username, 'LOGIN_ATTEMPT', description='Failed login - account inactive', status='failed')
        return jsonify({'success': False, 'message': 'Account is inactive. Please contact administrator.'}), 403
    
    # Verify password
    if not verify_password(password, user['password']):
        # Increment failed attempts
        user['failed_login_attempts'] = user.get('failed_login_attempts', 0) + 1
        
        if user['failed_login_attempts'] >= MAX_LOGIN_ATTEMPTS:
            user['account_locked'] = True
            user['locked_until'] = (datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)).strftime("%Y-%m-%dT%H:%M:%SZ")
            # Don't log login attempts
            # Logger.log_activity(username, 'ACCOUNT_LOCKED', description='Account locked due to multiple failed login attempts', status='warning')
        
        save_json(USERS_FILE, users)
        # Don't log login attempts
        # Logger.log_activity(username, 'LOGIN_ATTEMPT', description='Failed login - invalid password', status='failed')
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    # Check if using default password (first login)
    from config import DEFAULT_ACADEMIC_PASSWORD, DEFAULT_STUDENT_PASSWORD
    is_default_password = False
    if user['role'] == 'Faculty':
        is_default_password = verify_password(DEFAULT_ACADEMIC_PASSWORD, user['password'])
    elif user['role'] == 'Student':
        is_default_password = verify_password(DEFAULT_STUDENT_PASSWORD, user['password'])
    
    # Reset failed attempts on successful login
    user['failed_login_attempts'] = 0
    user['account_locked'] = False
    user['locked_until'] = None
    user['last_login'] = get_current_timestamp()
    user['login_count'] = user.get('login_count', 0) + 1
    
    # Track if password has been changed
    if 'password_changed' not in user:
        user['password_changed'] = not is_default_password
    
    save_json(USERS_FILE, users)
    
    # Create session
    token = create_session(username, user['role'])
    
    # Don't log login/logout activities
    # Logger.log_activity(username, 'USER_LOGIN', 'User', username, 'User logged in successfully', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': {
            'username': username,
            'role': user['role'],
            'profile_completed': user.get('profile_completed', False),
            'password_changed': user.get('password_changed', False),
            'is_default_password': is_default_password
        },
        'session_token': token
    })

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Reset password after verifying DOB year"""
    data = request.json or {}
    username = data.get('username', '').strip()
    dob_year = str(data.get('dob_year', '')).strip()
    new_password = data.get('new_password', '')
    
    if not username or not dob_year or not new_password:
        return jsonify({'success': False, 'message': 'Username, year of birth, and new password are required.'}), 400
    
    if len(dob_year) != 4 or not dob_year.isdigit():
        return jsonify({'success': False, 'message': 'Enter a valid 4-digit year of birth.'}), 400
    
    if len(new_password) < PASSWORD_MIN_LENGTH:
        return jsonify({'success': False, 'message': f'New password must be at least {PASSWORD_MIN_LENGTH} characters.'}), 400
    
    users = load_json(USERS_FILE)
    user_key = resolve_username_key(users, username)
    if not user_key:
        return jsonify({'success': False, 'message': 'Unable to verify the provided details.'}), 404
    
    user = users[user_key]
    profile = user.get('profile', {})
    dob = profile.get('dob', '')
    if not dob:
        return jsonify({'success': False, 'message': 'DOB is not available. Please contact the administrator.'}), 400
    
    profile_year = dob.split('-')[0]
    if profile_year != dob_year:
        return jsonify({'success': False, 'message': 'The provided details do not match our records.'}), 403
    
    user['password'] = hash_password(new_password)
    try:
        user['password_encrypted'] = encrypt_password(new_password)
    except Exception:
        pass
    user['password_plain'] = new_password
    user['password_changed'] = True
    user['updated_at'] = get_current_timestamp()
    user['failed_login_attempts'] = 0
    user['account_locked'] = False
    user['locked_until'] = None
    
    save_json(USERS_FILE, users)
    Logger.log_activity(user_key, 'PASSWORD_RESET', 'User', user_key, 'Password reset via DOB verification', 'success')
    
    return jsonify({'success': True, 'message': 'Password reset successfully. You can now log in with your new password.'})

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout endpoint"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = request.json.get('session_token') if request.is_json else None
    
    username = request.session_data['username']
    destroy_session(token)
    
    # Don't log login/logout activities
    # Logger.log_activity(username, 'USER_LOGOUT', 'User', username, 'User logged out', 'success')
    
    return jsonify({'success': True, 'message': 'Logout successful'})

@app.route('/api/auth/session-status', methods=['GET'])
@require_auth
def session_status():
    """Check session status and get remaining time"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session_data = validate_session(token)
    
    if not session_data:
        return jsonify({'success': False, 'message': 'Session expired'}), 401
    
    expires_at = session_data.get('expires_at')
    if not expires_at:
        created_at = session_data.get('created_at', datetime.now())
        expires_at = created_at + timedelta(seconds=SESSION_TIMEOUT_SECONDS)
        session_data['expires_at'] = expires_at
    remaining = max(0, int((expires_at - datetime.now()).total_seconds()))
    
    return jsonify({
        'success': True,
        'remaining_seconds': remaining,
        'total_seconds': SESSION_TIMEOUT_SECONDS,
        'user': {
            'username': session_data['username'],
            'role': session_data['role']
        }
    })

# User Management APIs
@app.route('/api/users/list', methods=['GET'])
@require_auth
def list_users():
    """List all users with profile completion status"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    users = load_json(USERS_FILE)
    user_list = []
    
    for username, user_data in users.items():
        plain_password = user_data.get('password_plain')
        encrypted = user_data.get('password_encrypted')
        if not plain_password:
            # Fallback to encrypted value if legacy record
            plain_password = encrypted
        photo_url = get_profile_photo_url(user_data)

        user_list.append({
            'id': user_data.get('id'),
            'username': username,
            'role': user_data.get('role'),
            'password_hash': user_data.get('password'),
            'password_encrypted': encrypted,
            'password_plain': plain_password,
            'status': user_data.get('status'),
            'email': user_data.get('profile', {}).get('email', ''),
            'last_login': user_data.get('last_login'),
            'registration_id': user_data.get('registration_id'),
            'profile_completed': user_data.get('profile_completed', False),
            'profile_status': 'Completed' if user_data.get('profile_completed', False) else 'Incomplete',
            'profile_photo_url': photo_url
        })
    
    return jsonify({'success': True, 'data': user_list, 'total': len(user_list)})

@app.route('/api/users/add', methods=['POST'])
@require_auth
def add_user():
    """Add new user"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    name = data.get('name', '').strip()
    role = data.get('role', '')
    
    if not name or not role:
        return jsonify({'success': False, 'message': 'Name and role are required'}), 400
    
    users = load_json(USERS_FILE)
    
    # Auto-generate username (except for admin)
    existing_usernames = set(users.keys())
    username = generate_username(name, existing_usernames)
    
    # Set default password based on role
    default_password = DEFAULT_ACADEMIC_PASSWORD if role == 'Faculty' else DEFAULT_STUDENT_PASSWORD
    
    user_id = generate_id('USR')
    users[username] = {
        "id": user_id,
        "username": username,
        "password": hash_password(default_password),
        "password_encrypted": encrypt_password(default_password),
        "password_plain": default_password,
        "role": role,
        "registration_id": generate_registration_id(),
        "status": "active",
        "profile_completed": False,
        "profile": {},
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
        "created_by": request.session_data['username'],
        "last_login": None,
        "login_count": 0,
        "failed_login_attempts": 0,
        "account_locked": False,
        "locked_until": None
    }
    
    save_json(USERS_FILE, users)
    Logger.log_activity(request.session_data['username'], 'USER_ADDED', 'User', username, f'User {username} created', 'success')
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'user': {
            'id': user_id,
            'username': username,
            'role': role,
            'registration_id': users[username]['registration_id'],
            'default_password': default_password
        }
    }), 201

@app.route('/api/users/change-password', methods=['PUT'])
@require_auth
def change_password():
    """Change user password"""
    data = request.json
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    username = request.session_data['username']
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Current and new passwords are required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters'}), 400
    
    users = load_json(USERS_FILE)
    
    if username not in users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    user = users[username]
    
    # Verify current password
    if not verify_password(current_password, user['password']):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
    
    # Update password
    user['password'] = hash_password(new_password)
    # Update encrypted copy for admin view (if encryption available)
    try:
        user['password_encrypted'] = encrypt_password(new_password)
    except Exception:
        pass
    user['password_plain'] = new_password
    user['password_changed'] = True  # Mark password as changed
    user['updated_at'] = get_current_timestamp()
    
    save_json(USERS_FILE, users)
    Logger.log_activity(username, 'PASSWORD_CHANGED', 'User', username, 'Password changed', 'success')
    
    return jsonify({
        'success': True, 
        'message': 'Password changed successfully',
        'password_changed': True
    })

@app.route('/api/users/<username>/details', methods=['GET'])
@require_auth
def get_user_details(username):
    """Get user details (admin sees password, academics don't)"""
    users = load_json(USERS_FILE)
    
    if username not in users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    user = users[username].copy()
    role = request.session_data['role']
    
    # Admin can see password, academics cannot
    if role == 'Admin':
        plain_password = user.get('password_plain') or user.get('password_encrypted')
        user_profile = user.get('profile', {}) or {}
        user_data = {
            'username': username,
            'role': user.get('role'),
            'password_hash': user.get('password'),  # Admin can see password hash
            'password_encrypted': user.get('password_encrypted'),
            'password_plain': plain_password,
            'status': user.get('status'),
            'registration_id': user.get('registration_id'),
            'profile_completed': user.get('profile_completed', False),
            'profile': user_profile,
            'profile_photo_url': get_profile_photo_url(user),
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login'),
            'login_count': user.get('login_count', 0)
        }
    elif role == 'Faculty':
        # Academics can see everything except password
        user_data = {
            'username': username,
            'role': user.get('role'),
            'status': user.get('status'),
            'registration_id': user.get('registration_id'),
            'profile_completed': user.get('profile_completed', False),
            'profile': user.get('profile', {}),
            'profile_photo_url': get_profile_photo_url(user),
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login'),
            'login_count': user.get('login_count', 0)
        }
    else:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    return jsonify({'success': True, 'user': user_data})

@app.route('/api/users/<username>/status', methods=['PUT'])
@require_auth
def update_user_status(username):
    """Update user status"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    users = load_json(USERS_FILE)
    
    if username not in users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    old_status = users[username].get('status')
    users[username]['status'] = new_status
    users[username]['updated_at'] = get_current_timestamp()
    
    save_json(USERS_FILE, users)
    Logger.log_activity(request.session_data['username'], 'USER_STATUS_CHANGED', 'User', username, f'Status changed from {old_status} to {new_status}', 'success')
    
    return jsonify({
        'success': True,
        'message': 'User status updated',
        'user': {
            'username': username,
            'status': new_status
        }
    })

# Profile Management APIs
@app.route('/api/profile/get', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    username = request.session_data['username']
    role = request.session_data['role']
    
    users = load_json(USERS_FILE)
    
    if username not in users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    user = users[username]
    
    # Check if user can view this profile
    if role != 'Admin' and username != request.session_data['username']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    return jsonify({
        'success': True,
        'profile': user.get('profile', {}) or {},
        'registration_id': user.get('registration_id'),
        'profile_completed': user.get('profile_completed', False),
        'username': username,
        'role': user.get('role'),
        'profile_photo_url': get_profile_photo_url(user)
    })

@app.route('/api/profile/photo', methods=['POST'])
@require_auth
def upload_profile_photo():
    """Upload or replace a profile photo"""
    target_username = request.form.get('username', '').strip() or request.session_data['username']
    users = load_json(USERS_FILE)
    target_key = resolve_username_key(users, target_username)
    
    if not target_key:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if request.session_data['role'] != 'Admin' and target_key != request.session_data['username']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if 'photo' not in request.files:
        return jsonify({'success': False, 'message': 'Photo file is required'}), 400
    
    photo = request.files['photo']
    if not photo or photo.filename == '':
        return jsonify({'success': False, 'message': 'Invalid photo upload'}), 400
    
    if not allowed_photo(photo.filename):
        return jsonify({'success': False, 'message': 'Unsupported file type. Please upload PNG, JPG, JPEG, GIF, or WEBP images.'}), 400
    
    # Validate size
    photo.stream.seek(0, os.SEEK_END)
    size_bytes = photo.stream.tell()
    photo.stream.seek(0)
    if size_bytes > MAX_PHOTO_SIZE_BYTES:
        return jsonify({'success': False, 'message': f'File too large. Maximum allowed size is {MAX_PHOTO_SIZE_MB} MB.'}), 400
    
    ext = photo.filename.rsplit('.', 1)[1].lower()
    safe_name = secure_filename(f"{target_key}_{int(time.time())}.{ext}")
    save_path = os.path.join(PROFILE_PHOTOS_DIR, safe_name)
    
    os.makedirs(PROFILE_PHOTOS_DIR, exist_ok=True)
    
    # Delete existing photo if present
    profile = users[target_key].setdefault('profile', {})
    old_photo = profile.get('photo')
    if old_photo:
        delete_profile_photo_file(old_photo)
    
    photo.save(save_path)
    relative_path = os.path.relpath(save_path, STATIC_DIR).replace('\\', '/')
    profile['photo'] = relative_path
    users[target_key]['profile'] = profile
    users[target_key]['updated_at'] = get_current_timestamp()
    
    save_json(USERS_FILE, users)
    photo_url = f"/static/{relative_path}"
    Logger.log_activity(request.session_data['username'], 'PROFILE_PHOTO_UPDATED', 'User', target_key, 'Profile photo updated', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Profile photo updated successfully',
        'photo_url': photo_url,
        'username': target_key
    })

@app.route('/api/profile/update', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    username = request.session_data['username']
    role = request.session_data['role']
    data = request.json
    
    # Check if updating own profile or admin updating any profile
    target_username = data.get('username', username)
    if role != 'Admin' and target_username != username:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    users = load_json(USERS_FILE)
    
    if target_username not in users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Determine if faculty email is immutable for self-service edits
    is_self_faculty = role == 'Faculty' and target_username == username
    immutable_email = None
    if is_self_faculty:
        existing_profile = users[target_username].get('profile', {})
        immutable_email = existing_profile.get('email', '').strip().lower()
        if not immutable_email:
            academics = load_json(ACADEMICS_FILE)
            acad_id = users[target_username].get('id')
            if acad_id and acad_id in academics:
                immutable_email = academics[acad_id].get('email', '').strip().lower()

    # Validate required fields
    required_fields = ['first_name', 'last_name', 'dob', 'gender', 'marital_status', 'father_name', 'mother_name']
    profile = {}
    
    for field in required_fields:
        value = data.get(field, '').strip()
        if not value:
            return jsonify({'success': False, 'message': f'{field.replace("_", " ").title()} is required'}), 400
        profile[field] = sanitize_input(value)
    
    # Handle email separately to keep faculty read-only
    if is_self_faculty:
        if not immutable_email:
            return jsonify({'success': False, 'message': 'Email must be assigned by an administrator before completing your profile.'}), 400
        profile['email'] = immutable_email
    else:
        email_value = data.get('email', '').strip()
        if not email_value:
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        sanitized_email = sanitize_input(email_value).lower()
        profile['email'] = sanitized_email
        if not validate_email(profile['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    # Validate email format for faculty (immutable value)
    if is_self_faculty and not validate_email(profile['email']):
        return jsonify({'success': False, 'message': 'Invalid email format. Please contact an administrator to correct it.'}), 400
    
    # Validate date
    try:
        dob_date = datetime.strptime(profile['dob'], "%Y-%m-%d")
        if dob_date > datetime.now():
            return jsonify({'success': False, 'message': 'Date of birth must be in the past'}), 400
    except:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    existing_profile = users[target_username].get('profile', {}) or {}
    if existing_profile.get('photo'):
        profile['photo'] = existing_profile['photo']
    users[target_username]['profile'] = profile
    users[target_username]['profile_completed'] = True
    users[target_username]['updated_at'] = get_current_timestamp()
    
    save_json(USERS_FILE, users)
    Logger.log_activity(username, 'PROFILE_UPDATED', 'User', target_username, 'Profile updated', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'profile': profile
    })

# Academic Management APIs
@app.route('/api/academics/list', methods=['GET'])
@require_auth
def list_academics():
    """List all academics"""
    academics = load_json(ACADEMICS_FILE)
    users = load_json(USERS_FILE)
    academic_list = []
    
    for acad_id, acad_data in academics.items():
        # Find username from users
        username = None
        for uname, user_data in users.items():
            if user_data.get('role') == 'Faculty' and user_data.get('id') == acad_id:
                username = uname
                break
        
        academic_list.append({
            'id': acad_id,
            'name': acad_data.get('name'),
            'username': username,
            'department': acad_data.get('department'),
            'qualification': acad_data.get('qualification'),
            'experience': acad_data.get('experience'),
            'email': acad_data.get('email'),
            'phone': acad_data.get('phone'),
            'status': acad_data.get('status', 'active'),
            'registration_id': acad_data.get('registration_id')
        })
    
    return jsonify({'success': True, 'data': academic_list, 'total': len(academic_list)})

@app.route('/api/academics/<acad_id>/view', methods=['GET'])
@require_auth
def view_academic(acad_id):
    """View academic details"""
    academics = load_json(ACADEMICS_FILE)
    users = load_json(USERS_FILE)
    
    if acad_id not in academics:
        return jsonify({'success': False, 'message': 'Academic not found'}), 404
    
    acad = academics[acad_id].copy()
    
    # Find associated user
    username = None
    user_data = None
    for uname, u_data in users.items():
        if u_data.get('role') == 'Faculty' and u_data.get('id') == acad_id:
            username = uname
            user_data = u_data
            break
    
    acad['username'] = username
    if user_data:
        acad['user_profile'] = user_data.get('profile', {})
        acad['profile_completed'] = user_data.get('profile_completed', False)
        acad['registration_id'] = user_data.get('registration_id')
        acad['profile_photo_url'] = get_profile_photo_url(user_data)
        # If requester is Admin, include user's password hash
        if request.session_data.get('role') == 'Admin':
            acad['password'] = user_data.get('password')
            acad['password_plain'] = user_data.get('password_plain') or user_data.get('password_encrypted')
    
    return jsonify({'success': True, 'academic': acad})

@app.route('/api/academics/add', methods=['POST'])
@require_auth
def add_academic():
    """Add new academic"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    qualification = data.get('qualification', '').strip()
    experience = data.get('experience', '').strip()
    email = data.get('email', '').strip()
    phone = data.get('phone', '').strip()
    
    # Validation
    if not all([name, department, qualification, experience, email, phone]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if not validate_email(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    if not validate_phone(phone):
        return jsonify({'success': False, 'message': 'Invalid phone number format'}), 400
    
    try:
        exp_num = int(experience)
        if exp_num < 0 or exp_num > 60:
            return jsonify({'success': False, 'message': 'Experience must be between 0 and 60 years'}), 400
    except:
        return jsonify({'success': False, 'message': 'Experience must be a number'}), 400
    
    academics = load_json(ACADEMICS_FILE)
    users = load_json(USERS_FILE)
    
    # Check duplicate email
    for acad in academics.values():
        if acad.get('email', '').lower() == email.lower():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
    
    acad_id = generate_id('ACM')
    
    # Auto-generate username
    existing_usernames = set(users.keys())
    username = generate_username(name, existing_usernames)
    
    academics[acad_id] = {
        "id": acad_id,
        "name": sanitize_input(name),
        "username": username,
        "department": sanitize_input(department),
        "qualification": sanitize_input(qualification),
        "experience": str(exp_num),
        "email": email.lower(),
        "phone": phone,
        "status": "active",
        "registration_id": generate_registration_id(),
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
        "created_by": request.session_data['username']
    }
    
    # Create user account for academic
    users[username] = {
        "id": acad_id,
        "username": username,
        "password": hash_password(DEFAULT_ACADEMIC_PASSWORD),
        "password_encrypted": encrypt_password(DEFAULT_ACADEMIC_PASSWORD),
        "password_plain": DEFAULT_ACADEMIC_PASSWORD,
        "role": "Faculty",
        "registration_id": academics[acad_id]['registration_id'],
        "status": "active",
        "profile_completed": False,
        "profile": {
            "email": email.lower()
        },
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
        "created_by": request.session_data['username'],
        "last_login": None,
        "login_count": 0,
        "failed_login_attempts": 0,
        "account_locked": False,
        "locked_until": None
    }
    
    save_json(ACADEMICS_FILE, academics)
    save_json(USERS_FILE, users)
    Logger.log_activity(request.session_data['username'], 'ACADEMIC_ADDED', 'Academic', acad_id, f'Academic {name} added', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Academic added successfully',
        'academic': {
            'id': acad_id,
            'name': name,
            'username': username,
            'registration_id': academics[acad_id]['registration_id'],
            'default_password': DEFAULT_ACADEMIC_PASSWORD
        }
    }), 201

@app.route('/api/academics/<acad_id>', methods=['PUT'])
@require_auth
def update_academic(acad_id):
    """Update academic"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    academics = load_json(ACADEMICS_FILE)
    
    if acad_id not in academics:
        return jsonify({'success': False, 'message': 'Academic not found'}), 404
    
    data = request.json
    acad = academics[acad_id]
    
    # Update fields
    if 'name' in data:
        acad['name'] = sanitize_input(data['name'].strip())
    if 'department' in data:
        acad['department'] = sanitize_input(data['department'].strip())
    if 'qualification' in data:
        acad['qualification'] = sanitize_input(data['qualification'].strip())
    if 'experience' in data:
        try:
            exp_num = int(data['experience'])
            if 0 <= exp_num <= 60:
                acad['experience'] = str(exp_num)
        except:
            pass
    if 'email' in data:
        email = data['email'].strip().lower()
        if validate_email(email):
            # Check duplicate
            for aid, a in academics.items():
                if aid != acad_id and a.get('email', '').lower() == email:
                    return jsonify({'success': False, 'message': 'Email already exists'}), 400
            acad['email'] = email
    if 'phone' in data:
        phone = data['phone'].strip()
        if validate_phone(phone):
            acad['phone'] = phone
    
    acad['updated_at'] = get_current_timestamp()
    save_json(ACADEMICS_FILE, academics)
    
    Logger.log_activity(request.session_data['username'], 'ACADEMIC_UPDATED', 'Academic', acad_id, f'Academic {acad["name"]} updated', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Academic updated successfully',
        'academic': acad
    })

@app.route('/api/academics/<acad_id>', methods=['DELETE'])
@require_auth
def delete_academic(acad_id):
    """Delete academic (soft delete)"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    academics = load_json(ACADEMICS_FILE)
    
    if acad_id not in academics:
        return jsonify({'success': False, 'message': 'Academic not found'}), 404
    
    academics[acad_id]['status'] = 'inactive'
    academics[acad_id]['updated_at'] = get_current_timestamp()
    
    save_json(ACADEMICS_FILE, academics)
    Logger.log_activity(request.session_data['username'], 'ACADEMIC_DELETED', 'Academic', acad_id, f'Academic {academics[acad_id]["name"]} deleted', 'success')
    
    return jsonify({'success': True, 'message': 'Academic deleted successfully'})

# Student Management APIs
@app.route('/api/students/list', methods=['GET'])
@require_auth
def list_students():
    """List all students"""
    students = load_json(STUDENTS_FILE)
    student_list = []
    
    for stu_id, stu_data in students.items():
        student_list.append({
            'id': stu_id,
            'student_name': stu_data.get('student_name'),
            'login_id': stu_data.get('login_id'),
            'section': stu_data.get('section'),
            'first_name': stu_data.get('first_name'),
            'last_name': stu_data.get('last_name'),
            'dob': stu_data.get('dob'),
            'gender': stu_data.get('gender'),
            'email': stu_data.get('email'),
            'status': stu_data.get('status', 'active'),
            'registration_id': stu_data.get('registration_id')
        })
    
    return jsonify({'success': True, 'data': student_list, 'total': len(student_list)})

@app.route('/api/students/add', methods=['POST'])
@require_auth
def add_student():
    """Add new student - only name and section required"""
    # Allow Admin and Faculty to add students
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    student_name = data.get('student_name', '').strip()
    section = data.get('section', '').strip()
    
    # Validation - only name and section required
    if not student_name or not section:
        return jsonify({'success': False, 'message': 'Student name and section are required'}), 400
    
    students = load_json(STUDENTS_FILE)
    users = load_json(USERS_FILE)
    
    # Auto-generate username
    existing_usernames = set(users.keys())
    username = generate_username(student_name, existing_usernames)
    
    stu_id = generate_id('STU')
    students[stu_id] = {
        "id": stu_id,
        "student_name": sanitize_input(student_name),
        "login_id": username,
        "section": section.upper(),
        "first_name": "",
        "last_name": "",
        "dob": "",
        "gender": "",
        "father_name": "",
        "mother_name": "",
        "email": "",
        "phone": "",
        "status": "active",
        "registration_id": generate_registration_id(),
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
        "created_by": request.session_data['username']
    }
    
    # Create user account for student
    users[username] = {
        "id": stu_id,
        "username": username,
        "password": hash_password(DEFAULT_STUDENT_PASSWORD),
        "password_encrypted": encrypt_password(DEFAULT_STUDENT_PASSWORD),
        "password_plain": DEFAULT_STUDENT_PASSWORD,
        "role": "Student",
        "registration_id": students[stu_id]['registration_id'],
        "status": "active",
        "profile_completed": False,
        "profile": {},
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
        "created_by": request.session_data['username'],
        "last_login": None,
        "login_count": 0,
        "failed_login_attempts": 0,
        "account_locked": False,
        "locked_until": None
    }
    
    save_json(STUDENTS_FILE, students)
    save_json(USERS_FILE, users)
    
    Logger.log_activity(request.session_data['username'], 'STUDENT_ADDED', 'Student', stu_id, f'Student {student_name} added', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Student added successfully',
        'student': {
            'id': stu_id,
            'student_name': student_name,
            'username': username,
            'section': section.upper(),
            'registration_id': students[stu_id]['registration_id'],
            'default_password': DEFAULT_STUDENT_PASSWORD
        }
    }), 201

@app.route('/api/students/<stu_id>/view', methods=['GET'])
@require_auth
def view_student(stu_id):
    """View student details"""
    # Allow Admin and Faculty (Academics) to view student details
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    students = load_json(STUDENTS_FILE)
    users = load_json(USERS_FILE)
    
    if stu_id not in students:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    student = students[stu_id].copy()
    
    # Find associated user
    username = student.get('login_id')
    user_data = None
    if username and username in users:
        user_data = users[username]
    
    student['username'] = username
    if user_data:
        student['user_profile'] = user_data.get('profile', {})
        student['profile_completed'] = user_data.get('profile_completed', False)
        student['registration_id'] = user_data.get('registration_id')
        student['profile_photo_url'] = get_profile_photo_url(user_data)
        # Admin can see password, academics cannot
        role = request.session_data['role']
        if role == 'Admin':
            student['password'] = user_data.get('password')
            student['password_plain'] = user_data.get('password_plain') or user_data.get('password_encrypted')
    
    return jsonify({'success': True, 'student': student})

@app.route('/api/students/<stu_id>', methods=['DELETE'])
@require_auth
def delete_student(stu_id):
    """Delete student (Admin and Academics can delete)"""
    # Allow Admin and Faculty (Academics) to delete students
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    students = load_json(STUDENTS_FILE)
    users = load_json(USERS_FILE)
    
    if stu_id not in students:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    student = students[stu_id]
    username = student.get('login_id')
    
    # Soft delete student
    students[stu_id]['status'] = 'inactive'
    students[stu_id]['updated_at'] = get_current_timestamp()
    
    # Deactivate user account
    if username and username in users:
        users[username]['status'] = 'inactive'
        users[username]['updated_at'] = get_current_timestamp()
    
    save_json(STUDENTS_FILE, students)
    save_json(USERS_FILE, users)
    
    Logger.log_activity(request.session_data['username'], 'STUDENT_DELETED', 'Student', stu_id, f'Student {student["student_name"]} deleted', 'success')
    
    return jsonify({'success': True, 'message': 'Student deleted successfully'})

@app.route('/api/students/<stu_id>', methods=['PUT'])
@require_auth
def update_student(stu_id):
    """Update student details (Admin and Faculty can update)"""
    # Allow Admin and Faculty (Academics) to update students
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    students = load_json(STUDENTS_FILE)
    
    if stu_id not in students:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    student = students[stu_id]
    
    # Update fields if provided
    if 'student_name' in data:
        student['student_name'] = sanitize_input(data['student_name'].strip())
    if 'section' in data:
        student['section'] = data['section'].strip().upper()
    if 'first_name' in data:
        student['first_name'] = sanitize_input(data['first_name'].strip())
    if 'last_name' in data:
        student['last_name'] = sanitize_input(data['last_name'].strip())
    if 'email' in data:
        email = data['email'].strip().lower()
        if email and validate_email(email):
            student['email'] = email
    if 'phone' in data:
        phone = data['phone'].strip()
        if phone and validate_phone(phone):
            student['phone'] = phone
    if 'dob' in data:
        student['dob'] = data['dob'].strip()
    if 'gender' in data:
        student['gender'] = data['gender'].strip()
    if 'father_name' in data:
        student['father_name'] = sanitize_input(data['father_name'].strip())
    if 'mother_name' in data:
        student['mother_name'] = sanitize_input(data['mother_name'].strip())
    
    student['updated_at'] = get_current_timestamp()
    save_json(STUDENTS_FILE, students)
    
    Logger.log_activity(request.session_data['username'], 'STUDENT_UPDATED', 'Student', stu_id, f'Student {student["student_name"]} updated', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Student updated successfully',
        'student': student
    })

# Event Management APIs
@app.route('/api/events/list', methods=['GET'])
@require_auth
def list_events():
    """List all events"""
    events = load_json(EVENTS_FILE)
    event_list = []
    
    for evt_id, evt_data in events.items():
        event_list.append({
            'id': evt_id,
            'title': evt_data.get('title'),
            'date': evt_data.get('date'),
            'time': evt_data.get('time'),
            'time_12': evt_data.get('time_12'),
            'organizer_name': evt_data.get('organizer_name'),
            'club_name': evt_data.get('club_name'),
            'chief_guest': evt_data.get('chief_guest'),
            'description': evt_data.get('description'),
            'capacity': evt_data.get('capacity'),
            'registered_count': evt_data.get('registered_count', 0),
            'venue': evt_data.get('venue'),
            'status': evt_data.get('status', 'active')
        })
    
    # Sort by date
    event_list.sort(key=lambda x: x.get('date', ''))
    
    return jsonify({'success': True, 'data': event_list, 'total': len(event_list)})

@app.route('/api/events/add', methods=['POST'])
@require_auth
def add_event():
    """Add new event"""
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    title = data.get('title', '').strip()
    date = data.get('date', '').strip()
    time = data.get('time', '').strip()
    organizer_name = data.get('organizer_name', '').strip()
    club_name = data.get('club_name', '').strip()
    capacity = data.get('capacity', '').strip()
    
    # Validation
    if not all([title, date, time, organizer_name, club_name, capacity]):
        return jsonify({'success': False, 'message': 'All required fields must be provided'}), 400
    
    try:
        cap_num = int(capacity)
        if cap_num < 1 or cap_num > 10000:
            return jsonify({'success': False, 'message': 'Capacity must be between 1 and 10000'}), 400
    except:
        return jsonify({'success': False, 'message': 'Capacity must be a number'}), 400
    
    # Validate date (must be today or future)
    try:
        event_date = datetime.strptime(date, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if event_date < today:
            return jsonify({'success': False, 'message': 'Event date must be today or in the future'}), 400
    except:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    
    # Convert time to 12-hour format
    time_12 = convert_24_to_12(time) if ':' in time and ('AM' not in time and 'PM' not in time) else time
    
    events = load_json(EVENTS_FILE)
    evt_id = generate_id('EVT')
    
    events[evt_id] = {
        "id": evt_id,
        "title": sanitize_input(title),
        "date": date,
        "time": convert_12_to_24(time_12) if 'AM' in time_12 or 'PM' in time_12 else time,
        "time_12": time_12,
        "organizer_name": sanitize_input(organizer_name),
        "club_name": sanitize_input(club_name),
        "chief_guest": sanitize_input(data.get('chief_guest', '').strip()),
        "description": sanitize_input(data.get('description', '').strip()),
        "capacity": cap_num,
        "registered_count": 0,
        "registrations": [],  # List of registered users
        "venue": sanitize_input(data.get('venue', '').strip()),
        "status": "active",
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
        "created_by": request.session_data['username']
    }
    
    save_json(EVENTS_FILE, events)
    Logger.log_activity(request.session_data['username'], 'EVENT_ADDED', 'Event', evt_id, f'Event {title} added', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Event created successfully',
        'event': {
            'id': evt_id,
            'title': title,
            'time_12': time_12
        }
    }), 201

@app.route('/api/events/<evt_id>/register', methods=['POST'])
@require_auth
def register_event(evt_id):
    """Register for event"""
    events = load_json(EVENTS_FILE)
    students = load_json(STUDENTS_FILE)
    users = load_json(USERS_FILE)
    
    if evt_id not in events:
        return jsonify({'success': False, 'message': 'Event not found'}), 404
    
    event = events[evt_id]
    username = request.session_data['username']
    user = users.get(username, {})
    
    # Only students can register
    if user.get('role') != 'Student':
        return jsonify({'success': False, 'message': 'Only students can register for events'}), 403
    
    # Check if already registered
    if 'registrations' not in event:
        event['registrations'] = []
    
    for reg in event['registrations']:
        if reg.get('username') == username:
            return jsonify({'success': False, 'message': 'Already registered for this event'}), 400
    
    # Check capacity
    if len(event['registrations']) >= event.get('capacity', 0):
        return jsonify({'success': False, 'message': 'Event is full'}), 400
    
    # Get student info
    student_info = None
    for stu_id, stu_data in students.items():
        if stu_data.get('login_id') == username:
            student_info = stu_data
            break
    
    # Add registration
    registration = {
        'username': username,
        'student_name': student_info.get('student_name', username) if student_info else username,
        'section': student_info.get('section', '') if student_info else '',
        'registered_at': get_current_timestamp()
    }
    
    event['registrations'].append(registration)
    event['registered_count'] = len(event['registrations'])
    event['updated_at'] = get_current_timestamp()
    
    save_json(EVENTS_FILE, events)
    Logger.log_activity(username, 'EVENT_REGISTERED', 'Event', evt_id, f'Registered for event {event["title"]}', 'success')
    
    return jsonify({'success': True, 'message': 'Successfully registered for event'})

@app.route('/api/events/<evt_id>/registrations', methods=['GET'])
@require_auth
def get_event_registrations(evt_id):
    """Get event registrations"""
    events = load_json(EVENTS_FILE)
    
    if evt_id not in events:
        return jsonify({'success': False, 'message': 'Event not found'}), 404
    
    event = events[evt_id]
    registrations = event.get('registrations', [])
    
    return jsonify({
        'success': True,
        'registrations': registrations,
        'total': len(registrations),
        'capacity': event.get('capacity', 0)
    })

# Timetable Management APIs
@app.route('/api/timetable/list', methods=['GET'])
@require_auth
def list_timetable():
    """List timetable entries"""
    timetable = load_json(TIMETABLE_FILE)
    
    # Filter expired entries
    for day in DAYS_OF_WEEK:
        if day in timetable:
            timetable[day] = [entry for entry in timetable[day] if not is_expired_timetable_entry(entry)]
    
    save_json(TIMETABLE_FILE, timetable)
    
    return jsonify({'success': True, 'data': timetable})

@app.route('/api/timetable/add', methods=['POST'])
@require_auth
def add_timetable_entry():
    """Add timetable entry with clash detection and section support"""
    # Allow Admin and Faculty (Academics) to add timetable entries
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    day = data.get('day', '').strip()
    start_time = data.get('start_time', '').strip()
    end_time = data.get('end_time', '').strip()
    class_name = data.get('class_name', '').strip()
    faculty_name = data.get('faculty_name', '').strip()
    subject = data.get('subject', '').strip()
    section = data.get('section', '').strip().upper()
    
    # Validation
    if not all([day, start_time, end_time, class_name, faculty_name, subject, section]):
        return jsonify({'success': False, 'message': 'All required fields including section must be provided'}), 400
    
    if day not in DAYS_OF_WEEK:
        return jsonify({'success': False, 'message': 'Invalid day'}), 400
    
    # Convert to 12-hour format if needed
    start_time_12 = convert_24_to_12(start_time) if ':' in start_time and ('AM' not in start_time and 'PM' not in start_time) else start_time
    end_time_12 = convert_24_to_12(end_time) if ':' in end_time and ('AM' not in end_time and 'PM' not in end_time) else end_time
    
    # Validate end time > start time
    start_24 = convert_12_to_24(start_time_12) if 'AM' in start_time_12 or 'PM' in start_time_12 else start_time
    end_24 = convert_12_to_24(end_time_12) if 'AM' in end_time_12 or 'PM' in end_time_12 else end_time
    
    try:
        start_hour, start_min = map(int, start_24.split(':'))
        end_hour, end_min = map(int, end_24.split(':'))
        start_total = start_hour * 60 + start_min
        end_total = end_hour * 60 + end_min
        
        if end_total <= start_total:
            return jsonify({'success': False, 'message': 'End time must be after start time'}), 400
    except:
        return jsonify({'success': False, 'message': 'Invalid time format'}), 400
    
    timetable = load_json(TIMETABLE_FILE)
    
    # Check for time clash (only for same section)
    clash = check_time_clash(day, start_time_12, end_time_12, timetable, section=section)
    if clash:
        return jsonify({
            'success': False,
            'message': f"Time clash detected! {clash['conflicting_class']} is scheduled from {clash['conflicting_time']}",
            'error_code': 'TT_CLASH_001',
            'conflicting_class': clash['conflicting_class'],
            'conflicting_time': clash['conflicting_time']
        }), 409
    
    entry_id = generate_id('TT')
    entry = {
        "id": entry_id,
        "day": day,
        "section": section,
        "start_time": start_24,
        "start_time_12": start_time_12,
        "end_time": end_24,
        "end_time_12": end_time_12,
        "class_name": sanitize_input(class_name),
        "faculty_name": sanitize_input(faculty_name),
        "subject": sanitize_input(subject),
        "topic_covered": sanitize_input(data.get('topic_covered', '').strip()),
        "classroom": sanitize_input(data.get('classroom', '').strip()),
        "building": sanitize_input(data.get('building', '').strip()),
        "created_at": get_current_timestamp(),
        "created_by": request.session_data['username']
    }
    
    if day not in timetable:
        timetable[day] = []
    timetable[day].append(entry)
    
    save_json(TIMETABLE_FILE, timetable)
    Logger.log_activity(request.session_data['username'], 'TIMETABLE_ADDED', 'Timetable', entry_id, f'Class {class_name} added to {day} for section {section}', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Class added successfully',
        'timetable_entry': {
            'id': entry_id,
            'day': day,
            'section': section,
            'start_time_12': start_time_12,
            'end_time_12': end_time_12
        }
    }), 201

@app.route('/api/timetable/<entry_id>', methods=['DELETE'])
@require_auth
def delete_timetable_entry(entry_id):
    """Delete timetable entry"""
    # Allow Admin and Faculty (Academics) to delete timetable entries
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    timetable = load_json(TIMETABLE_FILE)
    
    for day in DAYS_OF_WEEK:
        if day in timetable:
            for i, entry in enumerate(timetable[day]):
                if entry.get('id') == entry_id:
                    class_name = entry.get('class_name')
                    timetable[day].pop(i)
                    save_json(TIMETABLE_FILE, timetable)
                    Logger.log_activity(request.session_data['username'], 'TIMETABLE_DELETED', 'Timetable', entry_id, f'Class {class_name} deleted', 'success')
                    return jsonify({'success': True, 'message': 'Class deleted successfully'})
    
    return jsonify({'success': False, 'message': 'Timetable entry not found'}), 404


@app.route('/api/timetable/<entry_id>', methods=['PUT'])
@require_auth
def update_timetable_entry(entry_id):
    """Update timetable entry (Admin and Faculty)"""
    # Allow Admin and Faculty (Academics) to update timetable entries
    if request.session_data['role'] not in ['Admin', 'Faculty']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.json or {}

    timetable = load_json(TIMETABLE_FILE)

    # Find existing entry
    found = None
    found_day = None
    for day in DAYS_OF_WEEK:
        if day in timetable:
            for entry in timetable[day]:
                if entry.get('id') == entry_id:
                    found = entry
                    found_day = day
                    break
        if found:
            break

    if not found:
        return jsonify({'success': False, 'message': 'Timetable entry not found'}), 404

    # Prepare updated values (fall back to existing)
    day = data.get('day', found.get('day', found_day)).strip()
    start_time = data.get('start_time', found.get('start_time', '')).strip()
    end_time = data.get('end_time', found.get('end_time', '')).strip()
    class_name = data.get('class_name', found.get('class_name', '')).strip()
    faculty_name = data.get('faculty_name', found.get('faculty_name', '')).strip()
    subject = data.get('subject', found.get('subject', '')).strip()
    section = data.get('section', found.get('section', '')).strip().upper()

    # Validation
    if not all([day, start_time, end_time, class_name, faculty_name, subject, section]):
        return jsonify({'success': False, 'message': 'All required fields including section must be provided'}), 400

    if day not in DAYS_OF_WEEK:
        return jsonify({'success': False, 'message': 'Invalid day'}), 400

    # Convert times
    start_time_12 = convert_24_to_12(start_time) if ':' in start_time and ('AM' not in start_time and 'PM' not in start_time) else start_time
    end_time_12 = convert_24_to_12(end_time) if ':' in end_time and ('AM' not in end_time and 'PM' not in end_time) else end_time

    # Validate end time > start time
    start_24 = convert_12_to_24(start_time_12) if 'AM' in start_time_12 or 'PM' in start_time_12 else start_time
    end_24 = convert_12_to_24(end_time_12) if 'AM' in end_time_12 or 'PM' in end_time_12 else end_time

    try:
        start_hour, start_min = map(int, start_24.split(':'))
        end_hour, end_min = map(int, end_24.split(':'))
        start_total = start_hour * 60 + start_min
        end_total = end_hour * 60 + end_min

        if end_total <= start_total:
            return jsonify({'success': False, 'message': 'End time must be after start time'}), 400
    except:
        return jsonify({'success': False, 'message': 'Invalid time format'}), 400

    # Check for time clash (exclude current entry by id)
    clash = check_time_clash(day, start_time_12, end_time_12, timetable, exclude_id=entry_id, section=section)
    if clash:
        return jsonify({
            'success': False,
            'message': f"Time clash detected! {clash['conflicting_class']} is scheduled from {clash['conflicting_time']}",
            'error_code': 'TT_CLASH_001',
            'conflicting_class': clash['conflicting_class'],
            'conflicting_time': clash['conflicting_time']
        }), 409

    # Apply updates
    found['day'] = day
    found['section'] = section
    found['start_time'] = start_24
    found['start_time_12'] = start_time_12
    found['end_time'] = end_24
    found['end_time_12'] = end_time_12
    found['class_name'] = sanitize_input(class_name)
    found['faculty_name'] = sanitize_input(faculty_name)
    found['subject'] = sanitize_input(subject)
    found['topic_covered'] = sanitize_input(data.get('topic_covered', found.get('topic_covered', '')).strip())
    found['classroom'] = sanitize_input(data.get('classroom', found.get('classroom', '')).strip())
    found['building'] = sanitize_input(data.get('building', found.get('building', '')).strip())
    found['updated_at'] = get_current_timestamp()

    # If day changed, move entry between day lists
    if found_day != day:
        # remove from old day
        timetable[found_day] = [e for e in timetable.get(found_day, []) if e.get('id') != entry_id]
        if day not in timetable:
            timetable[day] = []
        timetable[day].append(found)

    save_json(TIMETABLE_FILE, timetable)
    Logger.log_activity(request.session_data['username'], 'TIMETABLE_UPDATED', 'Timetable', entry_id, f'Class {found.get("class_name")} updated', 'success')

    return jsonify({'success': True, 'message': 'Timetable entry updated', 'timetable_entry': found})

# Activity Log APIs
@app.route('/api/activities/list', methods=['GET'])
@require_auth
def list_activities():
    """List activity logs (excluding login/logout/theme changes)"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    limit = request.args.get('limit', 100, type=int)
    activities = Logger.get_activities(limit=limit)
    
    # Filter out login, logout, and theme changes
    filtered_activities = [
        a for a in activities 
        if a.get('action') not in ['USER_LOGIN', 'USER_LOGOUT', 'THEME_CHANGED', 'LOGIN_ATTEMPT']
    ]
    
    return jsonify({'success': True, 'data': filtered_activities, 'total': len(filtered_activities)})

# Dashboard APIs
@app.route('/api/dashboard/stats', methods=['GET'])
@require_auth
def dashboard_stats():
    """Get dashboard statistics"""
    role = request.session_data['role']
    
    users = load_json(USERS_FILE)
    academics = load_json(ACADEMICS_FILE)
    students = load_json(STUDENTS_FILE)
    events = load_json(EVENTS_FILE)
    timetable = load_json(TIMETABLE_FILE)
    
    stats = {
        'total_users': len(users),
        'total_academics': len([a for a in academics.values() if a.get('status') == 'active']),
        'total_students': len([s for s in students.values() if s.get('status') == 'active']),
        'total_events': len([e for e in events.values() if e.get('status') == 'active']),
        'active_sessions': len(active_sessions)
    }
    
    # Today's classes
    today = datetime.now().strftime("%A")
    today_classes = []
    if today in timetable:
        for entry in timetable[today]:
            if not is_expired_timetable_entry(entry):
                today_classes.append(entry)
    stats['today_classes'] = len(today_classes)
    
    return jsonify({'success': True, 'stats': stats})

# Data Management APIs (Admin Only)
@app.route('/api/data/clear', methods=['POST'])
@require_auth
def clear_data():
    """Clear data - all or partial (Admin only)"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    clear_type = data.get('type', 'partial')  # 'all' or 'partial'
    sections = data.get('sections', [])  # List of sections to clear
    
    cleared = []
    
    if clear_type == 'all':
        # Clear all data except admin user
        academics = {}
        save_json(ACADEMICS_FILE, academics)
        cleared.append('academics')
        
        students = {}
        save_json(STUDENTS_FILE, students)
        cleared.append('students')
        
        events = {}
        save_json(EVENTS_FILE, events)
        cleared.append('events')
        
        timetable = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": []
        }
        save_json(TIMETABLE_FILE, timetable)
        cleared.append('timetable')
        
        activities = []
        save_json(ACTIVITIES_FILE, activities)
        cleared.append('activities')
        
        # Clear users except admin
        users = load_json(USERS_FILE)
        admin_user = users.get('ADMIN', {})
        users = {'ADMIN': admin_user}
        save_json(USERS_FILE, users)
        cleared.append('users')
        
        Logger.log_activity(request.session_data['username'], 'DATA_CLEARED', 'System', None, 'All data cleared', 'success')
        
    elif clear_type == 'partial':
        # Clear partial data based on sections
        if not sections:
            return jsonify({'success': False, 'message': 'Sections required for partial clear'}), 400
        
        # Clear students by section
        students = load_json(STUDENTS_FILE)
        students_to_remove = []
        for stu_id, stu_data in students.items():
            if stu_data.get('section', '').upper() in [s.upper() for s in sections]:
                students_to_remove.append(stu_id)
                # Also remove user account
                login_id = stu_data.get('login_id')
                if login_id:
                    users = load_json(USERS_FILE)
                    if login_id in users:
                        del users[login_id]
                    save_json(USERS_FILE, users)
        
        for stu_id in students_to_remove:
            del students[stu_id]
        save_json(STUDENTS_FILE, students)
        if students_to_remove:
            cleared.append(f'students (sections: {", ".join(sections)})')
        
        # Clear timetable entries by section
        timetable = load_json(TIMETABLE_FILE)
        for day in DAYS_OF_WEEK:
            if day in timetable:
                timetable[day] = [e for e in timetable[day] if e.get('section', '').upper() not in [s.upper() for s in sections]]
        save_json(TIMETABLE_FILE, timetable)
        cleared.append(f'timetable (sections: {", ".join(sections)})')
        
        Logger.log_activity(request.session_data['username'], 'DATA_CLEARED', 'System', None, f'Partial data cleared for sections: {", ".join(sections)}', 'success')
    
    return jsonify({
        'success': True,
        'message': f'Data cleared successfully',
        'cleared': cleared
    })

# Theme Management APIs
@app.route('/api/user/theme', methods=['GET', 'PUT'])
@require_auth
def manage_theme():
    """Get or update user theme preference"""
    username = request.session_data['username']
    users = load_json(USERS_FILE)
    
    if username not in users:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    if request.method == 'GET':
        theme = users[username].get('theme', 'light')
        return jsonify({'success': True, 'theme': theme})
    
    # PUT - Update theme
    data = request.json
    theme = data.get('theme', 'light')
    
    if theme not in ['light', 'dark']:
        return jsonify({'success': False, 'message': 'Invalid theme. Use "light" or "dark"'}), 400
    
    users[username]['theme'] = theme
    users[username]['updated_at'] = get_current_timestamp()
    save_json(USERS_FILE, users)
    
    # Don't log theme changes
    # Logger.log_activity(username, 'THEME_CHANGED', 'User', username, f'Theme changed to {theme}', 'success')
    
    return jsonify({'success': True, 'message': 'Theme updated successfully', 'theme': theme})

# Export APIs (CSV/PDF)
@app.route('/api/export/<data_type>', methods=['GET'])
@require_auth
def export_data(data_type):
    """Export data as CSV or PDF"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    export_format = request.args.get('format', 'csv')  # csv or pdf
    
    if data_type == 'academics':
        academics = load_json(ACADEMICS_FILE)
        data = []
        for acad_id, acad_data in academics.items():
            data.append({
                'ID': acad_id,
                'Name': acad_data.get('name', ''),
                'Username': acad_data.get('username', ''),
                'Department': acad_data.get('department', ''),
                'Qualification': acad_data.get('qualification', ''),
                'Experience': acad_data.get('experience', ''),
                'Email': acad_data.get('email', ''),
                'Phone': acad_data.get('phone', ''),
                'Status': acad_data.get('status', ''),
                'Registration ID': acad_data.get('registration_id', '')
            })
        filename = 'academics'
        
    elif data_type == 'students':
        students = load_json(STUDENTS_FILE)
        data = []
        for stu_id, stu_data in students.items():
            data.append({
                'ID': stu_id,
                'Student Name': stu_data.get('student_name', ''),
                'Username': stu_data.get('login_id', ''),
                'Section': stu_data.get('section', ''),
                'First Name': stu_data.get('first_name', ''),
                'Last Name': stu_data.get('last_name', ''),
                'DOB': stu_data.get('dob', ''),
                'Gender': stu_data.get('gender', ''),
                'Email': stu_data.get('email', ''),
                'Phone': stu_data.get('phone', ''),
                'Father Name': stu_data.get('father_name', ''),
                'Mother Name': stu_data.get('mother_name', ''),
                'Status': stu_data.get('status', ''),
                'Registration ID': stu_data.get('registration_id', '')
            })
        filename = 'students'
        
    elif data_type == 'timetable':
        timetable = load_json(TIMETABLE_FILE)
        data = []
        for day in DAYS_OF_WEEK:
            if day in timetable:
                for entry in timetable[day]:
                    data.append({
                        'Day': entry.get('day', ''),
                        'Section': entry.get('section', ''),
                        'Start Time': entry.get('start_time_12', ''),
                        'End Time': entry.get('end_time_12', ''),
                        'Class Name': entry.get('class_name', ''),
                        'Faculty': entry.get('faculty_name', ''),
                        'Subject': entry.get('subject', ''),
                        'Topic': entry.get('topic_covered', ''),
                        'Classroom': entry.get('classroom', ''),
                        'Building': entry.get('building', '')
                    })
        filename = 'timetable'
        
    elif data_type == 'activities':
        activities = Logger.get_activities(limit=10000)
        # Filter out login/logout/theme
        activities = [a for a in activities if a.get('action') not in ['USER_LOGIN', 'USER_LOGOUT', 'THEME_CHANGED', 'LOGIN_ATTEMPT']]
        data = []
        for act in activities:
            data.append({
                'Timestamp': act.get('timestamp', ''),
                'User': act.get('user', ''),
                'Action': act.get('action', ''),
                'Description': act.get('description', ''),
                'Status': act.get('status', ''),
                'Entity Type': act.get('entity_type', ''),
                'Entity ID': act.get('entity_id', '')
            })
        filename = 'activities'
        
    elif data_type == 'users':
        users = load_json(USERS_FILE)
        data = []
        for username, user_data in users.items():
            data.append({
                'Username': username,
                'Role': user_data.get('role', ''),
                'Status': user_data.get('status', ''),
                'Email': user_data.get('profile', {}).get('email', ''),
                'Profile Completed': 'Yes' if user_data.get('profile_completed', False) else 'No',
                'Registration ID': user_data.get('registration_id', ''),
                'Last Login': user_data.get('last_login', ''),
                'Login Count': user_data.get('login_count', 0)
            })
        filename = 'users'
        
    else:
        return jsonify({'success': False, 'message': 'Invalid data type'}), 400
    
    if export_format == 'csv':
        # Generate CSV
        import csv
        import io
        from flask import Response
        
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        return response
    
    elif export_format == 'pdf':
        # For PDF, return JSON data (frontend will handle PDF generation)
        return jsonify({
            'success': True,
            'data': data,
            'filename': filename,
            'format': 'pdf'
        })
    
    return jsonify({'success': False, 'message': 'Invalid format'}), 400

# Backup API
@app.route('/api/backup/create', methods=['POST'])
@require_auth
def create_backup():
    """Create backup of all data"""
    if request.session_data['role'] != 'Admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    import shutil
    from datetime import datetime
    
    backup_dir = os.path.join(DATA_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = os.path.join(backup_dir, f'backup_{timestamp}')
    os.makedirs(backup_folder, exist_ok=True)
    
    # Copy all JSON files
    files_to_backup = [
        ('users.json', USERS_FILE),
        ('academics.json', ACADEMICS_FILE),
        ('students.json', STUDENTS_FILE),
        ('events.json', EVENTS_FILE),
        ('timetable.json', TIMETABLE_FILE),
        ('activities.json', ACTIVITIES_FILE)
    ]
    
    backed_up = []
    for filename, filepath in files_to_backup:
        if os.path.exists(filepath):
            shutil.copy2(filepath, os.path.join(backup_folder, filename))
            backed_up.append(filename)
    
    Logger.log_activity(request.session_data['username'], 'BACKUP_CREATED', 'System', None, f'Backup created: backup_{timestamp}', 'success')
    
    return jsonify({
        'success': True,
        'message': 'Backup created successfully',
        'backup_folder': f'backup_{timestamp}',
        'files': backed_up
    })

# Global error handler for unexpected exceptions
@app.errorhandler(Exception)
def handle_exception(error):
    """Catch all unhandled exceptions and return JSON error response"""
    import traceback
    error_msg = str(error)
    error_trace = traceback.format_exc()
    
    Logger.log_activity('SYSTEM', 'ERROR_EXCEPTION', 'System', None, f'Unhandled exception: {error_msg}', 'error')
    print(f"UNHANDLED EXCEPTION:\n{error_trace}")
    
    return jsonify({
        'success': False,
        'message': 'An unexpected error occurred. Please try again.',
        'error': error_msg if app.debug else 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Run server bound to localhost only for security (no world-wide access)
    print("\n" + "="*60)
    print("EduPortal Server Starting (local-only)...")
    print("="*60)
    print(f"Local access: http://127.0.0.1:5000 or http://localhost:5000")
    print("Server is NOT exposed to other machines.")
    print("="*60 + "\n")
    # Bind to 127.0.0.1 to prevent external network access
    app.run(debug=True, host='127.0.0.1', port=5000)

