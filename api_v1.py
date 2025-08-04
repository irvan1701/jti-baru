from flask import Blueprint, jsonify
import mysql.connector
import os

# Definisikan Blueprint API
api_bp = Blueprint('api', __name__)

# Konfigurasi database
DB_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
DB_USER = os.environ.get('MYSQL_USER', 'root')
DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
DB_NAME = os.environ.get('MYSQL_DB', 'jti-new2')

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

parameter_data_map = {
    'LWT': 'evap_lwt', 'RWT': 'evap_rwt', 'Evap Pressure': 'evap_pressure',
    'Cond LWT': 'cond_lwt', 'Cond RWT': 'cond_rwt', 'Cond Pressure': 'cond_pressure',
    'Discharge Temp': 'discharge_temp', 'Oil Sump Temp': 'oil_sump_temp',
    'Oil Discharge PSI': 'oil_sump_pressure', 'VSD Out Voltage': 'vsd_out_voltage',
    'FLA': 'fla', 'Input Power': 'input_power', 'Input KWH': 'input_kwh',
    'Operating Hour': 'operating_hour', 'Number of Start': 'number_of_start',
    'Act Current Limit': 'act_current_limit', 'VSD Out Freq': 'vsd_out_freq',
    'Mtr Wind PH A Temp': 'mtr_wind_ph_a_temp', 'Mtr Wind PH B Temp': 'mtr_wind_ph_b_temp',
    'Mtr Wind PH C Temp': 'mtr_wind_ph_c_temp', 'Status': 'status',
    'Warning': 'warning', 'Alarm': 'alarm', 'Safety Fault': 'safety_fault',
    'Cycling Fault': 'cycling_fault', 'Warning Fault': 'warning_fault',
    'Operating Code': 'operating_code', 'Liq Line Solenoid': 'liq_line_solenoid',
    'CH Liq Pump STS': 'ch_liq_pump_sts', 'Panel Stop Switch STS': 'panel_stop_switch_sts',
    'CH Liq Flow Switch': 'ch_liq_flow_switch', 'Cond Liq Flow Switch': 'cond_liq_flow_switch',
    'Cond Liq Pump STS': 'cond_liq_pump_sts', 'CH1 Evap RWT Fahrenheit': 'ch1_evap_rwt_fahrenheit',
    'CH1 Evap LWT Fahrenheit': 'ch1_evap_lwt_fahrenheit', 'CH2 Evap RWT Fahrenheit': 'ch2_evap_rwt_fahrenheit',
    'CH2 Evap LWT Fahrenheit': 'ch2_evap_lwt_fahrenheit', 'CH3 Evap RWT Fahrenheit': 'ch3_evap_rwt_fahrenheit',
    'CH3 Evap LWT Fahrenheit': 'ch3_evap_lwt_fahrenheit', 'CH4 Evap RWT Fahrenheit': 'ch4_evap_rwt_fahrenheit',
    'CH4 Evap LWT Fahrenheit': 'ch4_evap_lwt_fahrenheit', 'Leav CH Liq SP': 'leav_ch_liq_sp',
    'Evap RWT Fahrenheit': 'evap_rwt_fahrenheit', 'Evap LWT Fahrenheit': 'evap_lwt_fahrenheit',
    'VSD Input Power': 'vsd_input_power', 'VSD Input KWH': 'vsd_input_kwh',
    'Evap Refri Temp': 'evap_refri_temp', 'Vsd In Amb Temp': 'vsd_in_amb_temp',
    'Sys1 Disch Temp': 'sys1_disch_temp', 'Sys1 Oil Press': 'sys1_oil_press',
    'Sys1 Evap Press': 'sys1_evap_press', 'Sys1 Disch Press': 'sys1_disch_press',
    'Sys1 Comp FLA': 'sys1_comp_fla', 'Sys1 Run Hour': 'sys1_run_hour',
    'Sys2 Oil Press': 'sys2_oil_press', 'Sys2 Suct Press': 'sys2_suct_press',
    'Sys2 Disch Press': 'sys2_disch_press', 'Sys2 Comp FLA': 'sys2_comp_fla',
    'Sys2 Run Hour': 'sys2_run_hour', 'Chiller Run': 'chiller_run',
    'Chiller Alarm': 'chiller_alarm', 'Fault Code': 'fault_code',
    'Sys1 Suct Temp': 'sys1_suct_temp', 'Amb Air Temp': 'amb_air_temp',
    'Sys1 Suct Superheat': 'sys1_suct_superheat', 'Sys1 EEV Out Pct': 'sys1_eev_out_pct',
    'Sys1 Com1 Hour': 'sys1_com1_hour', 'Sys1 Com2 Hour': 'sys1_com2_hour',
    'Sys1 Com3 Hour': 'sys1_com3_hour', 'Sys2 Com1 Hour': 'sys2_com1_hour',
    'Sys2 Com2 Hour': 'sys2_com2_hour', 'Sys2 Com3 Hour': 'sys2_com3_hour',
    'Sys1 Com1 Run': 'sys1_com1_run', 'Sys1 Com2 Run': 'sys1_com2_run',
    'Sys1 Com3 Run': 'sys1_com3_run', 'Sys2 Com1 Run': 'sys2_com1_run',
    'Sys2 Com2 Run': 'sys2_com2_run', 'Sys2 Com3 Run': 'sys2_com3_run',
    'Sys2 Suct Temp': 'sys2_suct_temp', 'Sys2 Suct Superheat': 'sys2_suct_superheat',
    'Sys2 EEV Out Pct': 'sys2_eev_out_pct', 'Sys1 Disch Superheat': 'sys1_disch_superheat',
    'Sys2 Disch Temp': 'sys2_disch_temp', 'Sys2 Disch Superheat': 'sys2_disch_superheat',
    'Sys1 Fault Code': 'sys1_fault_code', 'Sys2 Fault Code': 'sys2_fault_code',
    'Sys1 Cond Temp': 'sys1_cond_temp', 'Out Amb Temp': 'out_amb_temp',
    'Sys1 Eductor Temp': 'sys1_eductor_temp', 'Sys2 Eductor Temp': 'sys2_eductor_temp',
    'Sys1 Alarm': 'sys1_alarm', 'Sys2 Alarm': 'sys2_alarm',
    'Sys1 Warning Code': 'sys1_warning_code', 'Sys2 Warning Code': 'sys2_warning_code',
    'Sys1 Fan Power': 'sys1_fan_power', 'Sys1 Comp Power': 'sys1_comp_power',
    'Sys2 Fan Power': 'sys2_fan_power', 'Sys2 Comp Power': 'sys2_comp_power',
    'Motor Ph A Current': 'motor_ph_a_current', 'Motor Ph B Current': 'motor_ph_b_current',
    'Motor Ph C Current': 'motor_ph_c_current',
    'Motor Ph A Voltage': 'motor_ph_a_voltage', 'Motor Ph B Voltage': 'motor_ph_b_voltage',
    'Motor Ph C Voltage': 'motor_ph_c_voltage', 'Seal Press Diff': 'seal_press_diff',
    'Filter Diff Press': 'filter_diff_press', 'Output Voltage': 'output_voltage',
}

