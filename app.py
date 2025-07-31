from flask import Flask, render_template, request, redirect, url_for, flash, session
from auth import auth_bp # Impor Blueprint dari auth.py
from datetime import datetime
import locale
import os # Import os for environment variables
from flask_bcrypt import Bcrypt # Import Bcrypt
import mysql.connector # Import MySQL connector

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
    parameters_by_section = {}
    last_updated_timestamp = None # Initialize to None

    # Mapping dictionary for parameter names to chiller_datas column names
    parameter_data_map = {
        'LWT': 'evap_lwt',
        'RWT': 'evap_rwt',
        'Evap Pressure': 'evap_pressure',
        'Cond LWT': 'cond_lwt',
        'Cond RWT': 'cond_rwt',
        'Cond Pressure': 'cond_pressure',
        'Discharge Temp': 'discharge_temp',
        'Oil Sump Temp': 'oil_sump_temp',
        'Oil Discharge PSI': 'oil_sump_pressure', # Assuming this is the correct column
        'VSD Out Voltage': 'vsd_out_voltage',
        'Motor PH A Current': 'vsd_ph_a_current',
        'Motor PH B Current': 'vsd_ph_b_current',
        'Motor PH C Current': 'vsd_ph_c_current',
        # Add all other parameter mappings here
        'Evap Satur Temp': 'evap_satur_temp',
        'Evap STD': 'evap_std',
        'Evap Refri Lvl': 'evap_refri_lvl',
        'Cond STD': 'cond_std',
        'Cond Refri Lvl': 'cond_refri_lvl',
        'Cond Refri Lvl SP': 'cond_refri_lvl_sp',
        'Drop Leg Refri Temp': 'drop_leg_refri_temp',
        'Oil Pressure Diff': 'oil_pressure_diff',
        'Oil Sump Pressure': 'oil_sump_pressure',
        'Oil Pump Pressure': 'oil_pump_pressure',
        'FLA': 'fla',
        'Input Power': 'input_power',
        'Input KWH': 'input_kwh',
        'Operating Hour': 'operating_hour',
        'Number of Start': 'number_of_start',
        'Act Current Limit': 'act_current_limit',
        'VSD Out Freq': 'vsd_out_freq',
        'Mtr Wind PH A Temp': 'mtr_wind_ph_a_temp',
        'Mtr Wind PH B Temp': 'mtr_wind_ph_b_temp',
        'Mtr Wind PH C Temp': 'mtr_wind_ph_c_temp',
        'Status': 'status',
        'Warning': 'warning',
        'Alarm': 'alarm',
        'Safety Fault': 'safety_fault',
        'Cycling Fault': 'cycling_fault',
        'Warning Fault': 'warning_fault',
        'Operating Code': 'operating_code',
        'Liq Line Solenoid': 'liq_line_solenoid',
        'CH Liq Pump STS': 'ch_liq_pump_sts',
        'Panel Stop Switch STS': 'panel_stop_switch_sts',
        'CH Liq Flow Switch': 'ch_liq_flow_switch',
        'Cond Liq Flow Switch': 'cond_liq_flow_switch',
        'Cond Liq Pump STS': 'cond_liq_pump_sts',
        'CH1 Evap RWT Fahrenheit': 'ch1_evap_rwt_fahrenheit',
        'CH1 Evap LWT Fahrenheit': 'ch1_evap_lwt_fahrenheit',
        'CH2 Evap RWT Fahrenheit': 'ch2_evap_rwt_fahrenheit',
        'CH2 Evap LWT Fahrenheit': 'ch2_evap_lwt_fahrenheit',
        'CH3 Evap RWT Fahrenheit': 'ch3_evap_rwt_fahrenheit',
        'CH3 Evap LWT Fahrenheit': 'ch3_evap_lwt_fahrenheit',
        'CH4 Evap RWT Fahrenheit': 'ch4_evap_rwt_fahrenheit',
        'CH4 Evap LWT Fahrenheit': 'ch4_evap_lwt_fahrenheit',
        'Leav CH Liq SP': 'leav_ch_liq_sp',
        'Evap RWT Fahrenheit': 'evap_rwt_fahrenheit',
        'Evap LWT Fahrenheit': 'evap_lwt_fahrenheit',
        'VSD Input Power': 'VSD_Input_Power',
        'VSD Input KWH': 'VSD_Input_KWH',
        'Evap Refri Temp': 'Evap_Refri_Temp',
        'Vsd In Amb Temp': 'Vsd_In_Amb_Temp',
        'Sys1 Disch Temp': 'Sys1_Disch_Temp',
        'Sys1 Oil Press': 'Sys1_Oil_Press',
        'Sys1 Evap Press': 'Sys1_Evap_Press',
        'Sys1 Disch Press': 'Sys1_Disch_Press',
        'Sys1 Comp FLA': 'Sys1_Comp_FLA',
        'Sys1 Run Hour': 'Sys1_Run_Hour',
        'Sys2 Oil Press': 'Sys2_Oil_Press',
        'Sys2 Suct Press': 'Sys2_Suct_Press',
        'Sys2 Disch Press': 'Sys2_Disch_Press',
        'Sys2 Comp FLA': 'Sys2_Comp_FLA',
        'Sys2 Run Hour': 'Sys2_Run_Hour',
        'Chiller Run': 'Chiller_Run',
        'Chiller Alarm': 'Chiller_Alarm',
        'Fault Code': 'Fault_Code',
        'Sys1 Suct Temp': 'Sys1_Suct_Temp',
        'Amb Air Temp': 'Amb_Air_Temp',
        'Sys1 Suct Superheat': 'Sys1_Suct_Superheat',
        'Sys1 EEV Out Pct': 'Sys1_EEV_Out_Pct',
        'Sys1 Com1 Hour': 'Sys1_Com1_Hour',
        'Sys1 Com2 Hour': 'Sys1_Com2_Hour',
        'Sys1 Com3 Hour': 'Sys1_Com3_Hour',
        'Sys2 Com1 Hour': 'Sys2_Com1_Hour',
        'Sys2 Com2 Hour': 'Sys2_Com2_Hour',
        'Sys2 Com3 Hour': 'Sys2_Com3_Hour',
        'Sys1 Com1 Run': 'Sys1_Com1_Run',
        'Sys1 Com2 Run': 'Sys1_Com2_Run',
        'Sys1 Com3 Run': 'Sys1_Com3_Run',
        'Sys2 Com1 Run': 'Sys2_Com1_Run',
        'Sys2 Com2 Run': 'Sys2_Com2_Run',
        'Sys2 Com3 Run': 'Sys2_Com3_Run',
        'Sys2 Suct Temp': 'Sys2_Suct_Temp',
        'Sys2 Suct Superheat': 'Sys2_Suct_Superheat',
        'Sys2 EEV Out Pct': 'Sys2_EEV_Out_Pct',
        'Sys1 Disch Superheat': 'Sys1_Disch_Superheat',
        'Sys2 Disch Temp': 'Sys2_Disch_Temp',
        'Sys2 Disch Superheat': 'Sys2_Disch_Superheat',
        'Sys1 Fault Code': 'Sys1_Fault_Code',
        'Sys2 Fault Code': 'Sys2_Fault_Code',
        'Sys1 Cond Temp': 'Sys1_Cond_Temp',
        'Out Amb Temp': 'Out_Amb_Temp',
        'Sys1 Eductor Temp': 'Sys1_Eductor_Temp',
        'Sys2 Eductor Temp': 'Sys2_Eductor_Temp',
        'Sys1 Alarm': 'Sys1_Alarm',
        'Sys2 Alarm': 'Sys2_Alarm',
        'Sys1 Warning Code': 'Sys1_Warning_Code',
        'Sys2 Warning Code': 'Sys2_Warning_Code',
        'Sys1 Fan Power': 'Sys1_Fan_Power',
        'Sys1 Comp Power': 'Sys1_Comp_Power',
        'Sys2 Fan Power': 'Sys2_Fan_Power',
        'Sys2 Comp Power': 'Sys2_Comp_Power',
        'Motor Ph A Current': 'Motor_Ph_A_Current',
        'Motor Ph B Current': 'Motor_Ph_B_Current',
        'Motor Ph C Current': 'Motor_Ph_C_Current',
        'Motor Ph A Voltage': 'Motor_Ph_A_Voltage',
        'Motor Ph B Voltage': 'Motor_Ph_B_Voltage',
        'Motor Ph C Voltage': 'Motor_Ph_C_Voltage',
        'Seal Press Diff': 'Seal_Press_Diff',
        'Filter Diff Press': 'Filter_Diff_Press',
        'Output Voltage': 'Output_Voltage',
    }

    if chiller_id:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # 1. Ambil detail chiller dasar
                cursor.execute("SELECT * FROM chillers WHERE id = %s", (chiller_id,))
                chiller_details = cursor.fetchone()

                # 2. Ambil data terbaru dari chiller_datas untuk chiller ini
                latest_chiller_data = None
                cursor.execute(
                    "SELECT * FROM chiller_datas WHERE chiller_id = %s ORDER BY timestamp DESC LIMIT 1",
                    (chiller_id,)
                )
                latest_chiller_data = cursor.fetchone()
                
                if latest_chiller_data and 'timestamp' in latest_chiller_data:
                    last_updated_timestamp = latest_chiller_data['timestamp']

                # 3. Ambil semua parameter konfigurasi untuk chiller ini
                query = """
                    SELECT
                        p.name, p.section, p.gauge_type, p.units, p.min_value, p.max_value,
                        cp.safe_range_low, cp.safe_range_high
                    FROM chiller_parameters cp
                    JOIN parameters p ON cp.parameter_id = p.id
                    WHERE cp.chiller_id = %s
                    ORDER BY p.section, p.id
                """
                cursor.execute(query, (chiller_id,))
                all_parameters = cursor.fetchall()

                # 4. Kelompokkan parameter berdasarkan bagian (section) dan isi nilai aktual
                for param in all_parameters:
                    section = param['section']
                    if section not in parameters_by_section:
                        parameters_by_section[section] = []
                    
                    # Dapatkan nama kolom dari mapping dictionary
                    data_col_name = parameter_data_map.get(param['name'])

                    # Ambil nilai aktual dari latest_chiller_data menggunakan data_col_name
                    if latest_chiller_data and data_col_name and data_col_name in latest_chiller_data:
                        param['current_value'] = latest_chiller_data[data_col_name]
                    else:
                        param['current_value'] = None # Atau nilai default lainnya jika data tidak ditemukan

                    parameters_by_section[section].append(param)

            except mysql.connector.Error as err:
                print(f"Error fetching dynamic dashboard data: {err}")
            finally:
                cursor.close()
                conn.close()

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    
    # Tentukan template berdasarkan chiller_type
    template_to_render = 'chiller_dashboard.html' # Default ke template universal
    if chiller_details and chiller_details.get('chiller_type'):
        # Konversi chiller_type ke nama file template (misal: 'BTPN_Type' -> 'btpn_type.html')
        specific_template = f"{chiller_details['chiller_type'].lower()}.html"
        # Periksa apakah template spesifik ada, jika tidak, gunakan default
        if os.path.exists(os.path.join(app.template_folder, specific_template)):
            template_to_render = specific_template
        else:
            print(f"Warning: Template {specific_template} not found. Falling back to chiller_dashboard.html.")

    return render_template(
        template_to_render, 
        active_page='chiller_monitor', 
        current_time=current_time, 
        chiller=chiller_details,
        sections=parameters_by_section,
        last_updated_timestamp=last_updated_timestamp
    )


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