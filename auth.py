from flask import Blueprint, render_template, request, redirect, url_for, flash, session

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# --- In-memory user storage (for demonstration purposes) ---
# In a real application, you would use a database (e.g., SQLite, PostgreSQL, MongoDB)
# along with a proper password hashing library (e.g., Werkzeug's generate_password_hash, check_password_hash)
# Storing user data as: {email: {'password': 'hashed_password', 'nama': '...', 'jabatan': '...'}}
users = {}

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles user registration with email, nama, jabatan, password, and confirm password.
    - GET: Displays the registration form.
    - POST: Processes the registration form submission.
    """
    if request.method == 'POST':
        email = request.form['email']
        nama = request.form['nama']
        jabatan = request.form['jabatan']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Basic validation
        if not email or not nama or not jabatan or not password or not confirm_password:
            flash('Semua bidang wajib diisi.', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Password dan Konfirmasi Password tidak cocok.', 'error')
            return redirect(url_for('auth.register'))

        if email in users:
            flash('Email sudah terdaftar. Silakan gunakan email lain atau login.', 'error')
            return redirect(url_for('auth.register'))

        # Store user details (in a real app, hash the password before storing)
        users[email] = {
            'password': password, # In production, use generate_password_hash(password)
            'nama': nama,
            'jabatan': jabatan
        }
        flash('Pendaftaran berhasil! Silakan masuk.', 'success')
        return redirect(url_for('auth.login')) # Redirect to login after successful registration
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    - GET: Displays the login form.
    - POST: Processes the login form submission.
    """
    if request.method == 'POST':
        # Assuming login will still use username for now, or change to email if preferred
        # Based on the image, the login page still asks for 'Username', not 'Email'.
        # If you want login to use email, change 'username' field in login.html to 'email'
        # and update this logic accordingly. For now, keeping it consistent with the previous login.html
        username_or_email = request.form['username'] # Or 'email' if you change the login form
        password = request.form['password']

        if not username_or_email or not password:
            flash('Username/Email dan password wajib diisi.', 'error')
            return redirect(url_for('auth.login'))

        # Check if login is by email (assuming email is unique and used as primary key)
        # If login uses username, you would iterate through users to find by 'nama'
        user_data = users.get(username_or_email) # Try to get user by email as key

        if user_data and user_data['password'] == password: # In production, use check_password_hash
            session['username'] = user_data['nama'] # Store 'nama' in session for display
            session['email'] = username_or_email # Store email in session as primary identifier
            flash('Login berhasil!', 'success')
            return redirect(url_for('auth.dashboard')) # Redirect to a dashboard or home page
        else:
            flash('Email atau password salah.', 'error')
            return redirect(url_for('auth.login'))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """
    Logs out the current user by clearing the session.
    """
    session.pop('username', None) # Remove username from session
    session.pop('email', None) # Remove email from session
    flash('Anda telah keluar.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
def dashboard():
    """
    A simple dashboard page that requires login.
    """
    if 'email' in session: # Check session using email as the unique identifier
        # Pass the 'nama' to the dashboard for display
        return render_template('dashboard.html', username=users[session['email']]['nama'])
    else:
        flash('Silakan login untuk mengakses halaman ini.', 'error')
        return redirect(url_for('auth.login'))

