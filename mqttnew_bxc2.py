import paho.mqtt.client as mqtt
import mysql.connector
import json
from datetime import datetime
import re
import time

# --- Konfigurasi MQTT ---
MQTT_BROKER = "broker.mqtt-dashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "ecu1051/mqtt_data/bxc2_sqc" 

# --- Konfigurasi MySQL ---
MYSQL_HOST = "127.0.0.1"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "jti-new2"
MYSQL_PORT = 3306

# Variabel global untuk koneksi database (akan diinisialisasi sekali)
global_mysql_conn = None

# --- Pemetaan Nama Kolom Database ---
# Ini sangat penting! Pastikan nama di payload (kunci) sesuai dengan nama di DB (nilai).
COLUMN_MAPPING = {
    "Evap_LWT": "evap_lwt",
    "Evap_RWT": "evap_rwt",
    "Cond_RWT": "cond_rwt",
    "Cond_LWT": "cond_lwt",
    "FLA": "fla",
    "Input_Power": "input_power",
    "Input_KWH": "input_kwh",
    "Operating_Hour": "operating_hour", # Menggunakan "Operating_Hour" sesuai payload Anda
    "Safety_Fault": "safety_fault",     # Sesuai dengan payload Anda
    "Cycling_Fault": "cycling_fault",
    "Warning_Fault": "warning_fault",
    "Evap_Pressure": "evap_pressure",
    "Cond_Pressure": "cond_pressure",
    "Oil_Pressure_Diff": "oil_pressure_diff",
    "VSD_Ph_A_Current": "vsd_ph_a_current",
    "VSD_Ph_B_Current": "vsd_ph_b_current",
    "VSD_Ph_C_Current": "vsd_ph_c_current",
    "Leav_Ch_Liq_SP": "leav_ch_liq_sp",
    "Act_Current_Limit": "act_current_limit",
    "Evap_Satur_Temp": "evap_satur_temp",
    "Cond_Satur_Temp": "cond_satur_temp",
    "Discharge_Temp": "discharge_temp",
    "Oil_Sump_Temp": "oil_sump_temp",
    "Cond_Refri_Lvl": "cond_refri_lvl", # Menggunakan "Cond_Refri_Lvl" sesuai payload Anda
    "Number_Of_Start": "number_of_start",
    "Oil_Sump_Pressure": "oil_sump_pressure",
    "Oil_Pump_Pressure": "oil_pump_pressure",
    "Operating_Code": "operating_code",
    "VSD_Out_Voltage": "vsd_out_voltage",
    "VSD_Out_Freq": "vsd_out_freq",
    "Cond_Refri_Lvl_SP": "cond_refri_lvl_sp", # Menggunakan "Cond_Refri_Lvl_SP" sesuai payload Anda
    "Drop_Leg_Refri_Temp": "drop_leg_refri_temp",
    "Evap_Refri_Lvl": "evap_refri_lvl", # Menggunakan "Evap_Refri_Lvl" sesuai payload Anda
    "Mtr_Wind_PH_A_Temp": "mtr_wind_ph_a_temp", # FIX: Match 'PH' uppercase from payload tag
    "Mtr_Wind_PH_B_Temp": "mtr_wind_ph_b_temp", # FIX: Match 'PH' uppercase from payload tag
    "Mtr_Wind_PH_C_Temp": "mtr_wind_ph_c_temp", # FIX: Match 'PH' uppercase from payload tag
    "Evap_STD": "evap_std",
    "Cond_STD": "cond_std",
    "Discharge_Superheat": "discharge_superheat",
    "Status": "status",
    "Warning": "warning",
    "Alarm": "alarm",
    "Liq_Line_Selenoid": "liq_line_solenoid", # FIX: Match typo "Selenoid" from payload tag
    "Ch_Liq_Pump_Sts": "ch_liq_pump_sts",
    "Panel_Stop_Switch_Sts": "panel_stop_switch_sts",
    "Ch_Liq_Flow_Switch": "ch_liq_flow_switch",
    "Cond_Liq_Flow_Switch": "cond_liq_flow_switch",
    "Cond_Liq_Pump_Sts": "cond_liq_pump_sts",
    
    # Tag-tag Fahrenheit:
    "Evap_RWT_Fahrenheit": "evap_rwt_fahrenheit",
    "Evap_LWT_Fahrenheit": "evap_lwt_fahrenheit",

    # Kolom umum (jika ada tag tanpa prefix CHx: di payload, misal "Sys1_Disch_Temp")
    # Jika payload Anda tidak punya tag global tanpa CHx, ini tidak akan dipakai
    "Sys1_Disch_Temp": "sys1_disch_temp",
    "Sys1_Oil_Press": "sys1_oil_press",
    "Sys1_Evap_Press": "sys1_evap_press",
    "Sys1_Disch_Press": "sys1_disch_press",
    "Sys1_Comp_FLA": "sys1_comp_fla",
    "Sys1_Run_Hour": "sys1_run_hour",
    "Sys2_Oil_Press": "sys2_oil_press",
    "Sys2_Suct_Press": "sys2_suct_press",
    "Sys2_Disch_Press": "sys2_disch_press",
    "Sys2_Comp_FLA": "sys2_comp_fla",
    "Sys2_Run_Hour": "sys2_run_hour",
    "Chiller_Run": "chiller_run",
    "Chiller_Alarm": "chiller_alarm",
    "Fault_Code": "fault_code",
    "Sys1_Suct_Temp": "sys1_suct_temp",
    "Amb_Air_Temp": "amb_air_temp",
    "Sys1_Suct_Superheat": "sys1_suct_superheat",
    "Sys1_EEV_Out_Pct": "sys1_eev_out_pct",
    "Sys1_Com1_Hour": "sys1_com1_hour",
    "Sys1_Com2_Hour": "sys1_com2_hour",
    "Sys1_Com3_Hour": "sys1_com3_hour",
    "Sys2_Com1_Hour": "sys2_com1_hour",
    "Sys2_Com2_Hour": "sys2_com2_hour",
    "Sys2_Com3_Hour": "sys2_com3_hour",
    "Sys1_Com1_Run": "sys1_com1_run",
    "Sys1_Com2_Run": "sys1_com2_run",
    "Sys1_Com3_Run": "sys1_com3_run",
    "Sys2_Com1_Run": "sys2_com1_run",
    "Sys2_Com2_Run": "sys2_com2_run",
    "Sys2_Com3_Run": "sys2_com3_run",
    "Sys2_Suct_Temp": "sys2_suct_temp",
    "Sys2_Suct_Superheat": "sys2_suct_superheat",
    "Sys2_EEV_Out_Pct": "sys2_eev_out_pct",
    "Sys1_Disch_Superheat": "sys1_disch_superheat",
    "Sys2_Disch_Temp": "sys2_disch_temp",
    "Sys2_Disch_Superheat": "sys2_disch_superheat",
    "Sys1_Fault_Code": "sys1_fault_code",
    "Sys2_Fault_Code": "sys2_fault_code",
    "Sys1_Cond_Temp": "sys1_cond_temp",
    "Out_Amb_Temp": "out_amb_temp",
    "Sys1_Eductor_Temp": "sys1_eductor_temp",
    "Sys2_Eductor_Temp": "sys2_eductor_temp",
    "Sys1_Alarm": "sys1_alarm",
    "Sys2_Alarm": "sys2_alarm",
    "Sys2_Cond_Temp": "sys2_cond_temp",
    "Sys1_Motor_Temp_1": "sys1_motor_temp_1",
    "Sys1_Motor_Temp_2": "sys1_motor_temp_2",
    "Sys1_Motor_Temp_3": "sys1_motor_temp_3",
    "Sys2_Motor_Temp_1": "sys2_motor_temp_1",
    "Sys2_Motor_Temp_2": "sys2_motor_temp_2",
    "Sys2_Motor_Temp_3": "sys2_motor_temp_3",
    "Sys1_Warning_Code": "sys1_warning_code",
    "Sys2_Warning_Code": "sys2_warning_code",
    "Sys1_Fan_Power": "sys1_fan_power",
    "Sys1_Comp_Power": "sys1_comp_power",
    "Sys2_Fan_Power": "sys2_fan_power",
    "Sys2_Comp_Power": "sys2_comp_power",
    "Motor_Ph_A_Voltage": "motor_ph_a_voltage",
    "Motor_Ph_B_Voltage": "motor_ph_b_voltage",
    "Motor_Ph_C_Voltage": "motor_ph_c_voltage",
    "Seal_Press_Diff": "seal_press_diff",
    "Filter_Diff_Press": "filter_diff_press",
    "Output_Voltage": "output_voltage",
}


