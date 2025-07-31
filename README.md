# JTI BAS Chiller Monitoring Dashboard

## Gambaran Umum Proyek

Proyek ini adalah Dashboard Pemantauan Chiller berbasis web yang dibangun dengan Flask. Aplikasi ini memungkinkan pengguna untuk memantau berbagai parameter chiller industri, mengelola akses pengguna, dan melihat dasbor spesifik situs atau spesifik jenis chiller. Aplikasi ini dilengkapi dengan sistem otentikasi yang kuat dan mesin templating dinamis yang menyesuaikan tata letak dasbor berdasarkan jenis chiller yang ditentukan dalam database, menjadikannya sangat skalabel dan mudah dipelihara.okay 

## Fitur

*   **Otentikasi Pengguna:** Registrasi pengguna, login, dan logout yang aman dengan hashing kata sandi (Bcrypt).
*   **Kontrol Akses Berbasis Peran:** Peran pengguna yang berbeda (Admin, User, Viewer) dengan izin yang bervariasi.
*   **Manajemen Situs:** Pengguna dapat memilih situs untuk melihat chiller terkait. Admin dapat mengelola akses pengguna ke situs tertentu.
*   **Pemantauan Chiller:** Melihat data (placeholder) real-time untuk chiller individual, termasuk berbagai parameter, rentang aman, dan nilai saat ini.
*   **Templating Dasbor Dinamis:** Tata letak dasbor dan parameter yang ditampilkan secara otomatis menyesuaikan berdasarkan `chiller_type` yang ditentukan dalam database, menghilangkan kebutuhan akan file HTML terpisah yang di-hardcode untuk setiap instance chiller.
*   **Manajemen Pengguna (Admin):** Admin dapat menambahkan pengguna baru, menetapkan peran, dan mengelola akses situs untuk pengguna yang sudah ada.
*   **Pembuatan Akun (Pengguna Biasa):** Pengguna biasa dapat menambahkan akun pengguna baru, terbatas pada situs yang mereka miliki aksesnya.

## Prasyarat

Sebelum menjalankan aplikasi ini, pastikan Anda telah menginstal yang berikut:

*   **Python 3.x**
*   **MySQL Database Server**
*   **pip** (penginstal paket Python)

## Instruksi Penyiapan

### 1. Kloning Repositori

```bash
git clone <url_repositori>
cd new-client/new-client
```

### 2. Penyiapan Database

Aplikasi ini menggunakan MySQL.

a.  **Buat Database:**
    Buat database MySQL baru (misalnya, `jti-new2`).

b.  **Konfigurasi Koneksi Database:**
    Buka `app.py` dan konfigurasikan detail koneksi MySQL Anda. Sangat disarankan untuk menggunakan variabel lingkungan untuk produksi:

    ```python
    app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', '127.0.0.1')
    app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'jti-new2')
    ```

c.  **Impor Skema Awal:**
    Jalankan skema SQL dari file `gateway-sql.sql` (atau yang serupa) yang sudah ada untuk membuat tabel `users`, `sites`, `chillers`, dan `user_site_access`.

d.  **Buat Tabel Dasbor Dinamis Baru:**
    Jalankan perintah SQL berikut untuk membuat tabel `parameters` dan `chiller_parameters`:

    ```sql
    CREATE TABLE parameters (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        section VARCHAR(100),
        gauge_type VARCHAR(50) NOT NULL,
        units VARCHAR(20),
        min_value FLOAT DEFAULT 0,
        max_value FLOAT DEFAULT 100
    );

    CREATE TABLE chiller_parameters (
        id INT AUTO_INCREMENT PRIMARY KEY,
        chiller_id VARCHAR(100) NOT NULL, -- PENTING: Harus cocok dengan tipe chillers.id
        parameter_id INT NOT NULL,
        safe_range_low FLOAT,
        safe_range_high FLOAT,
        FOREIGN KEY (chiller_id) REFERENCES chillers(id) ON DELETE CASCADE,
        FOREIGN KEY (parameter_id) REFERENCES parameters(id) ON DELETE CASCADE
    );
    ```

e.  **Tambahkan Kolom `chiller_type` ke Tabel `chillers`:**
    Kolom ini sangat penting untuk templating dinamis.

    ```sql
    ALTER TABLE chillers
    ADD COLUMN chiller_type VARCHAR(50) DEFAULT 'default_type';
    ```

f.  **Isi Tabel `parameters` dan `chiller_parameters`:**
    Masukkan definisi parameter spesifik Anda ke dalam tabel `parameters` dan tautkan ke chiller Anda di tabel `chiller_parameters`.

    **Contoh data `parameters`:**
    ```sql
    INSERT INTO parameters (name, section, gauge_type, units, min_value, max_value) VALUES
    ('LWT', 'Evaporator', 'linear-gauge', '°C', 0, 25),
    ('RWT', 'Evaporator', 'linear-gauge', '°C', 0, 25),
    ('Evap Pressure', 'Evaporator', 'radial-gauge', 'PSI', 235, 520),
    -- ... tambahkan semua parameter Anda
    ('VSD Out Voltage', 'Details', 'info-card', 'V', 0, 500);
    ```

    **Contoh data `chiller_parameters` (ganti ID dengan ID chiller Anda yang sebenarnya):**
    ```sql
    INSERT INTO chiller_parameters (chiller_id, parameter_id, safe_range_low, safe_range_high) VALUES
    ('bxc2_chiller_1', 1, 5.50, 8.80), -- LWT untuk bxc2_chiller_1
    ('bxc2_chiller_1', 3, 220.64, 275.80), -- Evap Pressure untuk bxc2_chiller_1
    ('menara_btpn_2', 1, 6.0, 9.5), -- LWT untuk menara_btpn_2 (rentang aman berbeda)
    ('menara_btpn_2', 10, 380.0, 420.0); -- VSD Out Voltage untuk menara_btpn_2
    -- ... tautkan semua parameter yang relevan untuk setiap chiller
    ```

