import paho.mqtt.client as mqtt
import mysql.connector
import json
from datetime import datetime
import re # Untuk mengekstrak site_id dari topik

# --- Konfigurasi Database (HARAP PERBARUI INI!) ---
db_config = {
    'host': '127.0.0.1',
    'user': 'root',        # <--- GANTI DENGAN USERNAME MySQL Anda
    'password': '', # <--- GANTI DENGAN PASSWORD MySQL Anda
    'database': 'jti-new2',
    'port' : '3306'
}




# --- Konfigurasi Broker MQTT ---
mqtt_broker_host = "broker.mqtt-dashboard.com"
mqtt_broker_port = 1883
mqtt_topic = "ecu1051/mqtt_data/menara_btpn" # Topik MQTT yang akan dilanggan

# --- Pemetaan Kolom Database ---
# Kamus ini memetakan nama tag dari payload Anda ke nama kolom database Anda.
# Pastikan ini sesuai dengan skema tabel 'chiller_datas' Anda.
# --- Pemetaan Kolom Database ---
# Kamus ini memetakan nama tag dari payload Anda ke nama kolom database Anda.
# Pastikan ini sesuai dengan skema tabel 'chiller_datas' Anda.
column_mapping = {
    "Evap_LWT": "evap_lwt",
    "Evap_RWT": "evap_rwt",
    "Evap_Pressure": "evap_pressure",
    "Cond_Pressure": "cond_pressure",
    "Oil_Pressure_Diff": "oil_pressure_diff",
    "Cond_RWT": "cond_rwt",
    "Cond_LWT": "cond_lwt",
    "FLA": "fla",
    "Motor_Ph_A_Current": "motor_ph_a_current",
    "Motor_Ph_B_Current": "motor_ph_b_current",
    "Motor_Ph_C_Current": "motor_ph_c_current",
    "VSD_Output_Voltage": "vsd_out_voltage",
    "Input_KWH": "input_kwh",
    "Evap_Satur_Temp": "evap_satur_temp",
    "Cond_Satur_Temp": "cond_satur_temp",
    "Discharge_Temp": "discharge_temp",
    "Oil_Sump_Temp": "oil_sump_temp",
    "Cond_Refrigerant_Level": "cond_refri_lvl",
    "Operating_Hours": "operating_hour", # <--- DITAMBAHKAN/DIPASTIKAN
    "Oil_Pump_Pressure": "oil_pump_pressure",
    "Safety_fault": "safety_fault",
    "Cycling_Fault": "cycling_fault",
    "Warning_Fault": "warning_fault",
    "Input_Power": "input_power",
    "Operating_Code": "operating_code",
    "VSD_Input_Power": "vsd_input_power",
    "VSD_Input_KWH": "vsd_input_kwh",
    "Evap_Refrigerant_Temp": "evap_refri_temp",
    # Tambahan dari payload yang Anda berikan:
    "VSD_Ph_A_Current": "vsd_ph_a_current", # <--- DITAMBAHKAN
    "VSD_Ph_B_Current": "vsd_ph_b_current", # <--- DITAMBAHKAN
    "VSD_Ph_C_Current": "vsd_ph_c_current", # <--- DITAMBAHKAN
    "Safety_Fault": "safety_fault", # <--- PASTIKAN 'Safety_fault' (ada underscore) di payload sama dengan yang di DB (Safety_fault)
                                    # Jika payload pakai 'Safety_Fault', maka harus dicantumkan di sini.
                                    # Payload Anda punya 'Safety_fault' (tanpa underscore di akhir) dan 'Safety_Fault' (dengan underscore di akhir)
                                    # Hati-hati dengan kapitalisasi dan underscore. Cek kembali payload asli Anda.
}
# --- Fungsi Bantuan ---
def get_db_connection():
    """Mencoba membuat koneksi database."""
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"Error koneksi database: {err}")
        return None