def initialize_mysql_connection():
    """Menginisialisasi koneksi MySQL global."""
    global global_mysql_conn
    max_retries = 5
    retry_delay = 5  # detik
    for i in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                port=MYSQL_PORT
            )
            print("Successfully connected to MySQL database (global connection)!")
            global_mysql_conn = conn
            return True
        except mysql.connector.Error as err:
            print(f"Attempt {i+1}/{max_retries}: Error connecting to MySQL (global): {err}")
            if i < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not establish global MySQL connection.")
                return False
    return False

def close_global_mysql_connection():
    """Menutup koneksi MySQL global."""
    global global_mysql_conn
    if global_mysql_conn and global_mysql_conn.is_connected():
        global_mysql_conn.close()
        print("Global MySQL connection closed.")

def insert_data_to_mysql(data, topic):
    """Memasukkan data dari pesan MQTT ke database MySQL."""
    global global_mysql_conn

    # Pastikan koneksi global aktif
    if global_mysql_conn is None or not global_mysql_conn.is_connected():
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Re-establishing global MySQL connection...")
        if not initialize_mysql_connection():
            print("Failed to re-establish MySQL connection. Skipping data insertion.")
            return

    cursor = global_mysql_conn.cursor()

    try:
        # --- Ekstraksi site_id dari topik MQTT ---
        # Contoh: "ecu1051/mqtt_data/bxc2_sqc" -> site_id = "bxc2_sqc"
        match_topic_site = re.search(r'ecu1051/mqtt_data/([^/]+)', topic)
        if not match_topic_site:
            print(f"Error: Tidak dapat mengekstrak site_id dari topik MQTT: {topic}. Melewatkan data.")
            return
        site_id = match_topic_site.group(1) # Contoh: "bxc2_sqc"

        ts_str = data["ts"]
        try:
            # Mengatasi berbagai format ISO 8601, termasuk yang memiliki Z atau offset
            timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            timestamp = timestamp.replace(tzinfo=None) # Hapus timezone info untuk MySQL DATETIME
        except ValueError:
            print(f"Warning: Failed to parse timestamp '{ts_str}' using fromisoformat. Trying fallback.")
            # Fallback untuk format "YYYY-MM-DDTHH:MM:SS+HHMM"
            # Split by '+' and take the first part
            timestamp = datetime.strptime(ts_str.split('+')[0], "%Y-%m-%dT%H:%M:%S")

        chiller_data_buffer = {}

        for item in data["d"]:
            tag = item["tag"]
            value = item["value"]

            # --- Parsing Tag untuk chiller_id dan metric_name ---
            # Pola untuk menangani format seperti "FBXI:CH1_Evap_LWT", "CH1:Evap_LWT" atau "CH1_Evap_LWT_Fahrenheit"
            # group(1) akan menjadi "CH1" atau "CH2"
            # group(2) akan menjadi "Evap_LWT" atau "Evap_LWT_Fahrenheit"
            match_tag = re.match(r'^(?:FBXI:)?(CH\d+)[:_]?(.*)$', tag)
            
            if not match_tag:
                print(f"Skipping unknown tag format (no CHx prefix found): {tag}")
                continue

            chiller_num_raw = match_tag.group(1) # Contoh: "CH1"
            metric_raw_name = match_tag.group(2) # Contoh: "Evap_LWT" atau "Evap_LWT_Fahrenheit"

            # Ekstrak angka chiller (misal dari "CH1" menjadi "1")
            chiller_number_match = re.search(r'\d+', chiller_num_raw)
            if not chiller_number_match:
                print(f"Warning: Could not extract chiller number from '{chiller_num_raw}'. Skipping tag: {tag}")
                continue
            chiller_number = chiller_number_match.group(0)

            # --- Bentuk chiller_id final: site_id_chiller_number ---
            # Contoh: "bxc2_sqc_1", "bxc2_sqc_3"
            # Jika di DB Anda site_id adalah "bxc2" (bukan "bxc2_sqc"),
            # Anda mungkin perlu menormalisasi site_id di sini:
            # site_id_for_db = site_id.replace("_sqc", "") # Misal jika site_id di DB adalah "bxc2"
            # final_chiller_id = f"{site_id_for_db.lower()}_{chiller_number}"
            # Untuk saat ini, saya akan menggunakan site_id langsung dari topik:
            final_chiller_id = f"{site_id.lower()}_{chiller_number}"

            metric_name_db = COLUMN_MAPPING.get(metric_raw_name)

            if not metric_name_db:
                print(f"Warning: No database column mapping found for tag field '{metric_raw_name}'. Skipping data for {final_chiller_id}.")
                continue

            # Simpan data ke buffer sementara per chiller_id
            if final_chiller_id not in chiller_data_buffer:
                chiller_data_buffer[final_chiller_id] = {}
            chiller_data_buffer[final_chiller_id][metric_name_db] = value
        
        # --- Proses Buffer dan Masukkan ke Database ---
        for current_full_chiller_id, params in chiller_data_buffer.items():
            if not params:
                continue

            insert_columns = ['timestamp', 'chiller_id']
            insert_values = [timestamp, current_full_chiller_id]
            update_set_clauses = []

            for param_name, param_value in params.items():
                insert_columns.append(f"`{param_name}`") # Gunakan backticks untuk nama kolom yang mungkin sensitif
                insert_values.append(param_value)
                update_set_clauses.append(f"`{param_name}` = VALUES(`{param_name}`)")

            column_names_str = ', '.join(insert_columns)
            placeholders = ', '.join(['%s'] * len(insert_values))
            update_clause_str = ', '.join(update_set_clauses)

            insert_query = f"""
            INSERT INTO `chiller_datas` ({column_names_str})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_clause_str};
            """
            try:
                cursor.execute(insert_query, tuple(insert_values))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Data for Chiller ID {current_full_chiller_id} at {timestamp} processed.")
            except mysql.connector.Error as err:
                # Menangkap error Foreign Key
                if err.errno == 1452: # MySQL error code for foreign key constraint fails
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error processing data for {current_full_chiller_id} at {timestamp}: Chiller ID '{current_full_chiller_id}' **NOT FOUND** in `chillers` table. Please add this chiller first.")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error processing data for {current_full_chiller_id} at {timestamp}: {err}")
                global_mysql_conn.rollback() # Rollback transaksi jika ada error pada chiller ini
                
        global_mysql_conn.commit() # Commit koneksi global setelah semua chiller dalam payload diproses
        print(f"[{datetime.now().strftime('%H:%M:%S')}] All chiller data for {timestamp} processed and committed successfully for site {site_id}.")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
        if global_mysql_conn:
            global_mysql_conn.rollback() # Rollback koneksi global
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if global_mysql_conn:
            global_mysql_conn.rollback() # Rollback koneksi global
  

# --- Callback MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to connect to MQTT, return code {rc}\n")

def on_message(client, userdata, msg):
    print(f"\n--- Message received on topic: {msg.topic} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')} ---")
    try:
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)
        insert_data_to_mysql(data, msg.topic)
    except json.JSONDecodeError:
        print(f"Error: Pesan yang diterima bukan JSON yang valid: {msg.payload.decode()}")
    except Exception as e:
        print(f"An unexpected error occurred while processing MQTT message: {e}")

# --- Main Program ---
if __name__ == "__main__":
    # Inisialisasi koneksi MySQL global sekali di awal
    if not initialize_mysql_connection():
        print("Exiting due to failed database connection initialization.")
        exit()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever() # Loop selamanya untuk memproses pesan