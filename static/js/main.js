/**
 * EduPortal - Main JavaScript Application
 * Handles all frontend functionality including session management, API calls, and page navigation
 */

const App = {
    sessionToken: null,
    user: null,
    sessionTimer: null,
    sessionCountdown: null,
    remainingSeconds: 900, // 15 minutes in seconds
    currentPage: 'dashboard',
    
    /**
     * Initialize the application
     */
    init: function() {
        // Check if user is logged in
        this.sessionToken = sessionStorage.getItem('session_token');
        const userStr = sessionStorage.getItem('user');
        
        if (!this.sessionToken || !userStr) {
            window.location.href = '/login';
            return;
        }
        
        this.user = JSON.parse(userStr);
        
        // Setup UI
        this.setupUI();
        this.setupEventListeners();
        this.startSessionTimer();
        this.loadPage(this.currentPage);
        
        // Check session status every 30 seconds
        setInterval(() => this.checkSessionStatus(), 30000);
    },
    
    /**
     * Setup UI elements
     */
    setupUI: function() {
        // Display user info
        const userDisplay = document.getElementById('userDisplay');
        if (userDisplay) {
            userDisplay.textContent = `${this.user.username} (${this.user.role})`;
        }
        
        // Show/hide menu items based on role
        if (this.user.role === 'Admin') {
            // Admin sees everything
            document.getElementById('academicsMenu').style.display = 'block';
            document.getElementById('studentsMenu').style.display = 'block';
            document.getElementById('adminMenu').style.display = 'block';
            document.getElementById('adminMenu2').style.display = 'block';
            document.getElementById('adminMenu3').style.display = 'block';
        } else if (this.user.role === 'Faculty') {
            // Faculty sees students but not academics menu
            document.getElementById('studentsMenu').style.display = 'block';
            document.getElementById('academicsMenu').style.display = 'none';
        } else {
            // Students see nothing extra
            document.getElementById('academicsMenu').style.display = 'none';
            document.getElementById('studentsMenu').style.display = 'none';
        }
        
        // Load theme preference
        this.loadTheme();
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners: function() {
        // Menu toggle
        const menuToggle = document.getElementById('menuToggle');
        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                const sidebar = document.getElementById('sidebar');
                if (sidebar) {
                    sidebar.classList.toggle('active');
                }
            });
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
        
        // Navigation links
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                if (page) {
                    if (page === 'change-password') {
                        this.showChangePasswordModal();
                    } else {
                        this.navigateToPage(page);
                    }
                }
            });
        });
        
        // Change password link
        const changePasswordLink = document.getElementById('changePasswordLink');
        if (changePasswordLink) {
            changePasswordLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showChangePasswordModal();
            });
        }
        
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Data management link (Admin only)
        const dataManagementLink = document.getElementById('dataManagementLink');
        if (dataManagementLink && this.user.role === 'Admin') {
            dataManagementLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showDataManagementModal();
            });
        }
    },
    
    /**
     * Start session timer
     */
    startSessionTimer: function() {
        // Sync with server first
        this.syncSessionTime();
        
        // Update every second locally
        this.sessionCountdown = setInterval(() => {
            this.updateTimerDisplay();
        }, 1000);
        
        // Sync with server every 30 seconds
        this.sessionTimer = setInterval(() => {
            this.syncSessionTime();
        }, 30000);
    },
    
    /**
     * Sync session time with server
     */
    syncSessionTime: async function() {
        try {
            const response = await this.apiCall('/api/auth/session-status', 'GET');
            if (response.success) {
                this.remainingSeconds = Math.max(0, response.remaining_seconds);
                this.updateTimerDisplay();
            } else {
                this.handleSessionExpired();
            }
        } catch (error) {
            console.error('Session sync failed:', error);
            this.handleSessionExpired();
        }
    },
    
    /**
     * Update timer display (countdown decreasing per second)
     */
    updateTimerDisplay: function() {
        if (this.remainingSeconds <= 0) {
            this.handleSessionExpired();
            return;
        }
        
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        const display = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        const timerDisplay = document.getElementById('timerDisplay');
        if (timerDisplay) {
            timerDisplay.textContent = display;
            
            // Warning when less than 2 minutes
            if (this.remainingSeconds < 120 && this.remainingSeconds > 0) {
                timerDisplay.style.color = '#fbbf24';
                timerDisplay.style.fontWeight = 'bold';
            } else if (this.remainingSeconds === 0) {
                timerDisplay.style.color = '#ef4444';
                timerDisplay.style.fontWeight = 'bold';
            } else {
                timerDisplay.style.color = '';
                timerDisplay.style.fontWeight = '';
            }
        }
        
        // Decrease counter
        this.remainingSeconds = Math.max(0, this.remainingSeconds - 1);
    },
    
    /**
     * Check session status
     */
    checkSessionStatus: async function() {
        try {
            const response = await this.apiCall('/api/auth/session-status', 'GET');
            if (!response.success) {
                this.handleSessionExpired();
            }
        } catch (error) {
            this.handleSessionExpired();
        }
    },
    
    /**
     * Handle session expired
     */
    handleSessionExpired: function() {
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
        }
        if (this.sessionCountdown) {
            clearInterval(this.sessionCountdown);
        }
        this.showToast('Session expired. Please login again.', 'warning');
        setTimeout(() => {
            sessionStorage.clear();
            window.location.href = '/login';
        }, 2000);
    },
    
    /**
     * Logout user
     */
    logout: async function() {
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
        }
        if (this.sessionCountdown) {
            clearInterval(this.sessionCountdown);
        }
        try {
            await this.apiCall('/api/auth/logout', 'POST');
            sessionStorage.clear();
            window.location.href = '/login';
        } catch (error) {
            sessionStorage.clear();
            window.location.href = '/login';
        }
    },
    
    /**
     * Navigate to page
     */
    navigateToPage: function(page) {
        this.currentPage = page;
        
        // Update active nav link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            }
        });
        
        // Close sidebar on mobile
        const sidebar = document.getElementById('sidebar');
        if (sidebar && window.innerWidth < 1200) {
            sidebar.classList.remove('active');
        }
        
        // Load page content
        this.loadPage(page);
    },
    
    /**
     * Load page content
     */
    loadPage: function(page) {
        const mainContent = document.getElementById('mainContent');
        if (!mainContent) return;
        
        switch(page) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'academics':
                this.loadAcademics();
                break;
            case 'students':
                this.loadStudents();
                break;
            case 'events':
                this.loadEvents();
                break;
            case 'timetable':
                this.loadTimetable();
                break;
            case 'profile':
                this.loadProfile();
                break;
            case 'users':
                if (this.user.role === 'Admin') {
                    this.loadUsers();
                }
                break;
            case 'activities':
                if (this.user.role === 'Admin') {
                    this.loadActivities();
                }
                break;
            case 'change-password':
                this.loadChangePasswordPage();
                break;
            case 'data-management':
                if (this.user.role === 'Admin') {
                    this.showDataManagementModal();
                }
                break;
            default:
                this.loadDashboard();
        }
    },
    
    /**
     * Load theme preference
     */
    loadTheme: async function() {
        try {
            const response = await this.apiCall('/api/user/theme', 'GET');
            if (response.success) {
                this.applyTheme(response.theme);
            }
        } catch (error) {
            // Default to light mode
            this.applyTheme('light');
        }
    },
    
    /**
     * Apply theme
     */
    applyTheme: function(theme) {
        const body = document.body;
        const themeIcon = document.getElementById('themeIcon');
        
        if (theme === 'dark') {
            body.classList.add('dark-mode');
              if (themeIcon) themeIcon.textContent = 'Light';
        } else {
            body.classList.remove('dark-mode');
              if (themeIcon) themeIcon.textContent = 'Dark';
        }
    },
    
    /**
     * Toggle theme
     */
    toggleTheme: async function() {
        try {
            const currentTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            const response = await this.apiCall('/api/user/theme', 'PUT', { theme: newTheme });
            if (response.success) {
                this.applyTheme(newTheme);
                this.showToast(`Switched to ${newTheme} mode`, 'success');
            }
        } catch (error) {
            this.showToast('Failed to change theme', 'error');
        }
    },
    
    /**
     * Show data management modal
     */
    showDataManagementModal: function() {
        const modal = this.createModal(
            'Data Management',
            `
                <div class="data-management">
                    <div class="alert alert-warning" style="margin-bottom: 20px;">
                        <strong>Warning:</strong> This action cannot be undone. Please be careful.
                    </div>
                    
                    <div class="form-group">
                        <label>Clear Type</label>
                        <select id="clearType" onchange="App.toggleClearOptions()">
                            <option value="partial">Clear Partial (By Section)</option>
                            <option value="all">Clear All Data</option>
                        </select>
                    </div>
                    
                    <div id="sectionsContainer" class="form-group">
                        <label>Sections to Clear (comma-separated)</label>
                        <input type="text" id="clearSections" placeholder="e.g., A, B, BCA">
                        <small class="form-text">Enter section names separated by commas</small>
                    </div>
                    
                    <div id="clearAllWarning" style="display: none; padding: 12px; background: #fee2e2; border-radius: 6px; margin-bottom: 16px;">
                        <strong style="color: #991b1b;">Warning: This will delete ALL data except Admin user!</strong>
                        <ul style="margin: 8px 0 0 20px; color: #991b1b;">
                            <li>All Academics</li>
                            <li>All Students</li>
                            <li>All Events</li>
                            <li>All Timetable Entries</li>
                            <li>All Activity Logs</li>
                            <li>All Users (except Admin)</li>
                        </ul>
                    </div>
                </div>
            `,
            [
                { text: 'Cancel', class: 'btn-secondary', action: 'close' },
                { text: 'Clear Data', class: 'btn-danger', action: () => this.clearData() }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Toggle clear options based on type
     */
    toggleClearOptions: function() {
        const clearType = document.getElementById('clearType').value;
        const sectionsContainer = document.getElementById('sectionsContainer');
        const clearAllWarning = document.getElementById('clearAllWarning');
        
        if (clearType === 'all') {
            sectionsContainer.style.display = 'none';
            clearAllWarning.style.display = 'block';
        } else {
            sectionsContainer.style.display = 'block';
            clearAllWarning.style.display = 'none';
        }
    },
    
    /**
     * Clear data
     */
    clearData: async function() {
        const clearType = document.getElementById('clearType').value;
        
        if (clearType === 'all') {
            if (!confirm('WARNING: This will delete ALL data except Admin user. This cannot be undone!\n\nAre you absolutely sure?')) {
                return;
            }
            
            if (!confirm('This is your last chance. Are you 100% certain you want to delete ALL data?')) {
                return;
            }
        } else {
            const sections = document.getElementById('clearSections').value.trim();
            if (!sections) {
                this.showToast('Please enter sections to clear', 'error');
                return;
            }
            
            if (!confirm(`Are you sure you want to clear data for sections: ${sections}?`)) {
                return;
            }
        }
        
        try {
            const data = {
                type: clearType
            };
            
            if (clearType === 'partial') {
                const sections = document.getElementById('clearSections').value.trim().split(',').map(s => s.trim()).filter(s => s);
                data.sections = sections;
            }
            
            const response = await this.apiCall('/api/data/clear', 'POST', data);
            if (response.success) {
                this.showToast(`Data cleared successfully: ${response.cleared.join(', ')}`, 'success');
                this.closeModal();
                
                // Reload current page
                setTimeout(() => {
                    this.loadPage(this.currentPage);
                }, 1000);
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to clear data', 'error');
        }
    },
    
    /**
     * Show change password modal
     */
    showChangePasswordModal: function() {
        const modal = this.createModal(
            'Change Password',
            `
                <form id="changePasswordForm">
                    <div class="form-group">
                        <label>Current Password *</label>
                        <input type="password" id="currentPassword" required>
                    </div>
                    <div class="form-group">
                        <label>New Password *</label>
                        <input type="password" id="newPassword" required minlength="6">
                    </div>
                    <div class="form-group">
                        <label>Confirm New Password *</label>
                        <input type="password" id="confirmPassword" required minlength="6">
                    </div>
                </form>
            `,
            [
                { text: 'Cancel', class: 'btn-secondary', action: 'close' },
                { text: 'Change Password', class: 'btn-primary', action: () => this.changePassword() }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Load change password page (for first-time login)
     */
    loadChangePasswordPage: function() {
        const content = `
            <div class="page-header">
                <h2>Create New Password</h2>
            </div>
            
            <div class="card" style="max-width: 500px; margin: 0 auto;">
                <div style="padding: 24px;">
                    <p style="margin-bottom: 24px; color: #ef4444;">
                        <strong>First Time Login:</strong> You must change your default password before continuing.
                    </p>
                    
                    <form id="changePasswordForm">
                        <div class="form-group">
                            <label for="currentPassword">Current Password (Default Password)</label>
                            <input type="password" id="currentPassword" class="form-control" required 
                                   placeholder="Enter your current default password">
                        </div>
                        
                        <div class="form-group">
                            <label for="newPassword">New Password</label>
                            <input type="password" id="newPassword" class="form-control" required 
                                   minlength="6" placeholder="Enter new password (min 6 characters)">
                            <small class="form-text">Password must be at least 6 characters long</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="confirmPassword">Confirm New Password</label>
                            <input type="password" id="confirmPassword" class="form-control" required 
                                   minlength="6" placeholder="Confirm new password">
                        </div>
                        
                        <div id="passwordError" class="error-message" style="display: none; margin-bottom: 16px;"></div>
                        
                        <button type="submit" class="btn btn-primary btn-block">Change Password</button>
                    </form>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        // Setup form handler
        document.getElementById('changePasswordForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.changePasswordFirstTime();
        });
    },
    
    /**
     * Change password (first-time login)
     */
    changePasswordFirstTime: async function() {
        const form = document.getElementById('changePasswordForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const errorDiv = document.getElementById('passwordError');
        
        if (newPassword !== confirmPassword) {
            errorDiv.textContent = 'New passwords do not match';
            errorDiv.style.display = 'block';
            return;
        }
        
        if (newPassword.length < 6) {
            errorDiv.textContent = 'Password must be at least 6 characters long';
            errorDiv.style.display = 'block';
            return;
        }
        
        errorDiv.style.display = 'none';
        
        try {
            const response = await this.apiCall('/api/users/change-password', 'PUT', {
                current_password: currentPassword,
                new_password: newPassword
            });
            
            if (response.success) {
                this.showToast('Password changed successfully! Please login again.', 'success');
                
                // Logout and redirect to login
                setTimeout(() => {
                    sessionStorage.clear();
                    window.location.href = '/login';
                }, 2000);
            } else {
                errorDiv.textContent = response.message || 'Failed to change password';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Failed to change password. Please try again.';
            errorDiv.style.display = 'block';
        }
    },
    
    /**
     * Change password (from modal)
     */
    changePassword: async function() {
        const form = document.getElementById('changePasswordForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (newPassword !== confirmPassword) {
            this.showToast('New passwords do not match', 'error');
            return;
        }
        
        try {
            const response = await this.apiCall('/api/users/change-password', 'PUT', {
                current_password: currentPassword,
                new_password: newPassword
            });
            
            if (response.success) {
                this.showToast('Password changed successfully', 'success');
                this.closeModal();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to change password', 'error');
        }
    },
    
    /**
     * Load dashboard
     */
    loadDashboard: async function() {
        const content = `
            <div class="page-header">
                <h2>Dashboard</h2>
            </div>
            
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="stat-card-title">Loading...</div>
                    <div class="stat-card-value">-</div>
                </div>
            </div>
            
            <div class="content-section">
                <h3>Quick Actions</h3>
                <div class="quick-actions" id="quickActions">
                    ${this.getQuickActions()}
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        // Load stats
        try {
            const response = await this.apiCall('/api/dashboard/stats', 'GET');
            if (response.success) {
                this.renderDashboardStats(response.stats);
            }
        } catch (error) {
            this.showToast('Failed to load dashboard stats', 'error');
        }
    },
    
    /**
     * Get quick actions based on role
     */
    getQuickActions: function() {
        if (this.user.role === 'Admin') {
            return `
                <a href="#" class="quick-action-btn" data-action="add-academic">
                    <div class="icon">Academic</div>
                    <div class="label">Add Academic</div>
                </a>
                <a href="#" class="quick-action-btn" data-action="add-student">
                    <div class="icon">Student</div>
                    <div class="label">Add Student</div>
                </a>
                <a href="#" class="quick-action-btn" data-action="add-event">
                    <div class="icon">Event</div>
                    <div class="label">Create Event</div>
                </a>
                <a href="#" class="quick-action-btn" data-action="add-class">
                    <div class="icon">Class</div>
                    <div class="label">Add Class</div>
                </a>
            `;
        } else {
            return `
                <a href="#" class="quick-action-btn" data-action="view-timetable">
                    <div class="icon">Timetable</div>
                    <div class="label">My Timetable</div>
                </a>
                <a href="#" class="quick-action-btn" data-action="view-events">
                    <div class="icon">Events</div>
                    <div class="label">Events</div>
                </a>
                <a href="#" class="quick-action-btn" data-action="view-profile">
                    <div class="icon">Profile</div>
                    <div class="label">My Profile</div>
                </a>
            `;
        }
    },
    
    /**
     * Render dashboard stats
     */
    renderDashboardStats: function(stats) {
        const statsGrid = document.getElementById('statsGrid');
        if (!statsGrid) return;
        
        if (this.user.role === 'Admin') {
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-card-title">Total Users</div>
                    <div class="stat-card-value">${stats.total_users}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Total Academics</div>
                    <div class="stat-card-value">${stats.total_academics}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Total Students</div>
                    <div class="stat-card-value">${stats.total_students}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Total Events</div>
                    <div class="stat-card-value">${stats.total_events}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Today's Classes</div>
                    <div class="stat-card-value">${stats.today_classes}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Active Sessions</div>
                    <div class="stat-card-value">${stats.active_sessions}</div>
                </div>
            `;
        } else {
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-card-title">Today's Classes</div>
                    <div class="stat-card-value">${stats.today_classes}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-title">Upcoming Events</div>
                    <div class="stat-card-value">${stats.total_events}</div>
                </div>
            `;
        }
        
        // Setup quick action buttons
        const quickActionBtns = document.querySelectorAll('.quick-action-btn');
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = btn.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });
    },
    
    /**
     * Handle quick action
     */
    handleQuickAction: function(action) {
        switch(action) {
            case 'add-academic':
                this.navigateToPage('academics');
                setTimeout(() => this.showAddAcademicModal(), 100);
                break;
            case 'add-student':
                this.navigateToPage('students');
                setTimeout(() => this.showAddStudentModal(), 100);
                break;
            case 'add-event':
                this.navigateToPage('events');
                setTimeout(() => this.showAddEventModal(), 100);
                break;
            case 'add-class':
                this.navigateToPage('timetable');
                setTimeout(() => this.showAddClassModal(), 100);
                break;
            case 'view-timetable':
                this.navigateToPage('timetable');
                break;
            case 'view-events':
                this.navigateToPage('events');
                break;
            case 'view-profile':
                this.navigateToPage('profile');
                break;
        }
    },
    
    /**
     * Load academics page
     */
    loadAcademics: async function() {
        if (this.user.role !== 'Admin') {
            this.showToast('Unauthorized access', 'error');
            return;
        }
        
        const content = `
            <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
                <h2>Academics Management</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary" onclick="App.exportData('academics', 'csv')">Export CSV</button>
                    <button class="btn btn-secondary" onclick="App.exportData('academics', 'pdf')">Export PDF</button>
                    <button class="btn btn-primary" id="addAcademicBtn">+ Add Academic</button>
                </div>
            </div>
            
            <div class="card">
                <div class="table-container">
                    <table id="academicsTable">
                        <thead>
                            <tr>
                                <th>S.No</th>
                                <th>Name</th>
                                <th>Department</th>
                                <th>Qualification</th>
                                <th>Experience</th>
                                <th>Email</th>
                                <th>Phone</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="academicsTableBody">
                            <tr><td colspan="9" class="text-center">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        // Setup add button
        document.getElementById('addAcademicBtn').addEventListener('click', () => {
            this.showAddAcademicModal();
        });
        
        // Load academics
        await this.loadAcademicsList();
    },
    
    /**
     * Load academics list
     */
    loadAcademicsList: async function() {
        try {
            const response = await this.apiCall('/api/academics/list', 'GET');
            if (response.success) {
                this.renderAcademicsTable(response.data);
            }
        } catch (error) {
            this.showToast('Failed to load academics', 'error');
        }
    },
    
    /**
     * Render academics table
     */
    renderAcademicsTable: function(academics) {
        const tbody = document.getElementById('academicsTableBody');
        if (!tbody) return;
        
        if (academics.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">No academics found</td></tr>';
            return;
        }
        
        tbody.innerHTML = academics.map((acad, index) => `
            <tr>
                <td>${index + 1}</td>
                <td>${this.escapeHtml(acad.name)}</td>
                <td>${this.escapeHtml(acad.department)}</td>
                <td>${this.escapeHtml(acad.qualification)}</td>
                <td>${acad.experience} years</td>
                <td>${this.escapeHtml(acad.email)}</td>
                <td>${this.escapeHtml(acad.phone)}</td>
                <td><span class="badge ${acad.status === 'active' ? 'badge-success' : 'badge-danger'}">${acad.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="App.viewAcademic('${acad.id}')">View</button>
                    <button class="btn btn-sm btn-primary" onclick="App.editAcademic('${acad.id}')">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="App.deleteAcademic('${acad.id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    },
    
    /**
     * Export data
     */
    exportData: async function(dataType, format) {
        try {
            if (format === 'csv') {
                const url = `/api/export/${dataType}?format=csv`;
                window.open(url, '_blank');
                this.showToast('Exporting CSV...', 'info');
            } else if (format === 'pdf') {
                const response = await this.apiCall(`/api/export/${dataType}?format=pdf`, 'GET');
                if (response.success) {
                    this.generatePDF(response.data, response.filename);
                }
            }
        } catch (error) {
            this.showToast('Failed to export data', 'error');
        }
    },
    
    /**
     * Generate PDF (simple text-based)
     */
    generatePDF: function(data, filename) {
        // Simple PDF generation using window.print or download as text
        let content = `${filename.toUpperCase()} REPORT\n`;
        content += `Generated: ${new Date().toLocaleString()}\n\n`;
        
        if (data.length > 0) {
            const headers = Object.keys(data[0]);
            content += headers.join('\t') + '\n';
            
            data.forEach(row => {
                content += headers.map(h => row[h] || '').join('\t') + '\n';
            });
        }
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}_${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('PDF data exported as text file', 'success');
    },
    
    /**
     * Create backup
     */
    createBackup: async function() {
        if (!confirm('Create backup of all data?')) {
            return;
        }
        
        try {
            const response = await this.apiCall('/api/backup/create', 'POST');
            if (response.success) {
                this.showToast(`Backup created: ${response.backup_folder}`, 'success');
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to create backup', 'error');
        }
    },
    
    /**
     * Show add academic modal
     */
    showAddAcademicModal: function(academic = null) {
        const isEdit = academic !== null;
        const modal = this.createModal(
            isEdit ? 'Edit Academic' : 'Add Academic',
            `
                <form id="academicForm">
                    <div class="form-group">
                        <label>Name *</label>
                        <input type="text" id="acadName" required value="${academic ? this.escapeHtml(academic.name) : ''}">
                    </div>
                    <div class="form-group">
                        <label>Department *</label>
                        <input type="text" id="acadDept" required value="${academic ? this.escapeHtml(academic.department) : ''}">
                    </div>
                    <div class="form-group">
                        <label>Qualification *</label>
                        <input type="text" id="acadQual" required value="${academic ? this.escapeHtml(academic.qualification) : ''}">
                    </div>
                    <div class="form-group">
                        <label>Experience (years) *</label>
                        <input type="number" id="acadExp" required min="0" max="60" value="${academic ? academic.experience : ''}">
                    </div>
                    <div class="form-group">
                        <label>Email *</label>
                        <input type="email" id="acadEmail" required value="${academic ? this.escapeHtml(academic.email) : ''}">
                    </div>
                    <div class="form-group">
                        <label>Phone *</label>
                        <input type="tel" id="acadPhone" required pattern="[0-9]{10}" value="${academic ? this.escapeHtml(academic.phone) : ''}">
                    </div>
                </form>
            `,
            [
                { text: 'Cancel', class: 'btn-secondary', action: 'close' },
                { text: isEdit ? 'Update' : 'Add', class: 'btn-primary', action: () => this.saveAcademic(academic?.id) }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Save academic
     */
    saveAcademic: async function(acadId) {
        const form = document.getElementById('academicForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const data = {
            name: document.getElementById('acadName').value.trim(),
            department: document.getElementById('acadDept').value.trim(),
            qualification: document.getElementById('acadQual').value.trim(),
            experience: document.getElementById('acadExp').value.trim(),
            email: document.getElementById('acadEmail').value.trim(),
            phone: document.getElementById('acadPhone').value.trim()
        };
        
        try {
            let response;
            if (acadId) {
                response = await this.apiCall(`/api/academics/${acadId}`, 'PUT', data);
            } else {
                response = await this.apiCall('/api/academics/add', 'POST', data);
            }
            
            if (response.success) {
                this.showToast(response.message, 'success');
                this.closeModal();
                await this.loadAcademicsList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to save academic', 'error');
        }
    },
    
    /**
     * Edit academic
     */
    editAcademic: async function(acadId) {
        try {
            const response = await this.apiCall('/api/academics/list', 'GET');
            if (response.success) {
                const academic = response.data.find(a => a.id === acadId);
                if (academic) {
                    this.showAddAcademicModal(academic);
                }
            }
        } catch (error) {
            this.showToast('Failed to load academic', 'error');
        }
    },
    
    /**
     * View academic
     */
    viewAcademic: async function(acadId) {
        try {
            const response = await this.apiCall(`/api/academics/${acadId}/view`, 'GET');
            if (response.success) {
                this.showAcademicDetails(response.academic);
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to load academic details', 'error');
        }
    },
    
    /**
     * Show academic details modal
     */
    showAcademicDetails: function(academic) {
        const modal = this.createModal(
            `Academic Details - ${this.escapeHtml(academic.name)}`,
            `
                <div class="academic-details">
                    <div class="form-group">
                        <label>Name</label>
                        <input type="text" value="${this.escapeHtml(academic.name || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" value="${this.escapeHtml(academic.username || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Department</label>
                        <input type="text" value="${this.escapeHtml(academic.department || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Qualification</label>
                        <input type="text" value="${this.escapeHtml(academic.qualification || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Experience</label>
                        <input type="text" value="${academic.experience || '0'} years" readonly>
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="text" value="${this.escapeHtml(academic.email || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Phone</label>
                        <input type="text" value="${this.escapeHtml(academic.phone || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Registration ID</label>
                        <input type="text" value="${this.escapeHtml(academic.registration_id || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Status</label>
                        <input type="text" value="${this.escapeHtml(academic.status || 'active')}" readonly>
                    </div>
                </div>
            `,
            [
                { text: 'Close', class: 'btn-secondary', action: 'close' }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Delete academic
     */
    deleteAcademic: async function(acadId) {
        if (!confirm('Are you sure you want to delete this academic?')) {
            return;
        }
        
        try {
            const response = await this.apiCall(`/api/academics/${acadId}`, 'DELETE');
            if (response.success) {
                this.showToast(response.message, 'success');
                await this.loadAcademicsList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to delete academic', 'error');
        }
    },
    
    /**
     * Load students page
     */
    loadStudents: async function() {
        // Allow Admin and Faculty to access the Students Management page
        if (this.user.role !== 'Admin' && this.user.role !== 'Faculty') {
            this.showToast('Unauthorized access', 'error');
            return;
        }
        
        const content = `
            <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
                <h2>Students Management</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary" onclick="App.exportData('students', 'csv')">Export CSV</button>
                    <button class="btn btn-secondary" onclick="App.exportData('students', 'pdf')">Export PDF</button>
                    <button class="btn btn-primary" id="addStudentBtn">+ Add Student</button>
                </div>
            </div>
            
            <div class="card">
                <div class="table-container">
                    <table id="studentsTable">
                        <thead>
                            <tr>
                                <th>S.No</th>
                                <th>Name</th>
                                <th>Login ID</th>
                                <th>Section</th>
                                <th>DOB</th>
                                <th>Gender</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="studentsTableBody">
                            <tr><td colspan="9" class="text-center">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        document.getElementById('addStudentBtn').addEventListener('click', () => {
            this.showAddStudentModal();
        });
        
        await this.loadStudentsList();
    },
    
    /**
     * Load students list
     */
    loadStudentsList: async function() {
        try {
            const response = await this.apiCall('/api/students/list', 'GET');
            if (response.success) {
                this.renderStudentsTable(response.data);
            }
        } catch (error) {
            this.showToast('Failed to load students', 'error');
        }
    },
    
    /**
     * Render students table
     */
    renderStudentsTable: function(students) {
        const tbody = document.getElementById('studentsTableBody');
        if (!tbody) return;
        
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">No students found</td></tr>';
            return;
        }
        
        tbody.innerHTML = students.map((stu, index) => `
            <tr>
                <td>${index + 1}</td>
                <td>${this.escapeHtml(stu.student_name)}</td>
                <td>${this.escapeHtml(stu.login_id)}</td>
                <td>${this.escapeHtml(stu.section)}</td>
                <td>${stu.dob}</td>
                <td>${this.escapeHtml(stu.gender)}</td>
                <td>${this.escapeHtml(stu.email || '-')}</td>
                <td><span class="badge ${stu.status === 'active' ? 'badge-success' : 'badge-danger'}">${stu.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="App.viewStudent('${stu.id}')">View</button>
                    ${this.user.role === 'Admin' || this.user.role === 'Faculty' ? `<button class="btn btn-sm btn-danger" onclick="App.deleteStudent('${stu.id}')">Delete</button>` : ''}
                </td>
            </tr>
        `).join('');
    },
    
    /**
     * Show add student modal (simplified - only name and section)
     */
    showAddStudentModal: function() {
        const modal = this.createModal(
            'Add Student',
            `
                <form id="studentForm">
                    <div class="form-group">
                        <label>Student Name *</label>
                        <input type="text" id="stuName" required placeholder="Enter full name">
                        <small class="form-text">Username will be auto-generated</small>
                    </div>
                    <div class="form-group">
                        <label>Section *</label>
                        <input type="text" id="stuSection" required placeholder="e.g., A, B, C, BCA">
                        <small class="form-text">Other details will be filled during first login</small>
                    </div>
                </form>
            `,
            [
                { text: 'Cancel', class: 'btn-secondary', action: 'close' },
                { text: 'Add', class: 'btn-primary', action: () => this.saveStudent() }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Save student (simplified)
     */
    saveStudent: async function() {
        const form = document.getElementById('studentForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const data = {
            student_name: document.getElementById('stuName').value.trim(),
            section: document.getElementById('stuSection').value.trim()
        };
        
        try {
            const response = await this.apiCall('/api/students/add', 'POST', data);
            if (response.success) {
                this.showToast(`Student added successfully. Username: ${response.student.username}, Default password: ${response.student.default_password}`, 'success');
                this.closeModal();
                await this.loadStudentsList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to save student', 'error');
        }
    },
    
    /**
     * Delete student
     */
    deleteStudent: async function(stuId) {
        if (!confirm('Are you sure you want to delete this student?')) {
            return;
        }
        
        try {
            const response = await this.apiCall(`/api/students/${stuId}`, 'DELETE');
            if (response.success) {
                this.showToast(response.message, 'success');
                await this.loadStudentsList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to delete student', 'error');
        }
    },
    
    /**
     * View student
     */
    viewStudent: async function(stuId) {
        try {
            const response = await this.apiCall(`/api/students/${stuId}/view`, 'GET');
            if (response.success) {
                this.showStudentDetails(response.student);
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to load student details', 'error');
        }
    },
    
    /**
     * Show student details modal
     */
    showStudentDetails: function(student) {
        const role = this.user.role;
        const passwordSection = role === 'Admin' && student.password ? `
            <div class="form-group">
                <label>Password Hash</label>
                <input type="text" value="${this.escapeHtml(student.password)}" readonly style="font-family: monospace; font-size: 12px;">
            </div>
        ` : '';
        
        const modal = this.createModal(
            `Student Details - ${this.escapeHtml(student.student_name)}`,
            `
                <div class="student-details">
                    <div class="form-group">
                        <label>Student Name</label>
                        <input type="text" value="${this.escapeHtml(student.student_name || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" value="${this.escapeHtml(student.username || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Section</label>
                        <input type="text" value="${this.escapeHtml(student.section || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Registration ID</label>
                        <input type="text" value="${this.escapeHtml(student.registration_id || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>First Name</label>
                        <input type="text" value="${this.escapeHtml(student.first_name || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Last Name</label>
                        <input type="text" value="${this.escapeHtml(student.last_name || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Date of Birth</label>
                        <input type="text" value="${student.dob || ''}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Gender</label>
                        <input type="text" value="${this.escapeHtml(student.gender || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="text" value="${this.escapeHtml(student.email || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Phone</label>
                        <input type="text" value="${this.escapeHtml(student.phone || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Father's Name</label>
                        <input type="text" value="${this.escapeHtml(student.father_name || '')}" readonly>
                    </div>
                    <div class="form-group">
                        <label>Mother's Name</label>
                        <input type="text" value="${this.escapeHtml(student.mother_name || '')}" readonly>
                    </div>
                    ${passwordSection}
                    <div class="form-group">
                        <label>Status</label>
                        <input type="text" value="${this.escapeHtml(student.status || 'active')}" readonly>
                    </div>
                </div>
            `,
            [
                { text: 'Close', class: 'btn-secondary', action: 'close' }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Load events page
     */
    loadEvents: async function() {
        const content = `
            <div class="page-header">
                <h2>Events Management</h2>
                ${this.user.role === 'Admin' ? '<button class="btn btn-primary" id="addEventBtn">+ Create Event</button>' : ''}
            </div>
            
            <div class="card">
                <div id="eventsList">
                    <div class="text-center">Loading...</div>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        if (this.user.role === 'Admin') {
            document.getElementById('addEventBtn').addEventListener('click', () => {
                this.showAddEventModal();
            });
        }
        
        await this.loadEventsList();
    },
    
    /**
     * Load events list
     */
    loadEventsList: async function() {
        try {
            const response = await this.apiCall('/api/events/list', 'GET');
            if (response.success) {
                this.renderEventsList(response.data);
            }
        } catch (error) {
            this.showToast('Failed to load events', 'error');
        }
    },
    
    /**
     * Render events list
     */
    renderEventsList: function(events) {
        const container = document.getElementById('eventsList');
        if (!container) return;
        
        if (events.length === 0) {
            container.innerHTML = '<div class="text-center">No events found</div>';
            return;
        }
        
        container.innerHTML = events.map(event => `
            <div class="card" style="margin-bottom: 16px;">
                <div class="card-header">
                    <h3 class="card-title">${this.escapeHtml(event.title)}</h3>
                    <span class="badge badge-success">${event.status}</span>
                </div>
                <div>
                    <p><strong>Date:</strong> ${event.date} at ${event.time_12}</p>
                    <p><strong>Organizer:</strong> ${this.escapeHtml(event.organizer_name)}</p>
                    <p><strong>Club:</strong> ${this.escapeHtml(event.club_name)}</p>
                    <p><strong>Capacity:</strong> ${event.registered_count}/${event.capacity}</p>
                    ${event.venue ? `<p><strong>Venue:</strong> ${this.escapeHtml(event.venue)}</p>` : ''}
                    ${event.description ? `<p>${this.escapeHtml(event.description)}</p>` : ''}
                    <div style="margin-top: 12px;">
                        ${this.user.role === 'Student' ? `<button class="btn btn-sm btn-primary" onclick="App.registerEvent('${event.id}')">Register</button>` : ''}
                        <button class="btn btn-sm btn-secondary" onclick="App.viewEventRegistrations('${event.id}')">View Registrations (${event.registered_count})</button>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    /**
     * Register for event
     */
    registerEvent: async function(evtId) {
        try {
            const response = await this.apiCall(`/api/events/${evtId}/register`, 'POST');
            if (response.success) {
                this.showToast(response.message, 'success');
                await this.loadEventsList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to register for event', 'error');
        }
    },
    
    /**
     * View event registrations
     */
    viewEventRegistrations: async function(evtId) {
        try {
            const response = await this.apiCall(`/api/events/${evtId}/registrations`, 'GET');
            if (response.success) {
                this.showEventRegistrations(evtId, response.registrations, response.total, response.capacity);
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to load registrations', 'error');
        }
    },
    
    /**
     * Show event registrations modal
     */
    showEventRegistrations: function(evtId, registrations, total, capacity) {
        const registrationsList = registrations.length === 0 
            ? '<p class="text-center">No registrations yet</p>'
            : `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>S.No</th>
                                <th>Student Name</th>
                                <th>Section</th>
                                <th>Username</th>
                                <th>Registered At</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${registrations.map((reg, index) => `
                                <tr>
                                    <td>${index + 1}</td>
                                    <td>${this.escapeHtml(reg.student_name)}</td>
                                    <td>${this.escapeHtml(reg.section)}</td>
                                    <td>${this.escapeHtml(reg.username)}</td>
                                    <td>${new Date(reg.registered_at).toLocaleString()}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        
        const modal = this.createModal(
            `Event Registrations (${total}/${capacity})`,
            `
                <div>
                    <p><strong>Total Registered:</strong> ${total} / ${capacity}</p>
                    ${registrationsList}
                </div>
            `,
            [
                { text: 'Close', class: 'btn-secondary', action: 'close' }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Show add event modal
     */
    showAddEventModal: function() {
        const modal = this.createModal(
            'Create Event',
            `
                <form id="eventForm">
                    <div class="form-group">
                        <label>Event Title *</label>
                        <input type="text" id="evtTitle" required>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Date *</label>
                            <input type="date" id="evtDate" required>
                        </div>
                        <div class="form-group">
                            <label>Time *</label>
                            <input type="time" id="evtTime" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Organizer Name *</label>
                            <input type="text" id="evtOrganizer" required>
                        </div>
                        <div class="form-group">
                            <label>Club Name *</label>
                            <input type="text" id="evtClub" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Capacity *</label>
                        <input type="number" id="evtCapacity" required min="1" max="10000">
                    </div>
                    <div class="form-group">
                        <label>Chief Guest</label>
                        <input type="text" id="evtGuest">
                    </div>
                    <div class="form-group">
                        <label>Venue</label>
                        <input type="text" id="evtVenue">
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="evtDesc" rows="3"></textarea>
                    </div>
                </form>
            `,
            [
                { text: 'Cancel', class: 'btn-secondary', action: 'close' },
                { text: 'Create', class: 'btn-primary', action: () => this.saveEvent() }
            ]
        );
        
        // Set minimum date to today
        const dateInput = document.getElementById('evtDate');
        if (dateInput) {
            dateInput.min = new Date().toISOString().split('T')[0];
        }
        
        document.body.appendChild(modal);
    },
    
    /**
     * Save event
     */
    saveEvent: async function() {
        const form = document.getElementById('eventForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const data = {
            title: document.getElementById('evtTitle').value.trim(),
            date: document.getElementById('evtDate').value,
            time: document.getElementById('evtTime').value,
            organizer_name: document.getElementById('evtOrganizer').value.trim(),
            club_name: document.getElementById('evtClub').value.trim(),
            capacity: document.getElementById('evtCapacity').value,
            chief_guest: document.getElementById('evtGuest').value.trim(),
            venue: document.getElementById('evtVenue').value.trim(),
            description: document.getElementById('evtDesc').value.trim()
        };
        
        try {
            const response = await this.apiCall('/api/events/add', 'POST', data);
            if (response.success) {
                this.showToast(response.message, 'success');
                this.closeModal();
                await this.loadEventsList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to create event', 'error');
        }
    },
    
    /**
     * Load timetable page
     */
    loadTimetable: async function() {
        const content = `
            <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
                <h2>Timetable Management</h2>
                ${this.user.role === 'Admin' || this.user.role === 'Faculty' ? `
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-secondary" onclick="App.exportData('timetable', 'csv')">Export CSV</button>
                        <button class="btn btn-secondary" onclick="App.exportData('timetable', 'pdf')">Export PDF</button>
                                <button class="btn btn-primary" id="addClassBtn">+ Add Class</button>
                    </div>
                ` : ''}
            </div>
            
            <div class="card">
                <div id="timetableContent">
                    <div class="text-center">Loading...</div>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        if (this.user.role === 'Admin' || this.user.role === 'Faculty') {
            const addBtn = document.getElementById('addClassBtn');
            if (addBtn) addBtn.addEventListener('click', () => {
                this.showAddClassModal();
            });
        }
        
        await this.loadTimetableData();
    },
    
    /**
     * Load timetable data
     */
    loadTimetableData: async function() {
        try {
            const response = await this.apiCall('/api/timetable/list', 'GET');
            if (response.success) {
                this.renderTimetable(response.data);
            }
        } catch (error) {
            this.showToast('Failed to load timetable', 'error');
        }
    },
    
    /**
     * Render timetable
     */
    renderTimetable: function(timetable) {
        const container = document.getElementById('timetableContent');
        if (!container) return;
        
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        
        // Group by section
        const sections = new Set();
        days.forEach(day => {
            (timetable[day] || []).forEach(entry => {
                if (entry.section) sections.add(entry.section);
            });
        });
        
        let html = '';
        
        if (sections.size === 0) {
            html = '<div class="text-center">No timetable entries found</div>';
        } else {
            sections.forEach(section => {
                html += `<div class="card" style="margin-bottom: 24px;"><h3 style="margin-bottom: 16px;">Section: ${section}</h3>`;
                html += '<div class="table-container"><table><thead><tr><th>Day</th><th>Time</th><th>Class</th><th>Faculty</th><th>Subject</th><th>Room</th>';
                if (this.user.role === 'Admin' || this.user.role === 'Faculty') {
                    html += '<th>Actions</th>';
                }
                html += '</tr></thead><tbody>';
                
                days.forEach(day => {
                    const entries = (timetable[day] || []).filter(e => e.section === section);
                    if (entries.length === 0) {
                        // Don't show empty days for each section
                    } else {
                        entries.forEach(entry => {
                            html += `
                                <tr>
                                    <td>${day}</td>
                                    <td>${entry.start_time_12} - ${entry.end_time_12}</td>
                                    <td>${this.escapeHtml(entry.class_name)}</td>
                                    <td>${this.escapeHtml(entry.faculty_name)}</td>
                                    <td>${this.escapeHtml(entry.subject)}</td>
                                    <td>${this.escapeHtml(entry.classroom || '-')}</td>
                                    ${this.user.role === 'Admin' || this.user.role === 'Faculty' ? `<td><button class="btn btn-sm btn-danger" onclick="App.deleteTimetableEntry('${entry.id}')">Delete</button></td>` : ''}
                                </tr>
                            `;
                        });
                    }
                });
                
                html += '</tbody></table></div></div>';
            });
        }
        
        container.innerHTML = html;
    },
    
    /**
     * Show add class modal
     */
    showAddClassModal: function() {
        const modal = this.createModal(
            'Add Class',
            `
                <form id="classForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Day *</label>
                            <select id="classDay" required>
                                <option value="">Select Day</option>
                                <option value="Monday">Monday</option>
                                <option value="Tuesday">Tuesday</option>
                                <option value="Wednesday">Wednesday</option>
                                <option value="Thursday">Thursday</option>
                                <option value="Friday">Friday</option>
                                <option value="Saturday">Saturday</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Subject *</label>
                            <input type="text" id="classSubject" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Start Time *</label>
                            <input type="time" id="classStartTime" required>
                        </div>
                        <div class="form-group">
                            <label>End Time *</label>
                            <input type="time" id="classEndTime" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Section *</label>
                            <input type="text" id="classSection" required placeholder="e.g., A, B, BCA">
                        </div>
                        <div class="form-group">
                            <label>Class Name *</label>
                            <input type="text" id="className" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Faculty Name *</label>
                            <input type="text" id="classFaculty" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Classroom</label>
                            <input type="text" id="classRoom">
                        </div>
                        <div class="form-group">
                            <label>Building</label>
                            <input type="text" id="classBuilding">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Topic Covered</label>
                        <textarea id="classTopic" rows="2"></textarea>
                    </div>
                </form>
            `,
            [
                { text: 'Cancel', class: 'btn-secondary', action: 'close' },
                { text: 'Add', class: 'btn-primary', action: () => this.saveClass() }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Save class
     */
    saveClass: async function() {
        const form = document.getElementById('classForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const data = {
            day: document.getElementById('classDay').value,
            start_time: document.getElementById('classStartTime').value,
            end_time: document.getElementById('classEndTime').value,
            section: document.getElementById('classSection').value.trim(),
            class_name: document.getElementById('className').value.trim(),
            faculty_name: document.getElementById('classFaculty').value.trim(),
            subject: document.getElementById('classSubject').value.trim(),
            classroom: document.getElementById('classRoom').value.trim(),
            building: document.getElementById('classBuilding').value.trim(),
            topic_covered: document.getElementById('classTopic').value.trim()
        };
        
        try {
            const response = await this.apiCall('/api/timetable/add', 'POST', data);
            if (response.success) {
                this.showToast(response.message, 'success');
                this.closeModal();
                await this.loadTimetableData();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to add class', 'error');
        }
    },
    
    /**
     * Delete timetable entry
     */
    deleteTimetableEntry: async function(entryId) {
        if (!confirm('Are you sure you want to delete this class?')) {
            return;
        }
        
        try {
            const response = await this.apiCall(`/api/timetable/${entryId}`, 'DELETE');
            if (response.success) {
                this.showToast(response.message, 'success');
                await this.loadTimetableData();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to delete class', 'error');
        }
    },
    
    /**
     * Load profile page
     */
    loadProfile: async function() {
        const content = `
            <div class="page-header">
                <h2>My Profile</h2>
            </div>
            
            <div class="card">
                <div id="profileContent">
                    <div class="text-center">Loading...</div>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        await this.loadProfileData();
    },
    
    /**
     * Load profile data
     */
    loadProfileData: async function() {
        try {
            const response = await this.apiCall('/api/profile/get', 'GET');
            if (response.success) {
                this.renderProfile(response);
            }
        } catch (error) {
            this.showToast('Failed to load profile', 'error');
        }
    },
    
    /**
     * Render profile
     */
    renderProfile: function(data) {
        const container = document.getElementById('profileContent');
        if (!container) return;
        
        if (!data.profile_completed) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <h3>Complete Your Profile</h3>
                    <p>You must complete your profile before accessing the dashboard.</p>
                </div>
                ${this.getProfileForm(data)}
            `;
        } else {
            container.innerHTML = `
                <div class="profile-display">
                    <p><strong>Registration ID:</strong> ${data.registration_id}</p>
                    <p><strong>Username:</strong> ${data.username}</p>
                    <p><strong>Role:</strong> ${data.role}</p>
                    <p><strong>First Name:</strong> ${this.escapeHtml(data.profile.first_name)}</p>
                    <p><strong>Last Name:</strong> ${this.escapeHtml(data.profile.last_name)}</p>
                    <p><strong>Date of Birth:</strong> ${data.profile.dob}</p>
                    <p><strong>Gender:</strong> ${this.escapeHtml(data.profile.gender)}</p>
                    <p><strong>Marital Status:</strong> ${this.escapeHtml(data.profile.marital_status)}</p>
                    <p><strong>Email:</strong> ${this.escapeHtml(data.profile.email)}</p>
                    <p><strong>Father's Name:</strong> ${this.escapeHtml(data.profile.father_name)}</p>
                    <p><strong>Mother's Name:</strong> ${this.escapeHtml(data.profile.mother_name)}</p>
                </div>
                <div class="form-actions">
                    <button class="btn btn-primary" onclick="App.showEditProfile()">Edit Profile</button>
                </div>
            `;
        }
        
        // Setup form submission if profile incomplete
        if (!data.profile_completed) {
            const form = document.getElementById('profileForm');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.saveProfile();
                });
            }
        }
    },
    
    /**
     * Get profile form
     */
    getProfileForm: function(data) {
        const profile = data.profile || {};
        return `
            <form id="profileForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>First Name *</label>
                        <input type="text" id="profFirstName" required value="${this.escapeHtml(profile.first_name || '')}">
                    </div>
                    <div class="form-group">
                        <label>Last Name *</label>
                        <input type="text" id="profLastName" required value="${this.escapeHtml(profile.last_name || '')}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Date of Birth *</label>
                        <input type="date" id="profDob" required value="${profile.dob || ''}">
                    </div>
                    <div class="form-group">
                        <label>Gender *</label>
                        <select id="profGender" required>
                            <option value="">Select</option>
                            <option value="Male" ${profile.gender === 'Male' ? 'selected' : ''}>Male</option>
                            <option value="Female" ${profile.gender === 'Female' ? 'selected' : ''}>Female</option>
                            <option value="Other" ${profile.gender === 'Other' ? 'selected' : ''}>Other</option>
                        </select>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Marital Status *</label>
                        <select id="profMarital" required>
                            <option value="">Select</option>
                            <option value="Single" ${profile.marital_status === 'Single' ? 'selected' : ''}>Single</option>
                            <option value="Married" ${profile.marital_status === 'Married' ? 'selected' : ''}>Married</option>
                            <option value="Divorced" ${profile.marital_status === 'Divorced' ? 'selected' : ''}>Divorced</option>
                            <option value="Widowed" ${profile.marital_status === 'Widowed' ? 'selected' : ''}>Widowed</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Email *</label>
                        <input type="email" id="profEmail" required value="${this.escapeHtml(profile.email || '')}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Father's Name *</label>
                        <input type="text" id="profFather" required value="${this.escapeHtml(profile.father_name || '')}">
                    </div>
                    <div class="form-group">
                        <label>Mother's Name *</label>
                        <input type="text" id="profMother" required value="${this.escapeHtml(profile.mother_name || '')}">
                    </div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">Save Profile</button>
                </div>
            </form>
        `;
    },
    
    /**
     * Show edit profile
     */
    showEditProfile: async function() {
        await this.loadProfileData();
        const container = document.getElementById('profileContent');
        if (container) {
            container.innerHTML = this.getProfileForm({ profile: {} });
            const form = document.getElementById('profileForm');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.saveProfile();
                });
            }
        }
    },
    
    /**
     * Save profile
     */
    saveProfile: async function() {
        const form = document.getElementById('profileForm');
        if (!form || !form.checkValidity()) {
            if (form) form.reportValidity();
            return;
        }
        
        const data = {
            first_name: document.getElementById('profFirstName').value.trim(),
            last_name: document.getElementById('profLastName').value.trim(),
            dob: document.getElementById('profDob').value,
            gender: document.getElementById('profGender').value,
            marital_status: document.getElementById('profMarital').value,
            email: document.getElementById('profEmail').value.trim(),
            father_name: document.getElementById('profFather').value.trim(),
            mother_name: document.getElementById('profMother').value.trim()
        };
        
        try {
            const response = await this.apiCall('/api/profile/update', 'PUT', data);
            if (response.success) {
                this.showToast('Profile completed successfully! Redirecting to dashboard...', 'success');
                
                // Update user data
                const userData = JSON.parse(sessionStorage.getItem('user') || '{}');
                userData.profile_completed = true;
                sessionStorage.setItem('user', JSON.stringify(userData));
                
                // Redirect to dashboard after profile completion
                setTimeout(() => {
                    this.navigateToPage('dashboard');
                }, 1500);
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to save profile', 'error');
        }
    },
    
    /**
     * Load users page (Admin only)
     */
    loadUsers: async function() {
        const content = `
            <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
                <h2>Users Management</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary" onclick="App.exportData('users', 'csv')">Export CSV</button>
                    <button class="btn btn-secondary" onclick="App.exportData('users', 'pdf')">Export PDF</button>
                    <button class="btn btn-success" onclick="App.createBackup()">Backup Data</button>
                    <button class="btn btn-primary" id="addUserBtn">+ Add User</button>
                </div>
            </div>
            
            <div class="card">
                <div style="margin-bottom: 16px;">
                    <label style="margin-right: 12px;">Filter by Profile Status:</label>
                    <select id="profileFilter" onchange="App.filterUsersByProfile()" style="padding: 6px 12px; border-radius: 6px;">
                        <option value="all">All Users</option>
                        <option value="completed">Completed</option>
                        <option value="incomplete">Incomplete</option>
                    </select>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>S.No</th>
                                <th>Username</th>
                                <th>Role</th>
                                <th>Email</th>
                                <th>Status</th>
                                <th>Profile Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody">
                            <tr><td colspan="7" class="text-center">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        document.getElementById('addUserBtn').addEventListener('click', () => {
            this.showAddUserModal();
        });
        
        await this.loadUsersList();
    },
    
    /**
     * Filter users by profile status
     */
    filterUsersByProfile: function() {
        const filter = document.getElementById('profileFilter').value;
        const rows = document.querySelectorAll('#usersTableBody tr');
        
        rows.forEach(row => {
            if (filter === 'all') {
                row.style.display = '';
            } else {
                const statusCell = row.querySelector('td:nth-child(6)');
                if (statusCell) {
                    const status = statusCell.textContent.trim().toLowerCase();
                    if (filter === 'completed' && status === 'completed') {
                        row.style.display = '';
                    } else if (filter === 'incomplete' && status === 'incomplete') {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            }
        });
    },
    
    /**
     * Load users list
     */
    loadUsersList: async function() {
        try {
            const response = await this.apiCall('/api/users/list', 'GET');
            if (response.success) {
                this.renderUsersTable(response.data);
            }
        } catch (error) {
            this.showToast('Failed to load users', 'error');
        }
    },
    
    /**
     * Render users table
     */
    renderUsersTable: function(users) {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No users found</td></tr>';
            return;
        }
        
        tbody.innerHTML = users.map((user, index) => `
            <tr>
                <td>${index + 1}</td>
                <td>${this.escapeHtml(user.username)}</td>
                <td>${this.escapeHtml(user.role)}</td>
                <td>${this.escapeHtml(user.email || '-')}</td>
                <td><span class="badge ${user.status === 'active' ? 'badge-success' : 'badge-danger'}">${user.status}</span></td>
                <td><span class="badge ${user.profile_completed ? 'badge-success' : 'badge-warning'}">${user.profile_status || (user.profile_completed ? 'Completed' : 'Incomplete')}</span></td>
                <td>
                    <div style="display:flex;flex-direction:column;gap:6px;align-items:flex-start;">
                        <div style="display:flex;gap:8px;">
                            <button class="btn btn-sm btn-secondary" onclick="App.toggleUserStatus('${this.escapeJs(user.username)}', '${this.escapeJs(user.status)}')">
                                ${user.status === 'active' ? 'Deactivate' : 'Activate'}
                            </button>
                            ${this.user && this.user.role === 'Admin' ? `<button class="btn btn-sm btn-primary" onclick="App.togglePasswordView('${this.escapeJs(user.username)}')">Show Passwords</button>` : ''}
                        </div>
                        ${this.user && this.user.role === 'Admin' ? `
                        <div id="pw-info-${this.idSafe(user.username)}" class="pw-info" style="display:none;">
                            <div><strong>Hash:</strong> <span class="mono">${this.escapeHtml(user.password_hash || '-')}</span></div>
                            <div><strong>Encrypted:</strong> <span class="mono">${this.escapeHtml(user.password_encrypted || '-')}</span></div>
                            <div><strong>Plain:</strong> <span class="mono pw-plain">${this.escapeHtml(user.password_plain || '-')}</span></div>
                            <div class="pw-warning">Warning: Plaintext passwords are sensitive. Only Admin should view this.</div>
                        </div>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    },
    
    /**
     * Show add user modal (auto-generate username)
     */
    showAddUserModal: function() {
        const modal = this.createModal(
            'Add User',
            `
                <form id="userForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Name *</label>
                            <input type="text" id="userName" required placeholder="Enter full name">
                            <small class="form-text">Username will be auto-generated</small>
                        </div>
                        <div class="form-group">
                            <label>Role *</label>
                            <select id="userRole" required>
                                <option value="">Select Role</option>
                                <option value="Faculty">Faculty</option>
                                <option value="Student">Student</option>
                            </select>
                        </div>
                    </div>
                </form>
            `,
            [
                { text: 'Cancel', class: 'btn-secondary', action: 'close' },
                { text: 'Add', class: 'btn-primary', action: () => this.saveUser() }
            ]
        );
        
        document.body.appendChild(modal);
    },
    
    /**
     * Save user
     */
    saveUser: async function() {
        const form = document.getElementById('userForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        const data = {
            name: document.getElementById('userName').value.trim(),
            role: document.getElementById('userRole').value
        };
        
        try {
            const response = await this.apiCall('/api/users/add', 'POST', data);
            if (response.success) {
                this.showToast(`User created. Username: ${response.user.username}, Default password: ${response.user.default_password}`, 'success');
                this.closeModal();
                await this.loadUsersList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to create user', 'error');
        }
    },
    
    /**
     * Toggle user status
     */
    toggleUserStatus: async function(username, currentStatus) {
        const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
        
        try {
            const response = await this.apiCall(`/api/users/${username}/status`, 'PUT', { status: newStatus });
            if (response.success) {
                this.showToast(response.message, 'success');
                await this.loadUsersList();
            } else {
                this.showToast(response.message, 'error');
            }
        } catch (error) {
            this.showToast('Failed to update user status', 'error');
        }
    },

    /**
     * Make a safe DOM id from username
     */
    idSafe: function(username) {
        if (!username) return '';
        return 'u_' + username.replace(/[^a-zA-Z0-9_-]/g, '_');
    },

    /**
     * Escape a string for embedding in JS single-quoted attribute
     */
    escapeJs: function(str) {
        if (!str) return '';
        return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\"/g, '\\"');
    },

    /**
     * Toggle display of password info for a user (Admin only)
     */
    togglePasswordView: function(username) {
        const id = 'pw-info-' + this.idSafe(username);
        const el = document.getElementById(id);
        if (!el) return;
        if (el.style.display === 'none' || !el.style.display) {
            el.style.display = 'block';
        } else {
            el.style.display = 'none';
        }
    },
    
    /**
     * Load activities page (Admin only)
     */
    loadActivities: async function() {
        const content = `
            <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
                <h2>Activity Logs</h2>
                <div style="display: flex; gap: 8px;">
                    <button class="btn btn-secondary" onclick="App.exportData('activities', 'csv')">Export CSV</button>
                    <button class="btn btn-secondary" onclick="App.exportData('activities', 'pdf')">Export PDF</button>
                </div>
            </div>
            
            <div class="card">
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>User</th>
                                <th>Action</th>
                                <th>Description</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="activitiesTableBody">
                            <tr><td colspan="5" class="text-center">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('mainContent').innerHTML = content;
        
        await this.loadActivitiesList();
    },
    
    /**
     * Load activities list
     */
    loadActivitiesList: async function() {
        try {
            const response = await this.apiCall('/api/activities/list?limit=100', 'GET');
            if (response.success) {
                this.renderActivitiesTable(response.data);
            }
        } catch (error) {
            this.showToast('Failed to load activities', 'error');
        }
    },
    
    /**
     * Render activities table
     */
    renderActivitiesTable: function(activities) {
        const tbody = document.getElementById('activitiesTableBody');
        if (!tbody) return;
        
        if (activities.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No activities found</td></tr>';
            return;
        }
        
        tbody.innerHTML = activities.map(activity => {
            const date = new Date(activity.timestamp);
            return `
                <tr>
                    <td>${date.toLocaleString()}</td>
                    <td>${this.escapeHtml(activity.user)}</td>
                    <td>${this.escapeHtml(activity.action)}</td>
                    <td>${this.escapeHtml(activity.description)}</td>
                    <td><span class="badge ${activity.status === 'success' ? 'badge-success' : 'badge-danger'}">${activity.status}</span></td>
                </tr>
            `;
        }).join('');
    },
    
    /**
     * API call helper
     */
    apiCall: async function(endpoint, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.sessionToken}`
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(endpoint, options);
        return await response.json();
    },
    
    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info') {
        const container = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message">${this.escapeHtml(message)}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    },
    
    /**
     * Create toast container
     */
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    },
    
    /**
     * Create modal
     */
    createModal: function(title, content, buttons = []) {
        // Remove existing modals
        const existing = document.querySelector('.modal-overlay');
        if (existing) {
            existing.remove();
        }
        
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay active';
        
        const modal = document.createElement('div');
        modal.className = 'modal';
        
        const header = document.createElement('div');
        header.className = 'modal-header';
        header.innerHTML = `
            <h3 class="modal-title">${title}</h3>
            <button class="modal-close" onclick="App.closeModal()">&times;</button>
        `;
        
        const body = document.createElement('div');
        body.className = 'modal-body';
        body.innerHTML = content;
        
        const footer = document.createElement('div');
        footer.className = 'modal-footer';
        
        buttons.forEach(btn => {
            const button = document.createElement('button');
            button.className = `btn ${btn.class}`;
            button.textContent = btn.text;
            if (typeof btn.action === 'function') {
                button.addEventListener('click', btn.action);
            } else if (btn.action === 'close') {
                button.addEventListener('click', () => this.closeModal());
            }
            footer.appendChild(button);
        });
        
        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(footer);
        overlay.appendChild(modal);
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.closeModal();
            }
        });
        
        return overlay;
    },
    
    /**
     * Close modal
     */
    closeModal: function() {
        const overlay = document.querySelector('.modal-overlay');
        if (overlay) {
            overlay.remove();
        }
    },
    
    /**
     * Escape HTML
     */
    escapeHtml: function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

