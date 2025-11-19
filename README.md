
# EduPortal

EduPortal is a Flask-based educational management system that consolidates day-to-day academic operations—user administration, faculty and student records, timetable scheduling, and event coordination—behind a role-aware dashboard. It ships with a lightweight JSON persistence layer for quick local deployments and a CORS-enabled API for pairing with modern frontend stacks.

## Highlights
- Role-scoped dashboards for Admin, Faculty, and Student personas
- Session tokens with inactivity timeout plus account lockout after repeated failures
- Automated username/ID generation and default credential workflows
- Timetable clash detection with section awareness and time-format conversions
- Event registration with capacity tracking and student auto-fill
- JSON data backup-on-write and activity audit trail capped at `MAX_ACTIVITY_LOGS`
- DOB-verified self-service password resets, profile photo uploads, and admin visibility into plaintext credentials and avatar gallery
- CLI tooling to regenerate full documentation (`create_documentation.py`)

## Tech Stack
- Backend: Flask 3.1, Python 3.7+
- Frontend assets: HTML/Jinja templates, vanilla JS (`backend/static/js/main.js`), CSS (`backend/static/css/style.css`)
- Storage: Structured JSON files in `backend/data/` (with `.backup` snapshots)
- Cross-origin: `flask-cors` for front/back separation

## System Requirements
- **Software**: Python 3.7+, pip, modern browser (Chrome/Firefox/Edge/Safari)
- **Python deps**: `pip install -r backend/requirements.txt` (Flask, Flask-CORS, python-docx, etc.)
- **OS**: Windows, macOS, or any Linux distro with write access to the repo folder
- **Hardware**: ≥2 GB RAM, ≥500 MB free disk, dual-core CPU or better

## Key Features
- Role-based dashboards with guarded navigation and session-aware API calls
- Faculty & student provisioning with automated username, registration ID, and default password assignment
- Timetable planner with section-based clash detection and automatic pruning of past sessions
- Event board supporting capacity filters and student self-registration
- Faculty dashboard permissions to add/edit students, create timetable entries, and spin up events directly from the side menu
- Complete profile workflow with strict validation (PII, dates, contact info)
- Login-page “Forgot Password” flow that verifies DOB (year-only) before issuing a reset across every role—no admin ticket needed
- Profile photo uploads with per-user previews, admin gallery visibility, and secure server-side storage
- Activity logger capped by `MAX_ACTIVITY_LOGS`, backup creation before each data write, and manual backup/export endpoints

## Repository Layout
```
backend/
  app.py                # Flask app + routes
  config.py             # Directories, security thresholds, defaults
  utils.py              # JSON I/O, auth helpers, validators, time utilities
  logger.py             # Activity/audit logging
  requirements.txt      # Python dependencies
  data/                 # JSON stores (users, academics, students, events, timetable, activities)
  static/               # CSS/JS/Imgs served by Flask
  templates/            # Login + dashboard shells
create_documentation.py # Generates full .docx documentation
EduPortal_Complete_Documentation.docx
README.md               # You are here
```

## Getting Started
1. **Clone & enter backend**
   ```bash
   git clone <repo-url>
   cd EduPortal/backend
   ```
2. **Create virtual environment (recommended)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate  # macOS/Linux
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run dev server**
   ```bash
   python app.py
   ```
5. **Open app**: http://localhost:5000 (login page redirects to dashboard post-authentication).

## Default Credentials
| Role    | Username | Password  | Notes                                   |
|---------|----------|-----------|-----------------------------------------|
| Admin   | `ADMIN`  | `admin123`| Auto-provisioned on first run           |
| Faculty | auto     | `acad123` | Created when Admin adds academic users  |
| Student | auto     | `stud123` | Created during student record creation  |

Non-admin users are forced to change default passwords after first login; profile completion is required (`/api/profile/update`).