@api_bp.route('/chiller_data/<string:chiller_id>')
def get_chiller_data(chiller_id):
    chiller_details = {}
    parameters_by_section = {}
    last_updated_timestamp = None
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM chillers WHERE id = %s", (chiller_id,))
            chiller_details = cursor.fetchone()

            latest_chiller_data = None
            cursor.execute(
                "SELECT * FROM chiller_datas WHERE chiller_id = %s ORDER BY timestamp DESC LIMIT 1",
                (chiller_id,)
            )
            latest_chiller_data = cursor.fetchone()
            
            if latest_chiller_data and 'timestamp' in latest_chiller_data:
                last_updated_timestamp = latest_chiller_data['timestamp']

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

            for param in all_parameters:
                section = param['section']
                if section not in parameters_by_section:
                    parameters_by_section[section] = []
                
                data_col_name = parameter_data_map.get(param['name'])
                if latest_chiller_data and data_col_name and data_col_name in latest_chiller_data:
                    param['current_value'] = latest_chiller_data[data_col_name]
                else:
                    param['current_value'] = None
                parameters_by_section[section].append(param)
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    response_data = {
        'chiller_details': chiller_details,
        'sections': parameters_by_section,
        'last_updated_timestamp': last_updated_timestamp.isoformat() if last_updated_timestamp else 'N/A'
    }
    
    return jsonify(response_data)