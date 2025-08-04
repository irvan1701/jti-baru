from flask import Flask, render_template, request, redirect, url_for, flash, session
from auth import auth_bp
from datetime import datetime
import locale
import os
from flask_bcrypt import Bcrypt
import mysql.connector
import requests
import json

app = Flask(__name__)

# Konfigurasi kunci rahasia dari variabel lingkungan atau gunakan default
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_here')

# Konfigurasi database MySQL
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'jti-new2')

bcrypt = Bcrypt(app)
app.register_blueprint(auth_bp)

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        return conn
    except mysql.connector.Error as err:
        flash(f"Error koneksi database: {err}", 'danger')
        print(f"Error koneksi database: {err}")
        return None

def is_admin():
    return 'logged_in' in session and session.get('role') == 'Admin'

def is_regular_user():
    return 'logged_in' in session and session.get('role') == 'User'

@app.route('/')
def index():
    if 'logged_in' not in session or not session['logged_in']:
        flash('Anda harus login terlebih dahulu.', 'warning')
        return redirect(url_for('auth.login'))
    return redirect(url_for('select_site'))

@app.route('/select_site')
def select_site():
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk memilih site.', 'warning')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    sites = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            user_role = session.get('role')
            user_id = session.get('user_id')

            if user_role in ['Admin', 'Viewer']:
                cursor.execute("SELECT id, name AS nama_site, location AS lokasi, image_name AS gambar_url FROM sites")
            elif user_id:
                cursor.execute("""
                    SELECT s.id, s.name AS nama_site, s.location AS lokasi, s.image_name AS gambar_url
                    FROM sites s
                    JOIN user_site_access usa ON s.id = usa.site_id
                    WHERE usa.user_id = %s
                """, (user_id,))
            
            sites = cursor.fetchall()

        except mysql.connector.Error as err:
            flash(f"Error saat mengambil daftar site: {err}", 'danger')
        finally:
            cursor.close()
            conn.close()

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('select_site.html', current_time=current_time, sites=sites)