## Configuration Cheatsheet (`backend/config.py`)
- `SESSION_TIMEOUT_MINUTES` / `SESSION_TIMEOUT_SECONDS`: inactivity window (default 15 min)
- `PASSWORD_MIN_LENGTH`, `MAX_LOGIN_ATTEMPTS`, `LOCKOUT_DURATION_MINUTES`: password policy & lockout rules
- `DEFAULT_*_PASSWORD`: bootstrap credentials per role
- `TIME_SLOTS`, `DAYS_OF_WEEK`: helper constants for timetable UI/forms
- `DATA_DIR`, `STATIC_DIR`, `TEMPLATES_DIR`: resolved at runtime; ensure write permissions for `data/`
- `PROFILE_PHOTOS_DIR`: static path where profile photo uploads are stored (`static/images/profiles`)

## Data Storage
All primary entities live in `backend/data/*.json`. Each save creates `<file>.backup` for quick recovery.

| File              | Purpose                                               |
|-------------------|--------------------------------------------------------|
| `users.json`      | Auth records, role, profile metadata, hashed + plaintext passwords, profile photo references |
| `academics.json`  | Faculty roster with departments & contact details      |
| `students.json`   | Student enrolments, sections, guardians, status        |
| `events.json`     | Campus events, capacity, registrations                 |
| `timetable.json`  | Day-by-day schedules grouped by section                |
| `activities.json` | Audit/history entries from `Logger`                    |

Backups: copy `<name>.json.backup` back over the original to restore.

## User Roles & Permissions
| Role    | Capabilities |
|---------|--------------|
| Admin   | Full CRUD on users/academics/students/events/timetable, data export, backups, activity log review, theme overrides, account unlocks, plaintext password visibility, cross-role photo oversight |
| Faculty | View/update own profile (email locked to admin-provided value), upload/update profile photos, change password, full student CRUD, create/delete timetable entries, create events |
| Student | View/update own profile, change password, read-only academics list/timetable/events, self-register for events within capacity |

