from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import mysql.connector
from flask_bcrypt import Bcrypt # Import Bcrypt

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt() # Inisialisasi Bcrypt (akan diinisialisasi dengan app di app.py)

# Fungsi untuk mendapatkan koneksi database
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB'],
            port=current_app.config['MYSQL_PORT']
        )
        return conn
    except mysql.connector.Error as err:
        flash(f"Error koneksi database: {err}", 'danger')
        print(f"Error koneksi database: {err}")
        return None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Menggunakan .get() untuk menghindari KeyError jika bidang tidak ada
        nama = request.form.get('nama')
        email = request.form.get('email')
        jabatan = request.form.get('jabatan')
        password = request.form.get('password')
        role = 'Admin' # Role otomatis diatur sebagai 'Admin'

        # Validasi input sederhana, 'role' tidak lagi divalidasi karena otomatis
        if not nama or not email or not password or not jabatan:
            flash('Semua kolom harus diisi!', 'danger')
            return render_template('register.html')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Periksa apakah email sudah terdaftar
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash('Email sudah terdaftar. Silakan gunakan email lain.', 'danger')
                else:
                    # Hash password sebelum menyimpan
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    
                    # Masukkan data pengguna baru ke database
                    cursor.execute(
                        "INSERT INTO users (nama, email, jabatan, password, role) VALUES (%s, %s, %s, %s, %s)",
                        (nama, email, jabatan, hashed_password, role)
                    )
                    conn.commit()
                    flash('Registrasi berhasil! Silakan login.', 'success')
                    return redirect(url_for('auth.login'))
            except mysql.connector.Error as err:
                flash(f"Error saat registrasi: {err}", 'danger')
                print(f"Error saat registrasi: {err}")
            finally:
                cursor.close()
                conn.close()
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email') # Menggunakan .get()
        password = request.form.get('password') # Menggunakan .get()

        # Validasi dasar untuk login
        if not email or not password:
            flash('Email dan password harus diisi.', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Cari pengguna berdasarkan email
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if user and bcrypt.check_password_hash(user['password'], password):
                    session['logged_in'] = True
                    session['user_id'] = user['id']
                    session['nama'] = user['nama']
                    session['email'] = user['email']
                    session['role'] = user['role']
                    flash('Login berhasil!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Email atau password salah.', 'danger')
            except mysql.connector.Error as err:
                flash(f"Error saat login: {err}", 'danger')
                print(f"Error saat login: {err}")
            finally:
                cursor.close()
                conn.close()
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('nama', None)
    session.pop('email', None)
    session.pop('role', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('auth.login'))

# Inisialisasi Bcrypt di luar Blueprint agar dapat diakses oleh aplikasi Flask
@auth_bp.record_once
def record_bcrypt(state):
    global bcrypt
    bcrypt = Bcrypt(state.app)

