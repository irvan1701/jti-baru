import paho.mqtt.client as mqtt
import mysql.connector
import json
from datetime import datetime
import re

# --- Konfigurasi Database (HARAP PERBARUI INI!) ---
db_config = {
    'host': '127.0.0.1',
    'user': 'jti_acr_bas',
    'password': 'JTI_j0h@r10',
    'database': 'jti-new2',
    'port': '3306'
}

# --- Konfigurasi Broker MQTT ---
mqtt_broker_host = "broker.mqtt-dashboard.com"
mqtt_broker_port = 1883
mqtt_topic = "ecu1051/mqtt_data/menara_btpn"

# --- Pemetaan Kolom Database ---
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
    "Operating_Hours": "operating_hour",
    "Operating_Hour": "operating_hour",
    "Oil_Pump_Pressure": "oil_pump_pressure",
    "Safety_fault": "safety_fault",
    "Cycling_Fault": "cycling_fault",
    "Warning_Fault": "warning_fault",
    "Input_Power": "input_power",
    "Operating_Code": "operating_code",
    "VSD_Input_Power": "vsd_input_power",
    "VSD_Input_KWH": "vsd_input_kwh",
    "Evap_Refrigerant_Temp": "evap_refri_temp",
    "VSD_Ph_A_Current": "vsd_ph_a_current",
    "VSD_Ph_B_Current": "vsd_ph_b_current",
    "VSD_Ph_C_Current": "vsd_ph_c_current",
    "Safety_Fault": "safety_fault",
    "Approach_Evap": "approach_evap",
    "Approach_Cond": "approach_cond",
    "EER": "eer",
    "COP": "cop",
    "Efficiency": "efficiency",
    "Cooling_Capacity": "cooling_capacity",
    "Cond_DT": "cond_dt",
    "Evap_DT": "evap_dt",
}

# --- Fungsi Bantuan ---
def get_db_connection():
    """Mencoba membuat koneksi database."""
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"Error koneksi database: {err}")
        return None

def c_to_f(celsius):
    """Mengonversi suhu dari Celsius ke Fahrenheit."""
    return (celsius * 9/5) + 32