## API Surface (selected)
| Domain          | Methods/Routes                             | Key Behaviours |
|-----------------|---------------------------------------------|----------------|
| Auth            | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/session-status`, `POST /api/auth/forgot-password` | Case-insensitive usernames, fixed-duration session tokens (no refresh reset), DOB-year verified password resets |
| Users           | `GET /api/users/list`, `POST /api/users/add`, `PUT /api/users/change-password`, `PUT /api/users/<username>/status` | Admin-only CRUD plus self-service password changes |
| Profiles        | `GET /api/profile/get`, `PUT /api/profile/update`, `POST /api/profile/photo` | Mandatory PII validation, faculty email lock, secure profile photo uploads |
| Academics       | `GET/POST/PUT/DELETE /api/academics/...`   | Auto-creates accompanying user accounts |
| Students        | `GET/POST/PUT/DELETE /api/students/...`    | Faculty/Admin restricted, syncs with `users.json` |
| Events          | `GET /api/events/list`, `POST /api/events/add`, `POST /api/events/<id>/register` | Admin/Faculty create events; students register with capacity enforcement |
| Timetable       | `GET /api/timetable/list`, `POST /api/timetable/add`, `PUT/DELETE /api/timetable/<id>` | Clash detection per section + 12/24h conversion |
| Data/Backup     | `POST /api/data/clear`, `POST /api/backup/create`, `GET /api/export/<type>` | Admin utilities for lifecycle management |

Each protected route uses the `@require_auth` decorator (`app.py`) to validate Bearer tokens or JSON `session_token`.

## Core Workflows
- **Authentication**: POST `/api/auth/login` → receive `session_token` → include as `Authorization: Bearer <token>` for all guarded routes; keep-alive with `/api/auth/session-status`.
- **User Management**: Admin hits `/api/users/add` with `{ "name": "...", "role": "Faculty|Student" }`; API auto-generates username, ID, default password and records metadata in `users.json`.
- **Profile Completion**: `/api/profile/update` requires personal info (first/last name, DOB, gender, marital status, parents, email); server sanitizes and validates before marking `profile_completed=True`. Faculty members submit the admin-provisioned email, which is locked against self-service edits.
- **Academics & Students**: Admin/Faculty can POST `/api/academics/add` or `/api/students/add` with minimal info; utils module creates matching user account and ties IDs for cross-reference. Faculty can now edit or soft-delete student records without escalating to Admin.
- **Timetable Planning**: Admin/Faculty POST `/api/timetable/add` specifying day, section, times, and subject; helper rejects overlaps and stores 24h/12h formats plus context (topic, classroom).
- **Events**: Admin or Faculty create events via `/api/events/add`; students register through `/api/events/<evt_id>/register`, which checks capacity and prevents duplicates.
- **Data Lifecycle**: `/api/data/clear` wipes selected sections or entire datasets, `/api/backup/create` snapshots JSON files, and `/api/export/<type>` streams CSVs for offline reporting.
- **Forgot Password**: From the login page, users select “Forgot Password?”, enter their username plus DOB year, and the backend (`POST /api/auth/forgot-password`) verifies the year before issuing a new password—no admin involvement required.
- **Profile Photos**: Any authenticated user can upload/update a profile picture via `/api/profile/photo`; Admin views every photo across the system from the Users table.

## Security & Resilience
- SHA-256 password hashing plus encrypted copy for admin viewing (`utils.hash_password/encrypt_password`)
- Forced password change tracking via `user['password_changed']`
- In-memory session store with fixed idle expiry (page refreshes no longer reset the timer), manual destruction at logout, and global `/api/auth/session-status`
- Lockout after `MAX_LOGIN_ATTEMPTS` with `LOCKOUT_DURATION_MINUTES` cool-down
- Input sanitization, email/phone validation, and future-date checks before persistence
- Timetable entries auto-pruned (expired classes) during fetch
- Activity logging via `Logger` for every critical CRUD + backup operation

## Maintenance & Ops Tips
- **Backups**: run `POST /api/backup/create` (Admin token) to snapshot all JSON stores under `backend/data/backups/backup_<timestamp>/`.
- **Docs**: regenerate comprehensive `.docx` guide by running `python create_documentation.py` from repo root.
- **Troubleshooting**:
  - Port conflicts → adjust `app.run(... port=XXXX)` in `app.py`
  - Session timeout feels short → increase `SESSION_TIMEOUT_MINUTES`
  - Corrupted JSON → restore from `.backup` or run `create_backup` before risky edits
  - Need logs → inspect `backend/data/activities.json` or `errors.log`

## Testing Checklist
- Verify login + dashboard access per role (Admin, Faculty, Student) using default creds then post-change credentials.
- Add sample academic/student/event/timetable entry and confirm they surface through respective list endpoints.
- Trigger account lock by failing login `MAX_LOGIN_ATTEMPTS` times; ensure unlock after `LOCKOUT_DURATION_MINUTES`.
- Register a student for an event to confirm capacity increments and duplicate prevention.
- Hit `/api/auth/session-status` after idle period to confirm timeout messaging.

## Documentation Assets
- `EduPortal_Complete_Documentation.docx`: high-level manual generated via `python create_documentation.py`.
- README (this file): operational quickstart + API primer; update alongside backend changes.
- Optionally export CSVs via `/api/export/<type>?format=csv` for external reporting packs.

## Contributing
1. Fork & branch (`git checkout -b feature/foo`)
2. Keep changes confined to relevant modules; avoid editing generated `.json` manually unless seeding data
3. Run lint/tests (if added) plus manual sanity tests via Postman or browser
4. Submit PR with screenshots or sample API payloads where helpful

---
Need a condensed reference? Use `EduPortal_Complete_Documentation.docx` for a narrative walkthrough or regenerate it after changes so teams stay aligned.


