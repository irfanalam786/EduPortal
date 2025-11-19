"""
Configuration file for EduPortal
Contains all constants, settings, and configuration values
"""

import os
from datetime import timedelta

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, 'images'), exist_ok=True)
PROFILE_PHOTOS_DIR = os.path.join(STATIC_DIR, 'images', 'profiles')
os.makedirs(PROFILE_PHOTOS_DIR, exist_ok=True)

# Data file paths
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
ACADEMICS_FILE = os.path.join(DATA_DIR, 'academics.json')
STUDENTS_FILE = os.path.join(DATA_DIR, 'students.json')
EVENTS_FILE = os.path.join(DATA_DIR, 'events.json')
TIMETABLE_FILE = os.path.join(DATA_DIR, 'timetable.json')
ACTIVITIES_FILE = os.path.join(DATA_DIR, 'activities.json')

# Session configuration
SESSION_TIMEOUT_MINUTES = 15
SESSION_TIMEOUT_SECONDS = SESSION_TIMEOUT_MINUTES * 60

# Security settings
PASSWORD_MIN_LENGTH = 6
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Default passwords
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ACADEMIC_PASSWORD = "acad123"
DEFAULT_STUDENT_PASSWORD = "stud123"

# Registration ID format: REG-[YYYYMMDDHHMMSS]-[XXXX]
REG_ID_PREFIX = "REG-"

# Time format
TIME_12_FORMAT = True
TIME_SLOTS = [
    "12:00 AM", "12:30 AM", "1:00 AM", "1:30 AM",
    "2:00 AM", "2:30 AM", "3:00 AM", "3:30 AM",
    "4:00 AM", "4:30 AM", "5:00 AM", "5:30 AM",
    "6:00 AM", "6:30 AM", "7:00 AM", "7:30 AM",
    "8:00 AM", "8:30 AM", "9:00 AM", "9:30 AM",
    "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
    "12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM",
    "2:00 PM", "2:30 PM", "3:00 PM", "3:30 PM",
    "4:00 PM", "4:30 PM", "5:00 PM", "5:30 PM",
    "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM",
    "8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM",
    "10:00 PM", "10:30 PM", "11:00 PM", "11:30 PM"
]

# Days of week
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Gender options
GENDER_OPTIONS = ["Male", "Female", "Other"]

# Marital status options
MARITAL_STATUS_OPTIONS = ["Single", "Married", "Divorced", "Widowed"]

# Pagination
DEFAULT_PAGE_SIZE = 25

# Activity log retention
MAX_ACTIVITY_LOGS = 10000