def insert_or_update_chiller_data(payload, topic):
    """
    Memproses payload chiller dan memasukkannya ke database.
    """
    cnx = get_db_connection()
    if not cnx:
        return

    cursor = cnx.cursor()

    try:
        # Ekstrak site_id dari topik MQTT
        # Misalnya, dari "ecu1051/mqtt_data/menara_btpn" akan menghasilkan "menara_btpn"
        match = re.search(r'ecu1051/mqtt_data/([^/]+)', topic)
        if not match:
            print(f"Error: Tidak dapat mengekstrak site_id dari topik: {topic}")
            return
        site_id = match.group(1)

        # Ekstrak timestamp dari payload
        timestamp_str = payload.get("ts")
        if not timestamp_str:
            print("Error: Field 'ts' (timestamp) tidak ditemukan dalam payload.")
            return

        # Parsing timestamp (menangani ISO 8601 dengan/tanpa Z atau offset zona waktu)
        if timestamp_str.endswith('Z'):
            timestamp = datetime.fromisoformat(timestamp_str[:-1])
        elif '+' in timestamp_str and len(timestamp_str.split('+')[-1]) == 5: # Handles +HH:MM
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            # Fallback untuk format sederhana jika tidak ada info zona waktu
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

        data_entries = payload.get("d", [])
        if not data_entries:
            print("Peringatan: Field 'd' (data) tidak ditemukan atau kosong dalam payload.")
            return

        # Untuk setiap entri data dalam payload
        for entry in data_entries:
            tag = entry.get("tag")
            value = entry.get("value")

            if not tag or value is None:
                print(f"Melewatkan entri dengan field 'tag' atau 'value' yang hilang: {entry}")
                continue

            # Ekstrak nomor chiller dari tag (misalnya, "CH1:Evap_LWT" -> "CH1")
            chiller_tag_parts = tag.split(':')
            if len(chiller_tag_parts) < 2:
                print(f"Melewatkan tag yang salah format (tidak ada chiller_num atau data_field): {tag}")
                continue

            chiller_num_raw = chiller_tag_parts[0] # Contoh: "CH1"
            # Buat chiller_id (contoh: "menara_btpn_1")
            # Pastikan chiller_num_raw diproses dengan benar menjadi hanya angka jika "CH" adalah awalan
            chiller_id_num = chiller_num_raw.lower().replace('ch', '')
            full_chiller_id = f"{site_id}_{chiller_id_num}"

            # Ekstrak nama field data yang sebenarnya (contoh: "Evap_LWT")
            data_field_name = chiller_tag_parts[1]

            db_column_name = column_mapping.get(data_field_name)

            if not db_column_name:
                print(f"Peringatan: Tidak ada pemetaan kolom database ditemukan untuk field tag '{data_field_name}'. Melewatkan.")
                continue

            # Gunakan INSERT ... ON DUPLICATE KEY UPDATE
            # Ini akan mencoba memasukkan baris. Jika kombinasi (timestamp, chiller_id) sudah ada
            # (karena UNIQUE KEY Anda), ia akan memperbarui kolom yang ditentukan.
            sql = f"""
            INSERT INTO chiller_datas (timestamp, chiller_id, {db_column_name})
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                {db_column_name} = VALUES({db_column_name})
            """
            try:
                cursor.execute(sql, (timestamp, full_chiller_id, value))
                print(f"Data {full_chiller_id} - {db_column_name} = {value} pada {timestamp} berhasil diinsert/update.")
            except mysql.connector.Error as err:
                print(f"Error saat insert/update data untuk {full_chiller_id}, {timestamp}, {db_column_name}: {err}")

        cnx.commit()
        print("Proses insert/update data selesai untuk payload ini.")

    except json.JSONDecodeError:
        print("Error: Payload MQTT bukan JSON yang valid.")
    except Exception as e:
        print(f"Terjadi error tak terduga saat memproses pesan: {e}")
    finally:
        if cnx and cnx.is_connected():
            cursor.close()
            cnx.close()
            print("Koneksi database ditutup.")

# --- Callback MQTT ---

def on_connect(client, userdata, flags, rc):
    """Fungsi callback saat klien terhubung ke broker MQTT."""
    if rc == 0:
        print(f"Terhubung ke Broker MQTT: {mqtt_broker_host}")
        client.subscribe(mqtt_topic)
        print(f"Berlangganan ke topik: {mqtt_topic}")
    else:
        print(f"Gagal terhubung, kode kembali {rc}\n")

def on_message(client, userdata, msg):
    """Fungsi callback saat pesan diterima dari broker MQTT."""
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        insert_or_update_chiller_data(payload, msg.topic)
    except json.JSONDecodeError:
        print(f"Pesan yang diterima bukan JSON yang valid: {msg.payload.decode('utf-8')}")
    except Exception as e:
        print(f"Error saat memproses pesan: {e}")

# --- Main Program ---
if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_broker_host, mqtt_broker_port, 60)
    client.loop_forever()
        
