from flask import Flask, render_template, request, redirect, url_for, flash, session
from auth import auth_bp # Impor Blueprint dari auth.py
from datetime import datetime
import locale

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Ganti dengan kunci rahasia yang kuat dan unik

# Daftarkan Blueprint autentikasi
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    """
    Rute utama yang mengarahkan ke halaman login.
    """
    return redirect(url_for('auth.login')) # Mengarahkan ke halaman login dari blueprint auth
@app.route('/tes')  # Mengubah endpoint dari '/' menjadi '/tes'
def home():
    # Mengambil waktu saat ini dan memformatnya
    # Contoh format: Rabu, 16 Juli 2025, 14:42:02
    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('select_site.html', current_time=current_time)

@app.route('/dashboard')  # Mengubah endpoint dari '/' menjadi '/tes'
def dashboard():
    # Mengambil waktu saat ini dan memformatnya
    # Contoh format: Rabu, 16 Juli 2025, 14:42:02
    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('dashboard.html', current_time=current_time)

@app.route('/chillers') # <<<<< Rute baru untuk halaman chiller
def chillers_page():
    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('select_chiller.html', current_time=current_time)

@app.route('/testing') # <<<<< Rute baru untuk halaman chiller
def testing():
    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('template2.html', current_time=current_time)








@app.route('/testinggg')
def testingg():
    # Sample data for the gauges
    gauges = [
        {"label": "Evap Pressure", "value": 120},
        {"label": "Temp Sensor", "value": 75},
        {"label": "Speed", "value": 150},
        {"label": "Humidity", "value": 30}
    ]
    return render_template('template2.html', gauges=gauges)

@app.route('/test')
def test():
    return render_template('template2.html', active_page='dashboard')

@app.route('/report')
def report():
    return render_template('sidebar.html', active_page='report') # Example of another page

@app.route('/manage_user')
def manage_user():
    return render_template('sidebar.html', active_page='manage_user') 





if __name__ == '__main__':
    # Jalankan aplikasi dalam mode debug untuk pengembangan.
    # Pastikan debug diatur ke False di lingkungan produksi.
    app.run(debug=True, host='0.0.0.0', port=5020)