def insert_or_update_chiller_data(payload, topic):
    """
    Memproses payload chiller dan memasukkannya ke database.
    """
    cnx = get_db_connection()
    if not cnx:
        return

    cursor = cnx.cursor()

    try:
        match = re.search(r'ecu1051/mqtt_data/([^/]+)', topic)
        if not match:
            print(f"Error: Tidak dapat mengekstrak site_id dari topik: {topic}")
            return
        site_id = match.group(1)

        timestamp_str = payload.get("ts")
        if not timestamp_str:
            print("Error: Field 'ts' (timestamp) tidak ditemukan dalam payload.")
            return

        if timestamp_str.endswith('Z'):
            timestamp = datetime.fromisoformat(timestamp_str[:-1])
        elif '+' in timestamp_str and len(timestamp_str.split('+')[-1]) == 5:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")

        data_entries = payload.get("d", [])
        if not data_entries:
            print("Peringatan: Field 'd' (data) tidak ditemukan atau kosong dalam payload.")
            return

        chiller_data = {}

        for entry in data_entries:
            tag = entry.get("tag")
            value = entry.get("value")

            if not tag or value is None:
                continue

            chiller_tag_parts = tag.split(':')
            if len(chiller_tag_parts) < 2:
                continue

            chiller_num_raw = chiller_tag_parts[0]
            data_field_name = chiller_tag_parts[1]

            if chiller_num_raw not in chiller_data:
                chiller_data[chiller_num_raw] = {}

            chiller_data[chiller_num_raw][data_field_name] = value
        
        for chiller_num_raw, data_values in chiller_data.items():
            chiller_id_num = chiller_num_raw.lower().replace('ch', '')
            full_chiller_id = f"{site_id}_{chiller_id_num}"

            columns_to_insert = ["timestamp", "chiller_id"]
            values_to_insert = [timestamp, full_chiller_id]
            updates = []
            
            print(f"\n--- DEBUGGING UNTUK CHILLER {full_chiller_id} PADA {timestamp} ---")
            
            efficiency = None
            cop = None
            eer = None
            cooling_capacity = None

            for tag_name, value in data_values.items():
                db_column_name = column_mapping.get(tag_name)
                
                if db_column_name:
                    columns_to_insert.append(db_column_name)
                    values_to_insert.append(value)
                    updates.append(f"{db_column_name} = VALUES({db_column_name})")
                print(f"Data dari payload (sebelum konversi): {tag_name} = {value}")

            try:
                evap_lwt_c = data_values.get("Evap_LWT")
                evap_satur_temp_c = data_values.get("Evap_Satur_Temp")
                evap_rwt_c = data_values.get("Evap_RWT")
                cond_lwt_c = data_values.get("Cond_LWT")
                cond_rwt_c = data_values.get("Cond_RWT")
                cond_satur_temp_c = data_values.get("Cond_Satur_Temp")
                fla = data_values.get("FLA")
                input_power = data_values.get("Input_Power")

                # Convert temperatures to Fahrenheit for calculation
                evap_lwt = c_to_f(evap_lwt_c) if evap_lwt_c is not None else None
                evap_satur_temp = c_to_f(evap_satur_temp_c) if evap_satur_temp_c is not None else None
                evap_rwt = c_to_f(evap_rwt_c) if evap_rwt_c is not None else None
                cond_lwt = c_to_f(cond_lwt_c) if cond_lwt_c is not None else None
                cond_rwt = c_to_f(cond_rwt_c) if cond_rwt_c is not None else None
                cond_satur_temp = c_to_f(cond_satur_temp_c) if cond_satur_temp_c is not None else None
                
                if evap_lwt is not None and evap_satur_temp is not None:
                    approach_evap = evap_lwt - evap_satur_temp
                    columns_to_insert.append("approach_evap")
                    values_to_insert.append(approach_evap)
                    updates.append("approach_evap = VALUES(approach_evap)")
                    print(f"approach_evap (Evap LWT F - Evap Satur Temp F): {approach_evap}")
                
                if cond_satur_temp is not None and cond_lwt is not None:
                    approach_cond = cond_satur_temp - cond_lwt
                    columns_to_insert.append("approach_cond")
                    values_to_insert.append(approach_cond)
                    updates.append("approach_cond = VALUES(approach_cond)")
                    print(f"approach_cond (Cond Satur F - Cond LWT F): {approach_cond}")

                evap_dt = None
                if evap_rwt is not None and evap_lwt is not None:
                    evap_dt = evap_rwt - evap_lwt
                    columns_to_insert.append("evap_dt")
                    values_to_insert.append(evap_dt)
                    updates.append("evap_dt = VALUES(evap_dt)")
                    print(f"evap_dt (Evap RWT F - Evap LWT F): {evap_dt}")
                
                if cond_lwt is not None and cond_rwt is not None:
                    cond_dt = cond_lwt - cond_rwt
                    columns_to_insert.append("cond_dt")
                    values_to_insert.append(cond_dt)
                    updates.append("cond_dt = VALUES(cond_dt)")
                    print(f"cond_dt (Cond LWT F - Cond RWT F): {cond_dt}")

                if evap_dt is not None:
                    cooling_capacity = evap_dt * 1296 / 24
                    columns_to_insert.append("cooling_capacity")
                    values_to_insert.append(cooling_capacity)
                    updates.append("cooling_capacity = VALUES(cooling_capacity)")
                    print(f"cooling_capacity (Evap DT F * 1296 / 24): {cooling_capacity}")

                    if input_power is not None and cooling_capacity is not None and cooling_capacity > 0:
                        efficiency = input_power / cooling_capacity
                        if efficiency > 0:
                            cop = 12 / efficiency / 3.142
                            eer = 12 / efficiency
                        else:
                            cop = 0.0
                            eer = 0.0
                            print("Peringatan: Nilai Efficiency nol, COP dan EER diatur ke 0.0.")
                    else:
                        print("Peringatan: Cooling_Capacity atau Input_Power tidak valid atau Cooling_Capacity nol. Efficiency, COP, dan EER diatur ke 0.0.")
                        efficiency = 0.0
                        cop = 0.0
                        eer = 0.0
                else:
                    print("Peringatan: Evap_DT tidak valid. Efficiency, COP, dan EER diatur ke 0.0.")
                    efficiency = 0.0
                    cop = 0.0
                    eer = 0.0
            
            except (TypeError, ValueError) as calc_err:
                print(f"Peringatan: Gagal melakukan perhitungan untuk chiller {full_chiller_id}: {calc_err}")
                efficiency = 0.0
                cop = 0.0
                eer = 0.0

            if efficiency is not None:
                columns_to_insert.append("efficiency")
                values_to_insert.append(efficiency)
                updates.append("efficiency = VALUES(efficiency)")
                print(f"efficiency: {efficiency}")

                columns_to_insert.append("cop")
                values_to_insert.append(cop)
                updates.append("cop = VALUES(cop)")
                print(f"cop: {cop}")

                columns_to_insert.append("eer")
                values_to_insert.append(eer)
                updates.append("eer = VALUES(eer)")
                print(f"eer: {eer}")

            if not updates:
                print(f"Peringatan: Tidak ada data yang valid untuk chiller {full_chiller_id} yang dapat diinsert/update.")
                continue

            columns_str = ", ".join(columns_to_insert)
            placeholders = ", ". join(["%s"] * len(values_to_insert))
            updates_str = ", ".join(updates)
            sql = f"INSERT INTO chiller_datas ({columns_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates_str}"
            
            print(f"SQL yang akan dieksekusi:\n{sql}")
            print(f"Nilai yang akan diinput:\n{values_to_insert}")

            try:
                cursor.execute(sql, values_to_insert)
                print(f"Data untuk {full_chiller_id} pada {timestamp} berhasil diinsert/update.")
            except mysql.connector.Error as err:
                print(f"Error saat insert/update data untuk {full_chiller_id}: {err}")

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