g.  **Perbarui Tabel `chillers` dengan `chiller_type`:**
    Tetapkan `chiller_type` ke setiap chiller di tabel `chillers` Anda. Jenis ini akan sesuai dengan file template HTML tertentu.

    ```sql
    UPDATE chillers SET chiller_type = 'BTPN_Type' WHERE id = 'menara_btpn_2';
    UPDATE chillers SET chiller_type = 'BXC2_Type' WHERE id = 'bxc2_chiller_1';
    -- ... perbarui untuk semua chiller Anda
    ```

### 3. Instal Dependensi Python

```bash
pip install -r requirements.txt
```

### 4. Variabel Lingkungan (Opsional tapi Disarankan)

Untuk produksi, atur kunci rahasia Flask Anda sebagai variabel lingkungan:

```bash
# Di Windows
set FLASK_SECRET_KEY=kunci_rahasia_super_anda

# Di Linux/macOS
export FLASK_SECRET_KEY=kunci_rahasia_super_anda
```

Jika tidak diatur, `app.py` akan menggunakan kunci default.

### 5. Buat Template Jenis Chiller

Untuk setiap `chiller_type` unik yang Anda definisikan di tabel `chillers` Anda, Anda perlu membuat file template HTML yang sesuai di direktori `templates/`.

**Aturan Penamaan Template:**
Jika `chiller_type` dalam database adalah `'Jenis_Chiller_Saya'`, maka nama file template harus `jenis_chiller_saya.html`.

**Contoh:**
*   Jika `chiller_type = 'BTPN_Type'`, buat `templates/btpn_type.html`.
*   Jika `chiller_type = 'BXC2_Type'`, buat `templates/bxc2_type.html`.
*   Jika `chiller_type = 'Default_Type'`, buat `templates/default_type.html`.

Template ini akan berisi tata letak, gauge, dan tabel parameter spesifik untuk jenis chiller tersebut. Anda dapat menyalin struktur dari `template2.html` atau `BTPN.html` sebagai titik awal dan menyesuaikannya.

### 6. Struktur Proyek (File Kunci)

```
.
├── app.py                  # Aplikasi Flask utama, routing, dan interaksi database
├── auth.py                 # Blueprint Otentikasi (login, register, logout)
├── requirements.txt        # Dependensi Python
├── static/                 # Aset statis (CSS, JS, gambar, ikon)
│   ├── css/
│   │   ├── dashboard_v2.css # Styling dasbor utama (diperbarui untuk tata letak dinamis)
│   │   ├── login.css
│   │   └── style.css
│   ├── images/             # Gambar chiller dan situs
│   └── js/                 # JavaScript untuk gauge dan fungsionalitas lainnya
└── templates/              # Template HTML
    ├── add_user_by_admin.html
    ├── chiller_dashboard.html # BARU: Template universal untuk dasbor dinamis
    ├── login.html
    ├── manage_user_access.html
    ├── manage_users.html
    ├── register.html
    ├── select_chiller.html
    ├── select_site.html
    ├── sidebar.html        # Template dasar untuk tata letak yang konsisten
    ├── template.html       # Contoh gauge lama (bisa dihapus)
    ├── tes.html            # Template tes (bisa dihapus)
    ├── user_add_account.html
    └── ... (template spesifik jenis chiller Anda, misal: btpn_type.html, bxc2_type.html)
```

### 7. Menjalankan Aplikasi

```bash
python app.py
```

Aplikasi biasanya akan berjalan di `http://127.0.0.1:5000/`.

## Catatan Penting untuk Pengembang

*   **Pengambilan Data Dinamis:** Rute `test` di `app.py` sekarang secara dinamis mengambil semua parameter dan konfigurasinya dari tabel `parameters` dan `chiller_parameters` berdasarkan `chiller_id`.
*   **Nilai Placeholder:** Saat ini, `param['current_value']` di `app.py` di-hardcode menjadi `7.11`. Dalam skenario dunia nyata, ini akan diganti dengan data aktual yang diambil dari sensor, Modbus, atau API.
*   **Kustomisasi Gauge:** `chiller_dashboard.html` menggunakan loop Jinja2 untuk merender gauge dan tabel. Anda dapat menyesuaikan atribut `data-*` dari elemen `<canvas>` berdasarkan data tabel `parameters` untuk mengontrol tampilan gauge (misalnya, `data-color-plate`, `data-color-needle-start`, dll.).
*   **Penanganan Error:** Penanganan error dasar untuk koneksi database sudah ada. Pertimbangkan untuk menambahkan logging error yang lebih kuat dan umpan balik pengguna.
*   **Keamanan:** Selalu gunakan kunci rahasia yang kuat dan unik dan jangan pernah mengekspos kredensial database secara langsung dalam kode di lingkungan produksi. Gunakan variabel lingkungan.

---