@app.route('/select_chiller/<string:site_id>')
def select_chiller(site_id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk memilih chiller.', 'warning')
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    chillers = []
    site_name = ""
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT name FROM sites WHERE id = %s", (site_id,))
            site_info = cursor.fetchone()
            if site_info:
                site_name = site_info['name']

            cursor.execute("""
                SELECT id, chiller_num AS nama_chiller, model_number AS model, serial_number, 
                       power_kW, ton_of_refrigeration, image_name AS gambar_url
                FROM chillers
                WHERE site_id = %s
            """, (site_id,))
            chillers = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error saat mengambil daftar chiller: {err}", 'danger')
        finally:
            cursor.close()
            conn.close()
    
    session['current_site_id'] = site_id
    session['current_site_name'] = site_name

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('select_chiller.html', current_time=current_time, chillers=chillers, site_name=site_name)

@app.route('/monitor_chiller/<string:chiller_id>')
def monitor_chiller(chiller_id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk memantau chiller.', 'warning')
        return redirect(url_for('auth.login'))
    return redirect(url_for('test', chiller_id=chiller_id))

@app.route('/test')
def test():
    """
    Rute test yang membangun dasbor secara dinamis dari database,
    mengambil nilai aktual dari chiller_datas.
    """
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses halaman test.', 'warning')
        return redirect(url_for('auth.login'))

    chiller_id = request.args.get('chiller_id')
    chiller_details = {}
    latest_chiller_data = None
    last_updated_timestamp = None

    if chiller_id:
        try:
            # Mengambil data dari API
            response = requests.get(f'http://127.0.0.1:8000/chiller_datas/{chiller_id}')
            response.raise_for_status()
            
            raw_json_data = response.json()
            if raw_json_data:
                latest_chiller_data = raw_json_data[0]
                if 'timestamp' in latest_chiller_data:
                    last_updated_timestamp = datetime.fromisoformat(latest_chiller_data['timestamp'])
            
            # Ambil detail chiller dasar dari database
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT * FROM chillers WHERE id = %s", (chiller_id,))
                    chiller_details = cursor.fetchone()
                finally:
                    cursor.close()
                    conn.close()

        except requests.exceptions.RequestException as e:
            flash(f'Gagal mengambil data dari API: {e}', 'danger')
            print(f"Error fetching data from API: {e}")
        except Exception as e:
            flash(f'Gagal memproses data: {e}', 'danger')
            print(f"Error processing data: {e}")
            
    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    
    template_to_render = 'chiller_dashboard.html'
    if chiller_details and chiller_details.get('chiller_type'):
        specific_template = f"{chiller_details['chiller_type'].lower()}.html"
        if os.path.exists(os.path.join(app.template_folder, specific_template)):
            template_to_render = specific_template
        else:
            print(f"Warning: Template {specific_template} not found. Falling back to chiller_dashboard.html.")

    return render_template(
        template_to_render, 
        active_page='chiller_monitor', 
        current_time=current_time, 
        chiller=chiller_details,
        data=latest_chiller_data,
        last_updated_timestamp=last_updated_timestamp
    )


# Rute untuk halaman debug data
@app.route('/data_table')
def data_table():
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses halaman ini.', 'warning')
        return redirect(url_for('auth.login'))

    # Mock daftar chiller ID untuk dropdown
    chiller_ids = ["bxc2_sqc_1", "bxc2_sqc_2", "bxc2_sqc_3", "bxc2_sqc_4","menara_btpn_1", "menara_btpn_2", "menara_btpn_3", "menara_btpn_4"]
    selected_chiller_id = request.args.get('chiller_id', chiller_ids[0] if chiller_ids else None)
    
    data = None
    if selected_chiller_id:
        try:
            # Mengambil data dari API
            response = requests.get(f'http://127.0.0.1:8000/chiller_datas/{selected_chiller_id}')
            response.raise_for_status() # Cek jika ada bad status code
            
            raw_json_data = response.json()
            if raw_json_data:
                data = raw_json_data[0]

        except requests.exceptions.RequestException as e:
            flash(f'Gagal mengambil data dari API: {e}', 'danger')
            print(f"Error fetching data from API: {e}")
            
    return render_template('data_table.html', data=data, chiller_ids=chiller_ids, selected_chiller_id=selected_chiller_id)


@app.route('/dashboard')
def dashboard():
    """
    Dashboard route, requires login.
    """
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses dashboard.', 'warning')
        return redirect(url_for('auth.login'))

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('dashboard.html', current_time=current_time)


@app.route('/testing')
def testing():
    """
    Testing page route, renders template2.html.
    """
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses halaman testing.', 'warning')
        return redirect(url_for('auth.login'))

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('template2.html', current_time=current_time)

@app.route('/testinggg')
def testingg():
    """
    Another testing page route with sample gauge data.
    """
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses halaman testing.', 'warning')
        return redirect(url_for('auth.login'))

    # Sample data for the gauges
    gauges = [
        {"label": "Evap Pressure", "value": 120},
        {"label": "Temp Sensor", "value": 75},
        {"label": "Speed", "value": 150},
        {"label": "Humidity", "value": 30}
    ]
    return render_template('template2.html', gauges=gauges)


@app.route('/report')
def report():
    """
    Report page route.
    """
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses halaman laporan.', 'warning')
        return redirect(url_for('auth.login'))

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('report.html', current_time=current_time)


@app.route('/manage_users')
def manage_users():
    """
    Halaman untuk mengelola daftar pengguna. Hanya dapat diakses oleh Admin.
    """
    if not is_admin():
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    users = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Mengambil semua pengguna (kecuali user yang sedang login, opsional)
            cursor.execute("SELECT id, nama, email, jabatan, role FROM users")
            users = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error saat mengambil daftar pengguna: {err}", 'danger')
            print(f"Error saat mengambil daftar pengguna: {err}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('manage_users.html', current_time=current_time, users=users)


@app.route('/manage_user_access/<int:user_id>', methods=['GET', 'POST'])
def manage_user_access(user_id):
    """
    Halaman untuk mengelola akses site untuk pengguna tertentu. Hanya dapat diakses oleh Admin.
    """
    if not is_admin():
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    user_info = None
    all_sites = []
    assigned_site_ids = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Ambil info pengguna
            cursor.execute("SELECT id, nama, email, role FROM users WHERE id = %s", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                flash('Pengguna tidak ditemukan.', 'danger')
                return redirect(url_for('manage_users'))

            # Ambil semua site
            cursor.execute("SELECT id, name AS nama_site FROM sites")
            all_sites = cursor.fetchall()

            # Ambil site yang sudah di-assign ke pengguna ini
            cursor.execute("SELECT site_id FROM user_site_access WHERE user_id = %s", (user_id,))
            assigned_site_ids = [row['site_id'] for row in cursor.fetchall()]

            if request.method == 'POST':
                selected_site_ids = request.form.getlist('sites') # Ambil daftar site yang dicentang
                
                # Hapus semua akses site yang ada untuk pengguna ini
                cursor.execute("DELETE FROM user_site_access WHERE user_id = %s", (user_id,))
                
                # Masukkan akses site yang baru dipilih
                for site_id in selected_site_ids:
                    cursor.execute("INSERT INTO user_site_access (user_id, site_id) VALUES (%s, %s)", (user_id, site_id))
                
                conn.commit()
                flash(f'Akses site untuk {user_info["nama"]} berhasil diperbarui.', 'success')
                return redirect(url_for('manage_users')) # Kembali ke daftar pengguna

        except mysql.connector.Error as err:
            flash(f"Error saat mengelola akses pengguna: {err}", 'danger')
            print(f"Error saat mengelola akses pengguna: {err}")
            if conn:
                conn.rollback() # Rollback transaksi jika ada error
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        return redirect(url_for('manage_users')) # Redirect jika koneksi DB gagal

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('manage_user_access.html',
                           current_time=current_time,
                           user_info=user_info,
                           all_sites=all_sites,
                           assigned_site_ids=assigned_site_ids)


@app.route('/user_add_account', methods=['GET', 'POST'])
def user_add_account():
    """
    Halaman untuk pengguna dengan peran 'User' untuk menambah akun baru
    yang terbatas pada site mereka sendiri.
    """
    if not is_regular_user():
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    assigned_sites_for_creator = []
    current_user_id = session.get('user_id')

    if conn and current_user_id:
        cursor = conn.cursor(dictionary=True)
        try:
            # Ambil site yang diizinkan untuk pengguna yang sedang login
            cursor.execute("""
                SELECT s.id, s.name AS nama_site
                FROM sites s
                JOIN user_site_access usa ON s.id = usa.site_id
                WHERE usa.user_id = %s
            """, (current_user_id,))
            assigned_sites_for_creator = cursor.fetchall()
            
            if not assigned_sites_for_creator:
                flash('Anda belum memiliki site yang ditetapkan untuk menambah akun.', 'warning')
                return redirect(url_for('index'))

            if request.method == 'POST':
                nama = request.form.get('nama')
                email = request.form.get('email')
                jabatan = request.form.get('jabatan')
                password = request.form.get('password')
                selected_site_id = request.form.get('site_id') # Ambil site_id dari form

                # Validasi input sederhana
                if not nama or not email or not password or not jabatan or not selected_site_id:
                    flash('Semua kolom harus diisi.', 'danger')
                    return render_template('user_add_account.html', current_time=datetime.now().strftime("%A, %d %B %Y, %H:%M:%S"), assigned_sites=assigned_sites_for_creator)

                # Validasi bahwa site yang dipilih adalah salah satu site yang diizinkan untuk pembuat akun
                allowed_site_ids = [s['id'] for s in assigned_sites_for_creator]
                if selected_site_id not in allowed_site_ids:
                    flash('Site yang dipilih tidak valid atau Anda tidak memiliki akses ke site tersebut.', 'danger')
                    return render_template('user_add_account.html', current_time=datetime.now().strftime("%A, %d %B %Y, %H:%M:%S"), assigned_sites=assigned_sites_for_creator)

                # Periksa apakah email sudah terdaftar
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash('Email sudah terdaftar. Silakan gunakan email lain.', 'danger')
                else:
                    # Hash password sebelum menyimpan
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    
                    # Masukkan data pengguna baru ke database dengan role 'User'
                    cursor.execute(
                        "INSERT INTO users (nama, email, jabatan, password, role) VALUES (%s, %s, %s, %s, %s)",
                        (nama, email, jabatan, hashed_password, 'User') # Role otomatis 'User'
                    )
                    new_user_id = cursor.lastrowid # Dapatkan ID pengguna yang baru dibuat
                    
                    # Tetapkan akses site untuk pengguna baru
                    cursor.execute("INSERT INTO user_site_access (user_id, site_id) VALUES (%s, %s)", (new_user_id, selected_site_id))
                    
                    conn.commit()
                    flash('Akun baru berhasil ditambahkan dan ditetapkan ke site yang dipilih!', 'success')
                    return redirect(url_for('user_add_account')) # Kembali ke halaman tambah akun

        except mysql.connector.Error as err:
            flash(f"Error saat menambah akun: {err}", 'danger')
            print(f"Error saat menambah akun: {err}")
            if conn:
                conn.rollback() # Rollback transaksi jika ada error
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        # Jika koneksi DB gagal atau user_id tidak ada
        flash('Terjadi masalah saat memuat data site. Silakan coba lagi.', 'danger')
        return redirect(url_for('index'))

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('user_add_account.html', current_time=current_time, assigned_sites=assigned_sites_for_creator)


@app.route('/add_user_by_admin', methods=['GET', 'POST'])
def add_user_by_admin():
    """
    Halaman untuk Admin menambahkan akun baru dengan peran dan akses site yang dipilih.
    """
    if not is_admin():
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    all_sites = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Ambil semua site untuk ditampilkan di formulir
            cursor.execute("SELECT id, name AS nama_site FROM sites")
            all_sites = cursor.fetchall()

            if request.method == 'POST':
                nama = request.form.get('nama')
                email = request.form.get('email')
                jabatan = request.form.get('jabatan')
                password = request.form.get('password')
                role = request.form.get('role')
                selected_site_ids = request.form.getlist('sites') # Ambil daftar site yang dicentang

                # Validasi input
                if not nama or not email or not password or not jabatan or not role:
                    flash('Semua kolom wajib diisi.', 'danger')
                    return render_template('add_user_by_admin.html', current_time=datetime.now().strftime("%A, %d %B %Y, %H:%M:%S"), all_sites=all_sites)

                # Periksa apakah email sudah terdaftar
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash('Email sudah terdaftar. Silakan gunakan email lain.', 'danger')
                else:
                    # Hash password
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    
                    # Masukkan pengguna baru
                    cursor.execute(
                        "INSERT INTO users (nama, email, jabatan, password, role) VALUES (%s, %s, %s, %s, %s)",
                        (nama, email, jabatan, hashed_password, role)
                    )
                    new_user_id = cursor.lastrowid

                    # Tetapkan akses site jika peran bukan Admin
                    if role in ['Viewer', 'User']:
                        for site_id in selected_site_ids:
                            cursor.execute("INSERT INTO user_site_access (user_id, site_id) VALUES (%s, %s)", (new_user_id, site_id))
                    
                    conn.commit()
                    flash(f'Pengguna {nama} ({role}) berhasil ditambahkan!', 'success')
                    return redirect(url_for('manage_users')) # Kembali ke daftar pengguna

        except mysql.connector.Error as err:
            flash(f"Error saat menambah pengguna: {err}", 'danger')
            print(f"Error saat menambah pengguna: {err}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        flash('Terjadi masalah saat memuat data site. Silakan coba lagi.', 'danger')
        return redirect(url_for('manage_users'))

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('add_user_by_admin.html', current_time=current_time, all_sites=all_sites)


if __name__ == '__main__':
    # Set locale to Indonesian for date and time formatting
    try:
        locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Indonesian_Indonesia.1252')
        except locale.Error:
            print("Warning: Indonesian locale not found. Date/time may not be formatted correctly.")
    app.run(debug=True, host='0.0.0.0')

