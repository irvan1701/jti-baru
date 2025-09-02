from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from auth import auth_bp
from datetime import datetime, timedelta
import locale
import os
from flask_bcrypt import Bcrypt
import mysql.connector
import requests
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Konfigurasi kunci rahasia dari variabel lingkungan atau gunakan default
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key_here')

# Konfigurasi database MySQL
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'jti-new2')
app.config['MYSQL_PORT'] = os.environ.get('MYSQL_PORT', '3306')

bcrypt = Bcrypt(app)
app.register_blueprint(auth_bp)


class PDFWithMargins(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', top_margin=20, bottom_margin=10, left_margin=10, right_margin=10, generation_time="", with_template_background=False, header_align_left=True):
        super().__init__(orientation, unit, format)
        self.set_top_margin(top_margin)
        self.set_left_margin(left_margin)
        self.set_right_margin(right_margin)
        self.set_auto_page_break(auto=True, margin=bottom_margin)
        self.generation_time = generation_time
        self.with_template_background = with_template_background
        self.header_align_left = header_align_left

    def header(self):
        # Add background only to portrait content pages
        is_portrait = self.w < self.h
        if self.with_template_background and self.page_no() > 1 and is_portrait:
            template_image_path = os.path.join(app.static_folder, 'images', 'template.png')
            if os.path.exists(template_image_path):
                self.image(template_image_path, x=0, y=0, w=self.w, h=self.h)

        # Set font for header
        self.set_font('helvetica', 'I', 8)
        
        if self.header_align_left:
            # Add the cell, aligned to the left
            self.cell(0, 9, f'Generated at: {self.generation_time}', 0, 0, 'L')
        else:
            # Align right
            page_width = self.w - self.l_margin - self.r_margin
            text_width = self.get_string_width(f'Generated at: {self.generation_time}')
            self.set_x(page_width - text_width + self.l_margin)
            self.cell(text_width, 10, f'Generated at: {self.generation_time}', 0, 0, 'R')

        # Move down to start content below header
        self.ln(15)

    def footer(self):
        # Page number
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, 'Page %s' % self.page_no(), 0, 0, 'C')

# --- HARDCODED LOOKUP TABLES (Lengkap) ---
safety_codes = {
    0: "No Safety Faults Present", 1: "Evaporator - Low Pressure", 2: "Evaporator - Transducer Or Leaving Liquid Probe",
    3: "Evaporator - Transducer Or Temperature Sensor", 4: "Condenser - High Pressure Contacts Open",
    5: "Condenser - High Pressure", 6: "Condenser - Pressure Transducer Out Of Range",
    7: "Auxiliary Safety - Contacts Closed", 8: "Discharge - Low Temperature", 9: "Discharge - High Temperature",
    10: "Oil - High Sump Temperature", 11: "Oil - Low Differential Pressure", 12: "Oil - High Differential Pressure",
    13: "Oil - Pump Pressure Transducer Out Of Range", 14: "Oil - Sump Pressure Transducer Out Of Range",
    15: "Motor - Lack Of Motor Oil Change", 16: "Sales Order - Invalid Compressor Model",
    17: "Sales Order - Invalid Gear Code", 18: "Oil - Differential Pressure Calibration", 19: "Safety Stop",
    20: "Oil - Variable Speed Pump - Setpoint Not Achieved", 21: "Control Panel - Power Failure",
    22: "Control Panel - Loss Of Control Voltage", 23: "MOTOR OR STARTER - CURRENT IMBALANCE",
    24: "Thrust Bearing - Proximity Probe Clearance", 25: "Thrust Bearing - Proximity Probe Uncalibrated",
    26: "Thrust Bearing - Proximity Probe Out Of Range", 27: "Thrust Bearing - High Oil Temperature",
    28: "Thrust Bearing - Oil Temperature Sensor", 29: "VSD - High Heatsink Temperature",
    30: "VSD - 105% MOTOR CURRENT OVERLOAD", 31: "VSD - HIGH PHASE A INVERTER HEATSINK TEMPERATURE",
    32: "VSD - HIGH PHASE B INVERTER HEATSINK TEMPERATURE",
    33: "VSD - HIGH PHASE C INVERTER HEATSINK TEMPERATURE", 34: "VSD - HIGH CONVERTER HEATSINK TEMPERATURE",
    35: "VSD - PRECHARGE LOCKOUT", 36: "HARMONIC FILTER - HIGH HEATSINK TEMPERATURE",
    37: "HARMONIC FILTER - HIGH TOTAL DEMAND DISTORTION", 38: "LCSSS - PHASE ROTATION",
    39: "LCSSS - MOTOR OR STARTER - CURRENT IMBALANCE", 40: "LCSSS - 105% MOTOR CURRENT OVERLOAD",
    41: "LCSSS - HIGH INSTANTANEOUS CURRENT", 42: "LCSSS - OPEN SCR", 43: "LCSSS - PHASE A SHORTED SCR",
    44: "LCSSS - PHASE B SHORTED SCR", 45: "LCSSS - PHASE C SHORTED SCR",
    46: "LCSSS - HIGH PHASE A HEATSINK TEMPERATURE", 47: "LCSSS - HIGH PHASE B HEATSINK TEMPERATURE",
    48: "LCSSS - HIGH PHASE C HEATSINK TEMPERATURE", 49: "Starter - Invalid Motor Selection",
    50: "Oil or Conduser Transducer Error", 51: "Evaporator - Low Pressure",
    52: "Evaporator - low Pressure - Smart Freeze", 53: "Surge Protection - Excess Surge",
    54: "VSD - HIGH INVERTER BASEPLATE TEMPERATURE", 55: "HARMONIC FILTER - HIGH BASEPLATE TEMPERATURE",
    56: "Thrust Bearing - Proximity Probe Clearance", 57: "Thrust Bearing - Limit Switch Open",
    58: "VGD Actuator - Positioning Fault", 59: "Oil - Sump Or Pump Transducer Error",
    60: "Motor - High Housing Temperature", 61: "Motor - High Winding Temperature",
    62: "Motor - High Bearing Temperature", 63: "VSD - HIGH PHASE A INVERTER BASEPLATE TEMPERATURE",
    64: "VSD - HIGH PHASE B INVERTER BASEPLATE TEMPERATURE",
    65: "VSD - HIGH PHASE C INVERTER BASEPLATE TEMPERATURE", 66: "VSD - MOTOR CURRENT IMBALANCE",
    67: "Condenser - High Pressure - Stopped", 68: "OIL - HIGH SUPPLY TEMPERATURE",
    69: "Motor - High Bearing Vibration", 70: "SALES ORDER - INVALID MODEL NUMBER",
    71: "LCSSS - PHASE A OPEN SCR", 72: "LCSSS - PHASE B OPEN SCR", 73: "LCSSS - PHASE C OPEN SCR",
    74: "Motor - Lack Of Bearing Lubrication", 75: "VSD - LOW FREQUENCY DETECTED",
    76: "VSD - Feedback Sensor", 77: "VSD - Control Fault", 78: "VSD - Drive Boot Failure",
    79: "MVSSS - PHASE ROTATION", 80: "MVSSS - MOTOR OR STARTER - CURRENT IMBALANCE",
    81: "MVSSS - 105% MOTOR CURRENT OVERLOAD", 82: "MVSSS - HIGH INSTANTANEOUS CURRENT",
    83: "MVSSS - FAILED SCR", 84: "MVSSS - HIGH HEATSINK TEMPERATURE", 85: "MVSSS - GROUND FAULT",
    86: "MVSSS - CONTACTOR FAULT", 87: "MVSSS - CONTROL BOARD FAULT", 88: "MVSSS - DISCONNECT FAULT",
    89: "VSD - POWER TRANSFORMER HIGH TEMPERATURE", 90: "VSD - HIGH OUTPUT FREQUENCY",
    91: "MVVSD - GROUND FAULT", 92: "VSD - MAIN CONTROL BOARD FAULT", 93: "MVVSD - CONTACTOR FAULT",
    94: "MVVSD - INTERLOCK FAULT", 95: "VSD - LOGIC BOARD PLUG", 96: "VSD - INPUT CURRENT OVERLOAD",
    97: "VSD - HIGH PHASE A INPUT BASEPLATE TEMPERATURE",
    98: "VSD - HIGH PHASE B INPUT BASEPLATE TEMPERATURE",
    99: "VSD - HIGH PHASE C INPUT BASEPLATE TEMPERATURE", 100: "MOTOR - LOW WINDING TEMPERATURE",
    101: "VSD - INVALID PWM SOFTWARE", 102: "VSD - BASEPLATE TEMPERATURE IMBALANCE",
    103: "VSD - DC BUS PRE-REGULATION LOCKOUT", 104: "VSD - GROUND FAULT",
    105: "VSD - HIGH INSTANTANEOUS CURRENT", 106: "MOTOR CURRENT > 15% FLA",
    107: "VSD - FREQUENCY > 0 HZ", 108: "VSD - PHASE A INPUT DCCT", 109: "VSD - PHASE B INPUT DCCT",
    110: "VSD - PHASE C INPUT DCCT", 111: "VSD - HIGH TOTAL DEMAND DISTORTION", 112: "Motor - Coiling Coil Leak",
    113: "MVVSD - Excessive Shutdowns", 114: "Isolation Valves - Not Opened",
    115: "VSD - OUTPUT PHASE ROTATION", 116: "VSD - Phase Locked Loop",
    117: "VSD - HIGH PHASE A INSTANTANEOUS CURRENT",
    118: "VSD - HIGH PHASE B INSTANTANEOUS CURRENT",
    119: "VSD - HIGH PHASE C INSTANTANEOUS CURRENT", 120: "VSD - Line Voltage Phase Rotation",
    121: "VSD - INPUT DCCT OFFSET LOCKOUT", 122: "VSD - LOGIC BOARD HARDWARE",
    123: "VSD - RECTIFIER PROGRAM FAULT", 124: "VSD - INVERTER PROGRAM FAULT",
    125: "VSD - DC BUS LOCKOUT - DO NOT RECYCLE POWER", 126: "VSD - MOTOR CURREN THD FAULT",
    127: "VSD - HIGH PHASE A MOTOR CURRENT", 128: "VSD - HIGH PHASE B MOTOR CURRENT",
    129: "VSD - HIGH PHASE C MOTOR CURRENT",
    130: "VSD - HIGH PHASE A MOTOR BASEPLATE TEMPERATURE",
    131: "VSD - HIGH PHASE B MOTOR BASEPLATE TEMPERATURE",
    132: "VSD - HIGH PHASE C MOTOR BASEPLATE TEMPERATURE", 133: "VSD - PHASE A MOTOR DCCT",
    134: "VSD - PHASE B MOTOR DCCT", 135: "VSD - PHASE C MOTOR DCCT",
    136: "Oil - High Sump Pressure", 137: "MBC - OVERSPEED FAULT", 138: "MBC - WATCHDOG",
    139: "MBC - POWER SUPPLY FAULT", 140: "MBC - HIGH HEATSINK TEMPERATURE",
    141: "MBC - HIGH DC BUS VOLTAGE", 142: "MBC - AMPLIFIER FUSE",
    143: "MBC - HIGH BEARING J TEMPERATURE", 144: "MBC - HIGH BEARING H1 TEMPERATURE",
    145: "MBC - HIGH BEARING H2 TEMPERATURE", 146: "MBC - HIGH BEARING K TEMPERATURE",
    147: "MBC - GROUND FAULT", 148: "MBC - LOW GATE VOLTAGE", 149: "MBC - HIGH GATE VOLTAGE",
    150: "MBC - HIGH AMPLIFIER TEMPERATURE", 151: "MBC - HIGH AMPLIFIER VOLTAGE",
    152: "MBC - FAULT CONTACTS OPEN", 153: "MBC - INITIALIZATION FAILURE", 154: "MBC - NOT LEVITATED",
    155: "SYSTEM - STARTUP FAILURE", 156: "UPS - Battery Not Connected",
    157: "UPS - Inverter Low Battery Voltage", 158: "MBC - SPEED SENSOR FAULT",
    159: "MBC - POWER FAIL LANDING", 160: "COMPRESSOR - LOW DISCHARGE SUPERHEAT",
    161: "MVSSS - HIGH HEATSINK  1 TEMPERATURE", 162: "MVSSS - HIGH HEATSINK  2 TEMPERATURE",
    163: "MVSSS - HIGH HEATSINK  3 TEMPERATURE", 164: "MOTOR CONTROLLER - FAULT CONTACTS OPEN",
    165: "VSD - HIGH PHASE A2 INSTANTANEOUS CURRENT",
    166: "VSD - HIGH PHASE B2 INSTANTANEOUS CURRENT",
    167: "VSD - HIGH PHASE C2 INSTANTANEOUS CURRENT",
    168: "VSD - HIGH PHASE A2 INVERTER BASEPLATE TEMPERATURE",
    169: "VSD - HIGH PHASE B2 INVERTER BASEPLATE TEMPERATURE",
    170: "VSD - HIGH PHASE C2 INVERTER BASEPLATE TEMPERATURE",
    171: "VSD - HIGH CONVERTER 2 HEATSINK TEMPERATURE", 172: "VSD - MOTOR CURRENT 2 IMBALANCE",
    173: "VSD - MOTOR CURRENT MISMATCH", 174: "VSD - HIGH PHASE A INPUT CURRENT",
    175: "VSD - HIGH PHASE B INPUT CURRENT", 176: "VSD - HIGH PHASE C INPUT CURRENT",
    177: "VSD - HIGH INPUT CURRENT TDD", 178: "INTERNAL ERROR - NO TIMER HANDERS AVAILABLE",
    179: "WATCHDOG - SOFTWARE REBOOT", 180: "VSD - PRECHARGE LOCKOUT 2",
    181: "VSD - BASEPLATE TEMPERATURE IMBALANCE 2",
    182: "OIL - VARIABLE SPEED PUMP - HIGH RATE OF CHANGE", 183: "VSD - HIGH MOTOR HARMONICS",
    184: "VSD - CAPACITOR FAULT", 185: "VSD - ELECTRICAL SGNATURE BOARD"
}

cycling_codes = {
     0: "No Cycling Faults Present", 1: "Multiunit Cycling - Contacts Open", 2: "System Cycling - Contact Open",
    3: "Oil - Low Temperature Differntial", 4: "Oil - Low Sump Temperature", 5: "Control Panel - Power Failure",
    6: "Leaving Chilled Liquid - Low Temperature", 7: "Leaving Chilled Liquid - Flow Switch Open",
    8: "Condenser - Flow Switch Open", 9: "MOTOR CONTROLLER - FAULT CONTACTS OPEN",
    10: "MOTOR CONTROLLER - LOSS OF CURRENT", 11: "POWER FAULT", 12: "Control Panel - Schedule",
    13: "Starter - Low Supply Line Voltage", 14: "Starter - High Supply Line Voltage",
    15: "Proximity Probe - Low Supply Voltage", 16: "Oil - Variable Speed Pump - Drive Contacts Open",
    17: "VSD - INITIALIZATION FAILED", 18: "VSD Shutdown - Requesting Fault Data",
    19: "VSD - HIGH PHASE A INSTANTANEOUS CURRENT", 20: "VSD - HIGH PHASE B INSTANTANEOUS CURRENT",
    21: "VSD - HIGH PHASE C INSTANTANEOUS CURRENT", 22: "VSD - PHASE A GATE DRIVER",
    23: "VSD - PHASE B GATE DRIVER", 24: "VSD - PHASE C GATE DRIVER", 25: "VSD - SINGLE PHASE INPUT POWER",
    26: "VSD - HIGH DC BUS VOLTAGE", 27: "VSD - LOGIC BOARD POWER SUPPLY",
    28: "VSD - LOW DC BUS VOLTAGE", 29: "VSD - DC BUS VOLTAGE IMBALANCE",
    30: "VSD - HIGH INTERNAL AMBIENT TEMPERATURE", 31: "VSD - INVALID CURRENT SCALE SELECTION",
    32: "VSD - LOW PHASE A INVERTER HEATSINK TEMPERATURE",
    33: "VSD - LOW PHASE B INVERTER HEATSINK TEMPERATURE",
    34: "VSD - LOW PHASE C INVERTER HEATSINK TEMPERATURE", 35: "VSD - LOW CONVERTER HEATSINK TEMPERATURE",
    36: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE",
    37: "VSD - PRECHARGE - LOW DC BUS VOLTAGE", 38: "VSD - LOGIC BOARD PROCESSOR",
    39: "VSD - RUN SIGNAL", 40: "VSD - SERIAL RECEIVE", 41: "VSD - Stop Contacts Open",
    42: "Harmonic Filter - Logic Board Or Communications", 43: "HARMONIC FILTER - HIGH DC BUS VOLTAGE",
    44: "HARMONIC FILTER - HIGH PHASE A CURRENT", 45: "HARMONIC FILTER - HIGH PHASE B CURRENT",
    46: "HARMONIC FILTER - HIGH PHASE C CURRENT", 47: "HARMONIC FILTER - PHASE LOCKED LOOP",
    48: "Harmonic Filter - Precharge - Low DC Bus Voltage", 49: "HARMONIC FILTER - LOW DC BUS VOLTAGE",
    50: "HARMONIC FILTER - DC BUS VOLTAGE IMBALANCE",
    51: "HARMONIC FILTER - INPUT CURRENT OVERLOAD", 52: "HARMONIC FILTER - LOGIC BOARD POWER SUPPLY",
    53: "HARMONIC FILTER - RUN SIGNAL", 54: "HARMONIC FILTER - DC CURRENT TRANSFORMER 1",
    55: "HARMONIC FILTER - DC CURRENT TRANSFORMER 2", 56: "LCSSS Initialization Failed",
    57: "LCSSS Shutdown - Requesting Full Data", 58: "LCSSS - LOW PHASE A TEMPERATURE SENSOR",
    59: "LCSSS - LOW PHASE B TEMPERATURE SENSOR", 60: "LCSSS - LOW PHASE C TEMPERATURE SENSOR",
    61: "LCSSS - PHASE LOCKED LOOP", 62: "LCSSS - POWER FAULT",
    63: "LCSSS - HIGH SUPPLY LINE VOLTAGE", 64: "LCSSS - LOW SUPPLY LINE VOLTAGE",
    65: "LCSSS - INVALID CURRENT SCALE SELECTION", 66: "LCSSS - RUN SIGNAL", 67: "LCSSS - SERIAL RECEIVE",
    68: "LCSSS - Stop Contacts Open", 69: "Motor Auto Lubrication In Progress",
    70: "Control Panel - Loss Of Control Voltage", 71: "LCSSS - LOGIC BOARD PROCESSOR",
    72: "LCSSS - LOGIC BOARD POWER SUPPLY", 73: "VSD - Serial Communications",
    74: "LCSSS - Serial Communications", 75: "LCSSS - PHASE LOSS",
    76: "VSD - LOW INVERTER BASEPLATE TEMPERATURE", 77: "Expansion I/O - Serial Communications",
    78: "VSD - LOW PHASE A INVERTER BASEPLATE TEMPERATURE",
    79: "VSD - LOW PHASE B INVERTER BASEPLATE TEMPERATURE",
    80: "VSD - LOW PHASE C INVERTER BASEPLATE TEMPERATURE", 81: "Motor Controller - Contacts Open",
    82: "MVVSD - Serial Communications", 83: "VSD - Input Power Transformer",
    84: "VSD - Input Over-Voltage", 85: "VSD - LOSS OF COOLING FAN",
    86: "VSD - HIGH INSTANTANEOUS CURRENT", 87: "MVSSS - Initialization Failed",
    88: "MVSSS Shutdown - Requesting Full Data", 89: "MVSSS - POWER FAULT",
    90: "MVSSS - HIGH SUPPLY LINE VOLTAGE", 91: "MVSSS - LOW SUPPLY LINE VOLTAGE",
    92: "MVSSS - RUN SIGNAL", 93: "MVSSS - Serial Communications",
    94: "MVSSS - Stop Contacts Open", 95: "MVSSS - LOGIC BOARD POWER SUPPLY",
    96: "MVSSS - PHASE LOSS", 97: "REFRIGERANT TYPE NOT SET",
    98: "VSD - Serial Communications", 99: "LCSSS - Serial Comms",
    100: "VSD - Serial Communications", 101: "Auto Detect - Serial Communications",
    102: "VSD - DC BUS VOLTAGE IMBALANCE - AU", 103: "VSD - DC BUS VOLTAGE IMBALANCE - AL",
    104: "VSD - DC BUS VOLTAGE IMBALANCE - BU", 105: "VSD - DC BUS VOLTAGE IMBALANCE - BL",
    106: "VSD - DC BUS VOLTAGE IMBALANCE - CU", 107: "VSD - DC BUS VOLTAGE IMBALANCE - CL",
    108: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - AU",
    109: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - AL",
    110: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - BU",
    111: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - BL",
    112: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - CU",
    113: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - CL", 114: "VSD - HIGH DC BUS VOLTAGE - AU",
    115: "VSD - HIGH DC BUS VOLTAGE - AL", 116: "VSD - HIGH DC BUS VOLTAGE - BU",
    117: "VSD - HIGH DC BUS VOLTAGE - BL", 118: "VSD - HIGH DC BUS VOLTAGE - CU",
    119: "VSD - HIGH DC BUS VOLTAGE - CL", 120: "VSD - GATE DRIVER - ANU",
    121: "VSD - GATE DRIVER - ANL", 122: "VSD - GATE DRIVER - AMU",
    123: "VSD - GATE DRIVER - AML", 124: "VSD - GATE DRIVER - BNU",
    125: "VSD - GATE DRIVER - BNL", 126: "VSD - GATE DRIVER - BMU",
    127: "VSD - GATE DRIVER - BML", 128: "VSD - GATE DRIVER - CNU",
    129: "VSD - GATE DRIVER - CNL", 130: "VSD - GATE DRIVER - CMU",
    131: "VSD - GATE DRIVER - CML", 132: "VSD - INPUT POWER SUPPLY",
    133: "VSD - HIGH PHASE A INPUT CURRENT", 134: "VSD - HIGH PHASE B INPUT CURRENT",
    135: "VSD - HIGH PHASE C INPUT CURRENT", 136: "VSD - HIGH PHASE A MOTOR CURRENT",
    137: "VSD - HIGH PHASE B MOTOR CURRENT", 138: "VSD - HIGH PHASE C MOTOR CURRENT",
    139: "VSD - PHASE A INPUT GATE DRIVER", 140: "VSD - PHASE B INPUT GATE DRIVER",
    141: "VSD - PHASE C INPUT GATE DRIVER", 142: "VGD Actuator - Serial Communications",
    143: "VSD - INVALID VSD MODEL", 144: "VSD - BASEPLATE TEMPERATURE IMBALANCE",
    145: "VSD - LOW PHASE A INPUT BASEPLATE TEMPERATURE",
    146: "VSD - LOW PHASE B INPUT BASEPLATE TEMPERATURE",
    147: "VSD - LOW PHASE C INPUT BASEPLATE TEMPERATURE", 148: "VSD - PHASE LOCKED LOOP",
    149: "VSD - LINE VOLTAGE PHASE ROTATION", 150: "VSD - PRECHARGE - LOW DC BUS VOLTAGE 1",
    151: "VSD - Input Voltage Imbalance", 152: "VSD - DC BUS PRE-REGULATION",
    153: "VSD - LOGIC BOARD PROCESSOR", 154: "MVSSS - SERIAL RECEIVE",
    155: "VSD - Identifying Drive", 156: "Leaving Condensor Liquid - High Temperature",
    157: "Condenser - Freeze Threat - Flow Switch Open", 158: "Isolation Valves - Not Closed",
    159: "VSD - PHASE A INPUT DCCT OFFSET", 160: "VSD - PHASE B INPUT DCCT OFFSET",
    161: "VSD - PHASE C INPUT DCCT OFFSET", 162: "VSD - INVALID SETPOINTS",
    163: "VSD - PRECHARGE - LOW DC BUS VOLTAGE 2", 164: "VSD - SERIAL RECEIVE",
    165: "VSD - PHASE A MOTOR GATE DRIVER", 166: "VSD - PHASE B MOTOR GATE DRIVER",
    167: "VSD - PHASE C MOTOR GATE DRIVER",
    168: "VSD - LOW PHASE A MOTOR BASEPLATE TEMPERATURE",
    169: "VSD - LOW PHASE B MOTOR BASEPLATE TEMPERATURE",
    170: "VSD - LOW PHASE C MOTOR BASEPLATE TEMPERATURE", 171: "VSD - NOT RUNNING",
    172: "Motor - Lack Of Bearing Lubrication", 173: "Evaporator - Low Pressure",
    174: "Expansion I/O - Serial Communications", 175: "Evaporator - Low Pressure - Smart Freeze",
    176: "MBC - LOW DC BUS VOLTAGE", 177: "MBC - J RADIAL POSITION",
    178: "MBC - K RADIAL POSITION", 179: "MBC - H AXIAL POSITION", 180: "MBC - FAULT CONTACTS OPEN",
    181: "MBC - SERIAL COMMUNICATIONS", 182: "SYSTEM - STARTUP FAILURE",
    183: "UPS - Line Low Battery Voltage", 184: "MBC - CALIBRATION FAULT",
    185: "MBC - BEARING CALIBRATION REQUIRED", 186: "MOTOR CONTROLLER - INITIALIZATION FAILURE",
    187: "MOTOR CONTROLLER - SERIAL COMMUNICATION",
    188: "HARMONIC FILTER - PRECHARGE - LOW DC BUS VOLTAGE 1",
    189: "HARMONIC FILTER - PRECHARGE - LOW DC BUS VOLTAGE 2",
    190: "VSD - HIGH PHASE A2 INSTANTANEOUS CURRENT",
    191: "VSD - HIGH PHASE B2 INSTANTANEOUS CURRENT",
    192: "VSD - HIGH PHASE C2 INSTANTANEOUS CURRENT", 193: "VSD - PHASE A2 GATE DRIVER",
    194: "VSD - PHASE B2 GATE DRIVER", 195: "VSD - PHASE C2 GATE DRIVER",
    196: "VSD - HIGH DC BUS 2 VOLTAGE", 197: "VSD - LOW DC BUS 2 VOLTAGE",
    198: "VSD - DC BUS 2 VOLTAGE IMBALANCE",
    199: "VSD - LOW PHASE A2 INVERTER BASEPLATE TEMPERATURE",
    200: "VSD - LOW PHASE B2 INVERTER BASEPLATE TEMPERATURE",
    201: "VSD - LOW PHASE C2 INVERTER BASEPLATE TEMPERATURE", 202: "VSD - LOW CONVERTER 2 HEATSINK TEMPERATURE",
    203: "VSD - PRECHARGE - DC BUS 2 VOLTAGE IMBALANCE",
    204: "VSD - PRECHARGE - LOW DC BUS 2 VOLTAGE 1", 205: "VSD - PRECHARGE - LOW DC BUS 2 VOLTAGE 2",
    206: "VSD - DC BUS VOLTAGE MISMATCH", 207: "UPS - NOT CHARGING",
    208: "VSD - SINGLE PHASE INPUT POWER 2", 209: "VSD - 105% MOTOR CURRENT OVERLOAD",
    210: "VSD - BASEPLATE TEMPERATURE IMBALANCE 2"
}

warning_codes = {
     0: "No Warning Present", 1: "Real-Time Clock Failure", 2: "Setpoint Override",
    3: "Condensor Or Evaporator Transducer Error", 4: "Evaporator - Low Pressure Limit",
    5: "Condensor - High Pressure Limit", 6: "OIL - HIGH SUPPLY TEMPERATURE",
    7: "COMPRESSOR - LOW DISCHARGE SUPERHEAT LIMIT", 8: "WARNING - CONDENSER - HIGH TUBE CLEANING TIME",
    9: "Standby Lube - Low Oil Pressure", 10: "Warning - Standby Lube Inihibited",
    11: "WARNING - VSD - HIGH CONVERTER OR INVERTER TEMPERATURE",
    12: "WARNING - SALES ORDER - INVALID SERIAL NUMBER", 13: "VGD Not Calibrated",
    14: "VGD Actuator Switch Open", 15: "PRV Not Calibrated", 16: "Vanes Uncalibrated - Fixed Speed",
    17: "WARNING - HARMONIC FILTER - OPERATION INIHIBITED", 18: "Harmonic Filter - Data Loss",
    19: "Auto Lube Req'd On Next Shutdown", 20: "Auto Lube Grease Level Low", 21: "Auto Lube Failed",
    22: "Motor Oil Change Suggested", 23: "Motor Oil Change Required", 24: "Lack Of Motor Oil Change",
    25: "Seal Lubrication In Process", 26: "External I/O - Serial Communications",
    27: "WARNIING - MMB - SERIAL COMMUNICATIONS",
    28: "WARNING - HARMONIC FILTER - INPUT FREQUENCY RANGE",
    29: "Surge Protection - Excess Surge Limit", 30: "Excess Surge Detected",
    31: "WARNING - HARMONIC FILTER - INVALID MODEL", 32: "Motor - High Housing Temperature",
    33: "KW Meter Not Calibrated", 34: "Condenser Or VGD Sensor Failure", 35: "Conditions Override VGD",
    36: "Motor Bearing Lube Suggested", 37: "Motor Bearing Lube Required", 38: "Motor Bearing Lube Not Done",
    39: "WARNING - HARMONIC FILTER - DATA LOSS", 40: "Motor - High Winding Temperature",
    41: "Motor - High Bearing Temperature", 42: "Motor - High Bearing Vibration",
    43: "Motor - Bearing Vibration Baseline Not Set",
    44: "WARNING - VSD - INPUT VOLTAGE IMBALANCE", 45: "WARNING - HARMONIC FILTER - NOT RUNNING",
    46: "Condenser - freeze Threat From Low Pressure", 47: "Liquid Level Setpoint Not Achieved",
    48: "VSD - DC Bus Active", 49: "WARNING - LOSS OF SUBCOOLER LIQUID SEAL",
    50: "Oil - High Sump Pressure",
    51: "ECON LCSSS - Invalid Current Scale Selection", 52: "ECON LCSSS - Phase Loss",
    53: "ECON LCSSS - Phase Locked Loop", 54: "ECON LCSSS - Power Fault",
    55: "ECON LCSSS - Run Signal", 56: "ECON LCSSS - Motor Current Imbalance",
    57: "ECON LCSSS - 105% Motor Current Overload", 58: "ECON LCSSS - High Motor Current",
    59: "ECON LCSSS - High Supply Line Voltage", 60: "ECON LCSSS - Low Supply Line Voltage",
    61: "ECON LCSSS - Open SCR", 62: "ECON LCSSS - Phase A Shorted SCR",
    63: "ECON LCSSS - Phase B Shorted SCR", 64: "ECON LCSSS - Phase C Shorted SCR",
    65: "ECON LCSSS - High Phase A Heatsink Temp - Stopped",
    66: "ECON LCSSS - High Phase B Heatsink Temp - Stopped",
    67: "ECON LCSSS - High Phase C Heatsink Temp - Stopped",
    68: "ECON LCSSS - High Phase A Heatsink Temperature",
    69: "ECON LCSSS - High Phase B Heatsink Temperature",
    70: "ECON LCSSS - High Phase C Heatsink Temperature",
    71: "ECON LCSSS - Low Phase A Temperature Sensor",
    72: "ECON LCSSS - Low Phase B Temperature Sensor",
    73: "ECON LCSSS - Low Phase C Temperature Sensor", 74: "ECON LCSSS - Serial Receive",
    75: "ECON LCSSS - Logic Board Power Supply", 76: "ECON LCSSS - Phase Rotation",
    77: "ECON LCSSS - Undefined Fault", 78: "COND OR ECON XDCR ERROR",
    79: "EVAP OR ECON XDCR ERROR", 80: "COND OR ECON VGD XDCR FAILURE", 81: "ECON HIGH STALL - VGD OVERRIDE",
    82: "ECON STANDBY FAULT - LOW OIL PRESSURE", 83: "ECON SEAL LUBRICATION INHIBITED",
    84: "ECON MOTOR - BEARING LUBE SUGGESTED", 85: "ECON MOTOR - BEARING LUBE REQUIRED",
    86: "ECON MOTOR - BEARING LUBE NOT ACHIEVED",
    87: "ECON LIQUID LEVEL SETPOINT NOT ACHIEVED", 88: "ECONOMIZER - LEVEL HIGH", 89: "ECON ANTI-RECYCLE",
    90: "ECON COMPRESSOR - PRV MOTOR SWITCH", 91: "ECONOMIZER - PRESSURE XDCR FAILURE",
    92: "ECON COMPRESSOR - HPCO SWITCH OPEN", 93: "ECON COMPRESSOR - GEAR RATIO INVALID",
    94: "ECON MOTOR - LINE FREQUENCY NOT SET", 95: "ECON DISCHARGE - LOW TEMPERATURE",
    96: "ECON DISCHARGE - HIGH TEMPERATURE",
    97: "ECON THRUST BEARING - LIMIT SWITCH OPEN",
    98: "ECON OIL - VSD PUMP - FAULT CONTACTS OPEN", 99: "ECON OIL - PUMP PRESSURE XDCR FAILURE",
    100: "ECON OIL - DIFF PRESSURE CALIBRATION",
    101: "ECON OIL - LOW DIFFERENTIAL PRESSURE", 102: "ECON OIL - HIGH DIFFERENTIAL PRESSURE",
    103: "ECON OIL - VSD PUMP - SETPOINT NOT ACHIEVED",
    104: "ECON MOTOR CONTROLLER - LOSS OF CURRENT",
    105: "ECON MOTOR CONTROLLER - SERIAL COMMUNICATIONS",
    106: "ECON MOTOR CONTROLLER - INITIALIZATION FAILED",
    107: "ECON MOTOR CONTROLLER - FAULT CONTACTS OPEN",
    108: "ECON MOTOR - LACK OF BEARING LUBRICATION",
    109: "ECON MOTOR - CURRENT > 15% FLA", 110: "ECON COMPRESSOR - PRV NOT CALIBRATED",
    111: "ECONOMIZEER - HIGH LEVEL (STOPPED)",
    112: "SALES ORDER - INVALID MOTOR VOLTS OR FLA", 113: "ECON MOTOR - HIGH WINDING TEMP",
    114: "ECON MOTOR - HIGH BEARING TEMP", 115: "ECON MOTOR - HIGH BEARING VIBRATION",
    116: "ECON MOTOR - VIBRATION BASELINE NOT SET", 117: "ECON MOTOR - HIGH WINDING TEMP SHUTDOWN",
    118: "ECON MOTOR - HIGH BEARING TEMP SHUTDOWN",
    119: "ECON MOTOR - HIGH BEARING VIBRATION SHUTDOWN",
    120: "ECON MOTOR - AUTO LUBRICATION IN PROGRESS", 121: "ECON AUTO LUBE REG'D ON NEXT SHUTDOWN",
    122: "ECON AUTO LUBE GREASE LEVEL LOW", 123: "ECON AUTO LUBE FAILED",
    124: "ECON MMB I/O SERIAL COMMUNICATIONS",
    125: "WARNING - UPS - BATTERY TEST FAILED", 126: "MBC - LOW AMPLIFIER RESISTANCE",
    127: "MBC - HIGH AMPLIFIER RESISTANCE", 128: "MBC - LOW AMPLIFIER CURRENT",
    129: "MBC - HIGH AMPLIFIER CURRENT", 130: "MBC - POSITION SENSOR ERROR",
    131: "WARNING - UPS - NOT CHARGING", 132: "UPS - Line Low Battery Voltage",
    133: "UPS - Battery Not Connected", 134: "UPS - Check Battery Connected",
    135: "WARNING - PURGE - HIGH COIL TEMP", 136: "WARNING - PURGE - HIGH COIL TEMP INHIBIT",
    137: "WARNING - PURGE - HIGH REGEN TANK TEMP", 138: "WARNING - PURGE - HIGH LEVEL",
    139: "WARNING - PURGE - EXCESS PURGE",
    140: "WARNING - PURGE - EQUALIZATION LOW SUCTION TEMP",
    141: "WARNING - PURGE - POSSIBLE AIR IN SYSTEM", 142: "WARNING - PURGE - OPERATION INHIBITED",
    143: "ECON MOTOR CONTROLLER - CONTACTS OPEN",
    144: "ECON MOTOR CONTROLLER - POWER FAULT",
    145: "WARNING - QUARTERLY SERVICE REQUIRED - CONTACT JCI",
    146: "WARNING - YEARLY SERVICE REQUIRED - CONTACT JCI",
    147: "WARNING - 3 YEAR SERVICE REQUIRED - CONTACT JCI",
    148: "WARNING - CHECK OIL SYSTEM",
    149: "WARNING - CONDENSER - HIGH SMALL TEMP DIFFERENCE",
    150: "WARNING - SYSTEM - REPLACE FILTER-DRIER",
    151: "WARNING - CONTROL PANEL - INTERNAL ERROR"
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            port=int(app.config['MYSQL_PORT'])
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

@app.context_processor
def inject_sites_for_nav():
    conn = get_db_connection()
    sites_with_status = []
    if not conn:
        return dict(all_sites_for_nav=sites_with_status)

    try:
        cursor = conn.cursor(dictionary=True)
        
        user_role = session.get('role')
        user_id = session.get('user_id')
        sites = []

        if user_role in ['Admin', 'Viewer']:
            cursor.execute("SELECT id, name FROM sites ORDER BY name")
        elif user_id:
            cursor.execute("""
                SELECT s.id, s.name
                FROM sites s
                JOIN user_site_access usa ON s.id = usa.site_id
                WHERE usa.user_id = %s
                ORDER BY s.name
            """, (user_id,))
        else:
            return dict(all_sites_for_nav=[])

        sites = cursor.fetchall()

        for site in sites:
            cursor.execute("SELECT id FROM chillers WHERE site_id = %s", (site['id'],))
            chillers_in_site = cursor.fetchall()
            chiller_ids = [chiller['id'] for chiller in chillers_in_site]

            site['alarm_status'] = 'none'
            site['alarms'] = []

            if chiller_ids:
                chiller_placeholders = ', '.join(['%s'] * len(chiller_ids))
                
                query_latest_data = f"""
                    SELECT cd.chiller_id, c.chiller_num, cd.safety_fault, cd.warning_fault, cd.cycling_fault
                    FROM chiller_datas cd
                    JOIN chillers c ON c.id = cd.chiller_id
                    INNER JOIN (
                        SELECT chiller_id, MAX(timestamp) as max_ts
                        FROM chiller_datas
                        WHERE chiller_id IN ({chiller_placeholders})
                        GROUP BY chiller_id
                    ) as latest ON cd.chiller_id = latest.chiller_id AND cd.timestamp = latest.max_ts
                """
                cursor.execute(query_latest_data, tuple(chiller_ids))
                faults_data = cursor.fetchall()

                active_alarms = []
                has_safety = False
                has_warning_or_cycling = False

                for fault in faults_data:
                    chiller_num_display = fault.get('chiller_num', '')
                    if fault['safety_fault'] and fault['safety_fault'] > 0:
                        has_safety = True
                        description = safety_codes.get(fault['safety_fault'], "Unknown Safety Fault")
                        active_alarms.append({'type': 'safety', 'description': description, 'chiller_num': chiller_num_display})
                    
                    if fault['warning_fault'] and fault['warning_fault'] > 0:
                        has_warning_or_cycling = True
                        description = warning_codes.get(fault['warning_fault'], "Unknown Warning Fault")
                        active_alarms.append({'type': 'warning', 'description': description, 'chiller_num': chiller_num_display})

                    if fault['cycling_fault'] and fault['cycling_fault'] > 0:
                        has_warning_or_cycling = True
                        description = cycling_codes.get(fault['cycling_fault'], "Unknown Cycling Fault")
                        active_alarms.append({'type': 'warning', 'description': description, 'chiller_num': chiller_num_display})

                if has_safety:
                    site['alarm_status'] = 'safety'
                elif has_warning_or_cycling:
                    site['alarm_status'] = 'warning'
                
                site['alarms'] = active_alarms
            
            sites_with_status.append(site)

    except Exception as e:
        print(f"Error injecting sites for nav: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
    return dict(all_sites_for_nav=sites_with_status)


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
            if cursor:
                cursor.close()
            if conn:
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
                       power_kW, ton_of_refrigeration, image_name AS gambar_url, chiller_type
                FROM chillers
                WHERE site_id = %s
                ORDER BY chiller_num
            """, (site_id,))
            chillers_raw = cursor.fetchall()
            chillers = [dict(c) for c in chillers_raw]

            for chiller in chillers:
                chiller['fla_status'] = 'stop' # Default status
                try:
                    # Menggunakan kolom `fla` dan threshold > 5 sesuai permintaan
                    cursor.execute("""
                        SELECT fla 
                        FROM chiller_datas 
                        WHERE chiller_id = %s 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (chiller['id'],))
                    latest_data = cursor.fetchone()
                    if latest_data and latest_data.get('fla') and latest_data['fla'] > 5:
                        chiller['fla_status'] = 'running'
                except mysql.connector.Error as e:
                    print(f"Warning: Gagal mengambil status untuk chiller {chiller['id']}. Pastikan kolom 'fla' ada. Error: {e}")

        except mysql.connector.Error as err:
            flash(f"Error saat mengambil daftar chiller: {err}", 'danger')
        finally:
            if cursor:
                cursor.close()
            if conn.is_connected():
                conn.close()
    
    session['current_site_id'] = site_id
    session['current_site_name'] = site_name

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('select_chiller.html', current_time=current_time, chillers=chillers, site_name=site_name, site_id=site_id)

@app.route('/monitor_chiller/<string:chiller_id>')
def monitor_chiller(chiller_id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk memantau chiller.', 'warning')
        return redirect(url_for('auth.login'))
    return redirect(url_for('test', chiller_id=chiller_id))

def translate_codes(data):
    """Fungsi pembantu untuk menerjemahkan kode numerik menjadi deskripsi."""
    if isinstance(data, list):
        for item in data:
            if 'safety_fault' in item:
                item['safety_fault_desc'] = safety_codes.get(item['safety_fault'], "Code Not Found")
            if 'cycling_fault' in item:
                item['cycling_fault_desc'] = cycling_codes.get(item['cycling_fault'], "Code Not Found")
            if 'warning_fault' in item:
                item['warning_fault_desc'] = warning_codes.get(item['warning_fault'], "Code Not Found")
    else:
        if 'safety_fault' in data:
            data['safety_fault_desc'] = safety_codes.get(data['safety_fault'], "Code Not Found")
        if 'cycling_fault' in data:
            data['cycling_fault_desc'] = cycling_codes.get(data['cycling_fault'], "Code Not Found")
        if 'warning_fault' in data:
            data['warning_fault_desc'] = warning_codes.get(data['warning_fault'], "Code Not Found")
    return data

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
    historical_data = []
    last_updated_timestamp = None

    now = datetime.now()
    start_date = request.args.get('start_date') or (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = request.args.get('end_date') or (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')

    if chiller_id:
        try:
            # 1. Mengambil data terbaru untuk tampilan utama
            response_latest = requests.get(f'http://127.0.0.1:8000/chillers/{chiller_id}/latest_data')
            response_latest.raise_for_status()
            
            raw_json_data = response_latest.json()
            if raw_json_data:
                latest_chiller_data = raw_json_data
                # LAKUKAN PENERJEMAHAN DI SINI
                latest_chiller_data = translate_codes(latest_chiller_data)
                
                if 'timestamp' in latest_chiller_data:
                    last_updated_timestamp = datetime.fromisoformat(latest_chiller_data['timestamp'])
            else:
                latest_chiller_data = None

            # 2. Mengambil data historis untuk grafik dengan filter waktu
            params = {'start_date': start_date, 'end_date': end_date}
            if start_date:
                params['start_date'] = datetime.fromisoformat(start_date).strftime('%Y-%m-%dT%H:%M:%S')
            if end_date:
                params['end_date'] = datetime.fromisoformat(end_date).strftime('%Y-%m-%dT%H:%M:%S')

            api_url = f'http://127.0.0.1:8000/chillers/{chiller_id}/history'
            response_history = requests.get(api_url, params=params)
            if response_history.status_code == 200:
                historical_data = response_history.json()
                # LAKUKAN PENERJEMAHAN DI SINI
                historical_data = translate_codes(historical_data)

            # Fallback: Jika tidak ada data pada rentang waktu default
            if not historical_data and not request.args.get('start_date') and not request.args.get('end_date'):
                if last_updated_timestamp:
                    flash('Tidak ada data dalam 12 jam terakhir. Menampilkan 12 jam data terakhir yang tersedia.', 'info')
                    end_date_dt = last_updated_timestamp
                    start_date_dt = end_date_dt - timedelta(hours=12)
                    params['start_date'] = start_date_dt.strftime('%Y-%m-%dT%H:%M:%S')
                    params['end_date'] = end_date_dt.strftime('%Y-%m-%dT%H:%M:%S')
                    start_date = start_date_dt.strftime('%Y-%m-%dT%H:%M')
                    end_date = end_date_dt.strftime('%Y-%m-%dT%H:%M')
                    response_history_fallback = requests.get(api_url, params=params)
                    if response_history_fallback.status_code == 200:
                        historical_data = response_history_fallback.json()
                        # LAKUKAN PENERJEMAHAN DI SINI
                        historical_data = translate_codes(historical_data)

            # 3. Ambil detail chiller dasar dari database
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT * FROM chillers WHERE id = %s", (chiller_id,))
                    chiller_details = cursor.fetchone()
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()

        except requests.exceptions.RequestException as e:
            flash(f'Gagal mengambil data dari API: {e}', 'danger')
            print(f"Error fetching data from API: {e}")
        except Exception as e:
            flash(f'Gagal memproses data: {e}', 'danger')
            print(f"Error processing data: {e}")
            
    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    
    template_to_render = 'default_type.html'
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    if chiller_details and chiller_details.get('chiller_type'):
        chiller_type = chiller_details['chiller_type'].lower()
        specific_template = f"{chiller_type}_type.html"
        if os.path.exists(os.path.join(app.template_folder, specific_template)):
            template_to_render = specific_template
            if chiller_type == 'btpn':
                chart_parameters = [
                    { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
                    { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
                    { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
                    { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
                    { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
                    { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
                    { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
                    { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
                    { "key": "fla", "label": "FLA", "unit": "%" },
                    { "key": "VSD_Input_Power", "label": "Input Power", "unit": "kW" },
                    { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
                    { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
                    { "key": "efficiency", "label": "efficiency", "unit": "STD" }
                ]
        else:
            print(f"Warning: Template {specific_template} not found. Falling back to default_type.html.")

    safe_ranges = {
        "evap_lwt": {"min": 5.5, "max": 8.8}, "evap_rwt": {"min": 11.11, "max": 14.44},
        "evap_satur_temp": {"min": 3.33, "max": 6.67}, "cond_lwt": {"min": 32.22, "max": 35.55},
        "cond_rwt": {"min": 26.67, "max": 30.0}, "cond_satur_temp": {"min": 32.22, "max": 40.56},
        "oil_sump_temp": {"min": 40.56, "max": 53.89}, "discharge_temp": {"min": 40.56, "max": 53.89},
    }

    return render_template(
        template_to_render, 
        active_page='chiller_monitor', 
        current_time=current_time, 
        chiller=chiller_details,
        data=latest_chiller_data,
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date,
        last_updated_timestamp=last_updated_timestamp,
        chart_parameters=chart_parameters,
        safe_ranges=safe_ranges
    )

# Rute untuk halaman debug data
@app.route('/data_table')
def data_table():
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses halaman ini.', 'warning')
        return redirect(url_for('auth.login'))

    chiller_ids = ["bxc2_sqc_1", "bxc2_sqc_2", "bxc2_sqc_3", "bxc2_sqc_4","menara_btpn_1", "menara_btpn_2", "menara_btpn_3", "menara_btpn_4"]
    selected_chiller_id = request.args.get('chiller_id', chiller_ids[0] if chiller_ids else None)
    
    now = datetime.now()
    start_date = request.args.get('start_date')
    if not start_date:
        start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
        
    end_date = request.args.get('end_date')
    if not end_date:
        end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')

    data = []
    if selected_chiller_id:
        try:
            params = {}
            if start_date:
                params['start_date'] = datetime.fromisoformat(start_date).strftime('%Y-%m-%dT%H:%M:%S')
            if end_date:
                params['end_date'] = datetime.fromisoformat(end_date).strftime('%Y-%m-%dT%H:%M:%S')
            
            api_url = f'http://127.0.0.1:8000/chillers/{selected_chiller_id}/history'
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            # Lakukan penerjemahan kode di sini
            data = translate_codes(data)

        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 404:
                flash(f'Tidak ada data historis ditemukan untuk chiller {selected_chiller_id} pada rentang waktu yang dipilih.', 'info')
            else:
                flash(f'Gagal mengambil data dari API: {e}', 'danger')
                print(f"Error fetching data from API: {e}")
            
    return render_template('data_table.html', 
                            data=data, 
                            chiller_ids=chiller_ids, 
                            selected_chiller_id=selected_chiller_id,
                            start_date=start_date,
                            end_date=end_date)


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


@app.route('/customer_on_call')
def customer_on_call():
    if 'logged_in' not in session or not session['logged_in']:
        flash('Silakan login untuk mengakses halaman ini.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('customer_on_call.html')



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
            cursor.execute("SELECT id, nama, email, role FROM users WHERE id = %s", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                flash('Pengguna tidak ditemukan.', 'danger')
                return redirect(url_for('manage_users'))

            cursor.execute("SELECT id, name AS nama_site FROM sites")
            all_sites = cursor.fetchall()

            cursor.execute("SELECT site_id FROM user_site_access WHERE user_id = %s", (user_id,))
            assigned_site_ids = [row['site_id'] for row in cursor.fetchall()]

            if request.method == 'POST':
                selected_site_ids = request.form.getlist('sites')
                
                cursor.execute("DELETE FROM user_site_access WHERE user_id = %s", (user_id,))
                
                for site_id in selected_site_ids:
                    cursor.execute("INSERT INTO user_site_access (user_id, site_id) VALUES (%s, %s)", (user_id, site_id))
                
                conn.commit()
                flash(f'Akses site untuk {user_info["nama"]} berhasil diperbarui.', 'success')
                return redirect(url_for('manage_users'))

        except mysql.connector.Error as err:
            flash(f"Error saat mengelola akses pengguna: {err}", 'danger')
            print(f"Error saat mengelola akses pengguna: {err}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        return redirect(url_for('manage_users'))

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('manage_user_access.html',
                           current_time=current_time,
                           user_info=user_info,
                           all_sites=all_sites,
                           assigned_site_ids=assigned_site_ids)


@app.route('/user_add_account', methods=['GET', 'POST'])
def user_add_account():
    if not is_regular_user():
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    assigned_sites_for_creator = []
    current_user_id = session.get('user_id')

    if conn and current_user_id:
        cursor = conn.cursor(dictionary=True)
        try:
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
                selected_site_id = request.form.get('site_id')

                if not nama or not email or not password or not jabatan or not selected_site_id:
                    flash('Semua kolom harus diisi.', 'danger')
                    return render_template('user_add_account.html', current_time=datetime.now().strftime("%A, %d %B %Y, %H:%M:%S"), assigned_sites=assigned_sites_for_creator)

                allowed_site_ids = [s['id'] for s in assigned_sites_for_creator]
                if selected_site_id not in allowed_site_ids:
                    flash('Site yang dipilih tidak valid atau Anda tidak memiliki akses ke site tersebut.', 'danger')
                    return render_template('user_add_account.html', current_time=datetime.now().strftime("%A, %d %B %Y, %H:%M:%S"), assigned_sites=assigned_sites_for_creator)

                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash('Email sudah terdaftar. Silakan gunakan email lain.', 'danger')
                else:
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    
                    cursor.execute(
                        "INSERT INTO users (nama, email, jabatan, password, role) VALUES (%s, %s, %s, %s, %s)",
                        (nama, email, jabatan, hashed_password, 'User')
                    )
                    new_user_id = cursor.lastrowid
                    
                    cursor.execute("INSERT INTO user_site_access (user_id, site_id) VALUES (%s, %s)", (new_user_id, selected_site_id))
                    
                    conn.commit()
                    flash('Akun baru berhasil ditambahkan dan ditetapkan ke site yang dipilih!', 'success')
                    return redirect(url_for('user_add_account'))

        except mysql.connector.Error as err:
            flash(f"Error saat menambah akun: {err}", 'danger')
            print(f"Error saat menambah akun: {err}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    else:
        flash('Terjadi masalah saat memuat data site. Silakan coba lagi.', 'danger')
        return redirect(url_for('index'))

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('user_add_account.html', current_time=current_time, assigned_sites=assigned_sites_for_creator)


@app.route('/add_user_by_admin', methods=['GET', 'POST'])
def add_user_by_admin():
    if not is_admin():
        flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    all_sites = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name AS nama_site FROM sites")
            all_sites = cursor.fetchall()

            if request.method == 'POST':
                nama = request.form.get('nama')
                email = request.form.get('email')
                jabatan = request.form.get('jabatan')
                password = request.form.get('password')
                role = request.form.get('role')
                selected_site_ids = request.form.getlist('sites')

                if not nama or not email or not password or not jabatan or not role:
                    flash('Semua kolom wajib diisi.', 'danger')
                    return render_template('add_user_by_admin.html', current_time=datetime.now().strftime("%A, %d %B %Y, %H:%M:%S"), all_sites=all_sites)

                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                if existing_user:
                    flash('Email sudah terdaftar. Silakan gunakan email lain.', 'danger')
                else:
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                    
                    cursor.execute(
                        "INSERT INTO users (nama, email, jabatan, password, role) VALUES (%s, %s, %s, %s, %s)",
                        (nama, email, jabatan, hashed_password, role)
                    )
                    new_user_id = cursor.lastrowid

                    if role in ['Viewer', 'User']:
                        for site_id in selected_site_ids:
                            cursor.execute("INSERT INTO user_site_access (user_id, site_id) VALUES (%s, %s)", (new_user_id, site_id))
                    
                    conn.commit()
                    flash(f'Pengguna {nama} ({role}) berhasil ditambahkan!', 'success')
                    return redirect(url_for('manage_users'))

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


@app.route('/add_site', methods=['POST'])
def add_site():
    if not is_admin():
        flash('Anda tidak memiliki izin untuk melakukan aksi ini.', 'danger')
        return redirect(url_for('select_site'))

    site_id = request.form.get('site_id')
    site_name = request.form.get('site_name')
    location = request.form.get('location')
    description = request.form.get('description')
    
    if not site_id or not site_name or not location:
        flash('Site ID, Nama Site, dan Lokasi harus diisi.', 'danger')
        return redirect(url_for('select_site'))

    image_filename = 'default_site.jpg'  # Default image
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            image_filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.static_folder, 'images', image_filename)
            try:
                image_file.save(save_path)
            except Exception as e:
                flash(f"Gagal menyimpan file gambar: {e}", 'danger')
                return redirect(url_for('select_site'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM sites WHERE id = %s", (site_id,))
            if cursor.fetchone():
                flash(f'Site ID "{site_id}" sudah ada. Harap gunakan ID lain.', 'danger')
                return redirect(url_for('select_site'))

            # Asumsi kolom 'description' ada di tabel. Jika tidak, akan ada error.
            cursor.execute(
                "INSERT INTO sites (id, name, location, description, image_name) VALUES (%s, %s, %s, %s, %s)",
                (site_id, site_name, location, description, image_filename)
            )
            conn.commit()
            flash(f'Site "{site_name}" berhasil ditambahkan.', 'success')
        except mysql.connector.Error as err:
            if err.errno == 1054: # ER_BAD_FIELD_ERROR for unknown column
                flash('Error: Kolom "description" tidak ada di tabel `sites`. Mohon update skema database.', 'danger')
            else:
                flash(f"Error saat menambahkan site: {err}", 'danger')
            print(f"Error saat menambahkan site: {err}")
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return redirect(url_for('select_site'))


@app.route('/add_chiller/<string:site_id>', methods=['POST'])
def add_chiller(site_id):
    if not is_admin():
        flash('Anda tidak memiliki izin untuk melakukan aksi ini.', 'danger')
        return redirect(url_for('select_chiller', site_id=site_id))

    chiller_id = request.form.get('chiller_id')
    chiller_num = request.form.get('chiller_num')
    serial_number = request.form.get('serial_number')
    model_number = request.form.get('model_number')
    power_kW = request.form.get('power_kW')
    ton_of_refrigeration = request.form.get('ton_of_refrigeration')
    chiller_type = request.form.get('chiller_type')

    if not chiller_id or not chiller_num:
        flash('ID Chiller dan Nomor Chiller harus diisi.', 'danger')
        return redirect(url_for('select_chiller', site_id=site_id))

    image_filename = 'chiller.png' # Default image
    if 'image' in request.files:
        image_file = request.files['image']
        if image_file.filename != '':
            image_filename = secure_filename(image_file.filename)
            save_path = os.path.join(app.static_folder, 'images', image_filename)
            try:
                image_file.save(save_path)
            except Exception as e:
                flash(f"Gagal menyimpan file gambar: {e}", 'danger')
                return redirect(url_for('select_chiller', site_id=site_id))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Check if chiller ID already exists for this site
            cursor.execute("SELECT id FROM chillers WHERE id = %s AND site_id = %s", (chiller_id, site_id))
            if cursor.fetchone():
                flash(f'Chiller ID "{chiller_id}" sudah ada untuk site ini. Harap gunakan ID lain.', 'danger')
                return redirect(url_for('select_chiller', site_id=site_id))

            cursor.execute(
                "INSERT INTO chillers (id, site_id, chiller_num, serial_number, model_number, power_kW, ton_of_refrigeration, image_name, chiller_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (chiller_id, site_id, chiller_num, serial_number, model_number, power_kW, ton_of_refrigeration, image_filename, chiller_type)
            )
            conn.commit()
            flash(f'Chiller "{chiller_num}" berhasil ditambahkan.', 'success')
        except mysql.connector.Error as err:
            flash(f"Error saat menambahkan chiller: {err}", 'danger')
            print(f"Error saat menambahkan chiller: {err}")
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return redirect(url_for('select_chiller', site_id=site_id))

# Route untuk halaman edit chiller
@app.route('/edit_chiller/<string:chiller_id>', methods=['GET', 'POST'])
def edit_chiller(chiller_id):
    if not is_admin():
        flash('Anda tidak memiliki izin untuk melakukan aksi ini.', 'danger')
        return redirect(url_for('select_chiller', site_id=session.get('current_site_id')))

    conn = get_db_connection()
    chiller_data = None
    site_id = session.get('current_site_id')

    if not conn:
        return redirect(url_for('select_chiller', site_id=site_id))

    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            # Handle the POST request for updating the chiller
            chiller_num = request.form.get('chiller_num')
            serial_number = request.form.get('serial_number')
            model_number = request.form.get('model_number')
            power_kW = request.form.get('power_kW')
            ton_of_refrigeration = request.form.get('ton_of_refrigeration')
            chiller_type = request.form.get('chiller_type')

            # Get current image name before updating
            cursor.execute("SELECT image_name FROM chillers WHERE id = %s", (chiller_id,))
            current_chiller = cursor.fetchone()
            image_filename = current_chiller['image_name']

            # Handle file upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename != '':
                    # Delete old image if it's not the default one
                    if image_filename and image_filename != 'chiller.png':
                        old_image_path = os.path.join(app.static_folder, 'images', image_filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)

                    image_filename = secure_filename(image_file.filename)
                    save_path = os.path.join(app.static_folder, 'images', image_filename)
                    image_file.save(save_path)

            cursor.execute(
                """
                UPDATE chillers SET chiller_num = %s, serial_number = %s, model_number = %s,
                power_kW = %s, ton_of_refrigeration = %s, image_name = %s, chiller_type = %s
                WHERE id = %s
                """,
                (chiller_num, serial_number, model_number, power_kW, ton_of_refrigeration, image_filename, chiller_type, chiller_id)
            )
            conn.commit()
            flash(f'Chiller "{chiller_num}" berhasil diperbarui.', 'success')
            return redirect(url_for('select_chiller', site_id=site_id))
        
        else:
            # Handle the GET request to display the edit form
            cursor.execute("SELECT * FROM chillers WHERE id = %s", (chiller_id,))
            chiller_data = cursor.fetchone()
            if not chiller_data:
                flash('Chiller tidak ditemukan.', 'danger')
                return redirect(url_for('select_chiller', site_id=site_id))

    except mysql.connector.Error as err:
        flash(f"Error saat mengedit chiller: {err}", 'danger')
        print(f"Error saat mengedit chiller: {err}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    current_time = datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    return render_template('edit_chiller.html', current_time=current_time, chiller=chiller_data, site_id=site_id)


# Route untuk menghapus chiller
@app.route('/delete_chiller/<string:chiller_id>', methods=['POST'])
def delete_chiller(chiller_id):
    if not is_admin():
        flash('Anda tidak memiliki izin untuk melakukan aksi ini.', 'danger')
        return redirect(url_for('select_chiller', site_id=session.get('current_site_id')))

    site_id = session.get('current_site_id')
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get image name before deleting
            cursor.execute("SELECT image_name FROM chillers WHERE id = %s", (chiller_id,))
            chiller = cursor.fetchone()
            if chiller and chiller['image_name'] and chiller['image_name'] != 'chiller.png':
                image_path = os.path.join(app.static_folder, 'images', chiller['image_name'])
                if os.path.exists(image_path):
                    os.remove(image_path)

            # Delete the chiller and its data from the database
            cursor.execute("DELETE FROM chiller_datas WHERE chiller_id = %s", (chiller_id,))
            cursor.execute("DELETE FROM chillers WHERE id = %s", (chiller_id,))
            conn.commit()
            flash('Chiller berhasil dihapus.', 'success')
        except mysql.connector.Error as err:
            flash(f"Error saat menghapus chiller: {err}", 'danger')
            conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return redirect(url_for('select_chiller', site_id=site_id))


@app.route('/edit_site/<string:site_id>', methods=['POST'])
def edit_site(site_id):
    if not is_admin():
        flash('Anda tidak memiliki izin untuk melakukan aksi ini.', 'danger')
        return redirect(url_for('select_site'))

    site_name = request.form.get('site_name')
    location = request.form.get('location')
    description = request.form.get('description')

    if not site_name or not location:
        flash('Nama site dan lokasi harus diisi.', 'danger')
        return redirect(url_for('select_site'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get current image name
            cursor.execute("SELECT image_name FROM sites WHERE id = %s", (site_id,))
            current_site = cursor.fetchone()
            if not current_site:
                flash('Site tidak ditemukan.', 'danger')
                return redirect(url_for('select_site'))
            
            image_filename = current_site['image_name']

            # Handle file upload
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename != '':
                    # Delete old image if it's not the default one
                    if image_filename and image_filename != 'default_site.jpg':
                        old_image_path = os.path.join(app.static_folder, 'images', image_filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)

                    image_filename = secure_filename(image_file.filename)
                    save_path = os.path.join(app.static_folder, 'images', image_filename)
                    image_file.save(save_path)

            # Update database
            cursor.execute(
                "UPDATE sites SET name = %s, location = %s, description = %s, image_name = %s WHERE id = %s",
                (site_name, location, description, image_filename, site_id)
            )
            conn.commit()
            flash(f'Site "{site_name}" berhasil diperbarui.', 'success')

        except mysql.connector.Error as err:
            flash(f"Error saat memperbarui site: {err}", 'danger')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('select_site'))


@app.route('/delete_site/<string:site_id>', methods=['POST'])
def delete_site(site_id):
    if not is_admin():
        flash('Anda tidak memiliki izin untuk melakukan aksi ini.', 'danger')
        return redirect(url_for('select_site'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get image name before deleting
            cursor.execute("SELECT image_name FROM sites WHERE id = %s", (site_id,))
            site = cursor.fetchone()
            if site and site['image_name'] and site['image_name'] != 'default_site.jpg':
                image_path = os.path.join(app.static_folder, 'images', site['image_name'])
                if os.path.exists(image_path):
                    os.remove(image_path)

            # Delete the site from DB
            cursor.execute("DELETE FROM sites WHERE id = %s", (site_id,))
            conn.commit()
            flash('Site berhasil dihapus.', 'success')
        except mysql.connector.Error as err:
            flash(f"Error saat menghapus site: {err}", 'danger')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('select_site'))

def inject_sites_for_nav():
    conn = get_db_connection()
    sites_with_status = []
    if not conn:
        return dict(all_sites_for_nav=sites_with_status)

    try:
        cursor = conn.cursor(dictionary=True)
        
        user_role = session.get('role')
        user_id = session.get('user_id')
        sites = []

        if user_role in ['Admin', 'Viewer']:
            cursor.execute("SELECT id, name FROM sites ORDER BY name")
        elif user_id:
            cursor.execute("""
                SELECT s.id, s.name
                FROM sites s
                JOIN user_site_access usa ON s.id = usa.site_id
                WHERE usa.user_id = %s
                ORDER BY s.name
            """, (user_id,))
        else:
            return dict(all_sites_for_nav=[])

        sites = cursor.fetchall()

        for site in sites:
            cursor.execute("SELECT id FROM chillers WHERE site_id = %s", (site['id'],))
            chillers_in_site = cursor.fetchall()
            chiller_ids = [chiller['id'] for chiller in chillers_in_site]

            site['alarm_status'] = 'none'
            site['alarms'] = []

            if chiller_ids:
                chiller_placeholders = ', '.join(['%s'] * len(chiller_ids))
                
                query_latest_data = f"""
                    SELECT cd.chiller_id, c.chiller_num, cd.safety_fault, cd.warning_fault, cd.cycling_fault
                    FROM chiller_datas cd
                    JOIN chillers c ON c.id = cd.chiller_id
                    INNER JOIN (
                        SELECT chiller_id, MAX(timestamp) as max_ts
                        FROM chiller_datas
                        WHERE chiller_id IN ({chiller_placeholders})
                        GROUP BY chiller_id
                    ) as latest ON cd.chiller_id = latest.chiller_id AND cd.timestamp = latest.max_ts
                """
                cursor.execute(query_latest_data, tuple(chiller_ids))
                faults_data = cursor.fetchall()

                active_alarms = []
                has_safety = False
                has_warning_or_cycling = False

                for fault in faults_data:
                    chiller_num_display = fault.get('chiller_num', '')
                    if fault['safety_fault'] and fault['safety_fault'] > 0:
                        has_safety = True
                        description = safety_codes.get(fault['safety_fault'], "Unknown Safety Fault")
                        active_alarms.append({'type': 'safety', 'description': description, 'chiller_num': chiller_num_display})
                    
                    if fault['warning_fault'] and fault['warning_fault'] > 0:
                        has_warning_or_cycling = True
                        description = warning_codes.get(fault['warning_fault'], "Unknown Warning Fault")
                        active_alarms.append({'type': 'warning', 'description': description, 'chiller_num': chiller_num_display})

                    if fault['cycling_fault'] and fault['cycling_fault'] > 0:
                        has_warning_or_cycling = True
                        description = cycling_codes.get(fault['cycling_fault'], "Unknown Cycling Fault")
                        active_alarms.append({'type': 'warning', 'description': description, 'chiller_num': chiller_num_display})

                if has_safety:
                    site['alarm_status'] = 'safety'
                elif has_warning_or_cycling:
                    site['alarm_status'] = 'warning'
                
                site['alarms'] = active_alarms
            
            sites_with_status.append(site)

    except Exception as e:
        print(f"Error injecting sites for nav: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
    return dict(all_sites_for_nav=sites_with_status)


def celsius_to_fahrenheit(celsius):
    """Converts Celsius to Fahrenheit."""
    if celsius is None:
        return None
    return (celsius * 9/5) + 32

@app.route('/report/pdf/<string:chiller_id>', methods=['GET', 'POST'])
def report_pdf(chiller_id):
    """
    Menghasilkan laporan PDF untuk chiller.
    """
    if 'logged_in' not in session:
        flash('Anda harus login untuk mengakses laporan.', 'warning')
        return redirect(url_for('auth.login'))

    notes = {}
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('notes_'):
                notes[key[6:]] = value
        unit = request.form.get('unit', 'celsius')
    else:
        unit = request.args.get('unit', 'celsius')

    conn = get_db_connection()
    if not conn:
        flash("Tidak dapat terhubung ke database.", "danger")
        return redirect(url_for('index'))

    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM chillers WHERE id = %s", (chiller_id,))
        chiller_details = cursor.fetchone()
        
        if not chiller_details:
            flash("Chiller tidak ditemukan.", "danger")
            return redirect(url_for('index'))
            
        site_id = chiller_details['site_id']
        user_id = session.get('user_id')
        user_role = session.get('role')

        if user_role not in ['Admin', 'Viewer']:
            cursor.execute("SELECT user_id FROM user_site_access WHERE user_id = %s AND site_id = %s", (user_id, site_id))
            if not cursor.fetchone():
                flash("Anda tidak memiliki izin untuk mengakses laporan chiller ini.", "danger")
                return redirect(url_for('select_site'))

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        now = datetime.now()
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else now - timedelta(hours=12)
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else now

        historical_data = []
        try:
            params = {
                'start_date': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                'end_date': end_date.strftime('%Y-%m-%dT%H:%M:%S')
            }
            api_url = f'http://127.0.0.1:8000/chillers/{chiller_id}/history'
            response_history = requests.get(api_url, params=params)
            response_history.raise_for_status()
            historical_data = response_history.json()
        except requests.exceptions.RequestException as e:
            print(f"Permintaan API gagal: {e}")
            flash(f'Gagal mengambil data dari API untuk laporan: {e}', 'danger')
            return redirect(url_for('test', chiller_id=chiller_id))

        if not historical_data:
            flash('Tidak ada data historis untuk periode yang dipilih.', 'warning')
            return redirect(url_for('test', chiller_id=chiller_id, start_date=start_date.strftime('%Y-%m-%dT%H:%M'), end_date=end_date.strftime('%Y-%m-%dT%H:%M')))

        interval_hours = request.args.get('interval', 1, type=int)
        if historical_data and interval_hours > 0:
            sampled_data = []
            last_timestamp = None
            
            historical_data.sort(key=lambda x: x['timestamp'])

            for data_point in historical_data:
                current_timestamp = datetime.fromisoformat(data_point['timestamp'])
                
                if last_timestamp is None or (current_timestamp - last_timestamp) >= timedelta(hours=interval_hours):
                    sampled_data.append(data_point)
                    last_timestamp = current_timestamp
            historical_data = sampled_data

        safe_ranges = {
            "evap_lwt": {"min": 5.5, "max": 8.8}, "evap_rwt": {"min": 11.11, "max": 14.44},
            "evap_satur_temp": {"min": 3.33, "max": 6.67}, "cond_lwt": {"min": 32.22, "max": 35.55},
            "cond_rwt": {"min": 26.67, "max": 30.0}, "cond_satur_temp": {"min": 32.22, "max": 40.56},
            "oil_sump_temp": {"min": 40.56, "max": 53.89}, "discharge_temp": {"min": 40.56, "max": 53.89},
        }
        chart_sections = {
            "Evaporator": [{"key": "evap_lwt", "label": "Evap LWT (°C)"}, {"key": "evap_rwt", "label": "Evap RWT (°C)"}, {"key": "evap_pressure", "label": "Evap Pressure (kPa)"}, {"key": "evap_satur_temp", "label": "Evap Sat. Temp (°C)"}],
            "Condenser": [{"key": "cond_lwt", "label": "Cond LWT (°C)"}, {"key": "cond_rwt", "label": "Cond RWT (°C)"}, {"key": "cond_pressure", "label": "Cond Pressure (kPa)"}, {"key": "cond_satur_temp", "label": "Cond Sat. Temp (°C)"}],
            "Oil & Discharge": [{"key": "oil_sump_temp", "label": "Oil Sump Temp (°C)"}, {"key": "discharge_temp", "label": "Discharge Temp (°C)"}],
            "Power": [{"key": "fla", "label": "FLA (%)"}, {"key": "input_power", "label": "Input Power (kW)"}, {"key": "VSD_Input_Power", "label": "Input Power (kW)"}]
        }

        if unit == 'fahrenheit':
            temp_keys_to_convert = []
            for section in chart_sections.values():
                for param in section:
                    if "(°C)" in param['label']:
                        temp_keys_to_convert.append(param['key'])
                        param['label'] = param['label'].replace('°C', '°F')

            for d in historical_data:
                for key in temp_keys_to_convert:
                    if key in d and d[key] is not None:
                        d[key] = celsius_to_fahrenheit(d[key])
            
            for key in temp_keys_to_convert:
                if key in safe_ranges:
                    safe_ranges[key]['min'] = celsius_to_fahrenheit(safe_ranges[key]['min'])
                    safe_ranges[key]['max'] = celsius_to_fahrenheit(safe_ranges[key]['max'])

        # --- Data "Customer On Call" (kosong) ---
        on_call_data = []
        # --- End ---

        generation_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        pdf = PDFWithMargins(generation_time=generation_time, with_template_background=True, header_align_left=False)
        pdf.set_auto_page_break(auto=True, margin=25)

        # Halaman Judul
        pdf.add_page()
        title_image_path = os.path.join(app.static_folder, 'images', 'judul.png')
        if os.path.exists(title_image_path):
            pdf.image(title_image_path, x=0, y=0, w=pdf.w, h=pdf.h)

        # Tambahkan judul laporan di kiri bawah
        site_name = session.get('current_site_name', 'Unknown Site')
        month_map = {
            1: "JANUARI", 2: "FEBRUARI", 3: "MARET", 4: "APRIL", 5: "MEI", 6: "JUNI",
            7: "JULI", 8: "AGUSTUS", 9: "SEPTEMBER", 10: "OKTOBER", 11: "NOVEMBER", 12: "DESEMBER"
        }
        bulan_awal = month_map.get(start_date.month, "")
        tahun_awal = start_date.year
        bulan_akhir = month_map.get(end_date.month, "")
        tahun_akhir = end_date.year

        if bulan_awal == bulan_akhir and tahun_awal == tahun_akhir:
            periode = f"{bulan_awal} {tahun_awal}"
        elif tahun_awal != tahun_akhir:
            periode = f"{bulan_awal} {tahun_awal} - {bulan_akhir} {tahun_akhir}"
        else:
            periode = f"{bulan_awal} - {bulan_akhir} {tahun_awal}"

        line1 = "LAPORAN PEMELIHARAAN"
        line2 = f"{site_name.upper()} "
        line3 = f"PERIODE {periode}"

        pdf.set_y(-95) # 80 mm from bottom

        # Line 1
        pdf.set_font('helvetica', 'B', 28) # Bigger font
        pdf.cell(0, 10, line1, 0, 1, 'L') # ln=1 to move to next line, align Left

        # Line 2
        pdf.set_font('helvetica', 'B', 22) # Smaller font
        pdf.cell(0, 10, line2, 0, 1, 'L')

        # Line 3
        pdf.set_font('helvetica', 'B', 22)
        pdf.cell(0, 10, line3, 0, 0, 'L')

        # Halaman Surat
        pdf.add_page()
        pdf.set_font('helvetica', '', 12)
        
        pdf.cell(0, 10, '[bulan tahun]', 0, 1, 'L')
        pdf.cell(0, 10, '[site]', 0, 1, 'L')
        pdf.ln(10)

        pdf.cell(0, 10, 'Dear Bapak [nama cus],', 0, 1, 'L')
        pdf.ln(5)

        body_text = """Terima kasih atas kepercayaannya menggunakan PT Jaya Teknik Indonesia Untuk melakukan pemeliharaan chiller di [site].

Bersama ini kami sampaikan review laporan bulanan untuk periode januari 2024. dalam laporan ini kami sampaikan rekomendasi dan hasil pemeliharaan chiller di [site].

Kami bersedia untuk melakukan diskusi lanjutan untuk membahas laporan ini sehingga kami bisa mensupport kegiatan bisnis di [site]."""
        pdf.multi_cell(0, 5, body_text)
        pdf.ln(10)

        pdf.cell(0, 10, 'Hormat Kami,', 0, 1, 'L')
        pdf.ln(15)

        signature_text = """Penanggung jawab
PT Jaya Teknik Indonesia
Service Manager /jabatan penanggung jawab
Arif.Imran@jayateknik.com / email
+62 83887"""
        pdf.multi_cell(0, 7, signature_text)

        # Halaman Konten Laporan - Chiller Details
        pdf.add_page()

        pdf.set_font('helvetica', 'B', 16)
        site_name = session.get('current_site_name', 'Unknown Site')
        chiller_name = chiller_details.get('chiller_num', chiller_id)
        pdf.cell(0, 10, f'Laporan Chiller - {site_name}', 0, 1, 'C')
        pdf.cell(0, 10, f'Chiller: {chiller_name}', 0, 1, 'C')
        pdf.ln(10)

        image_path = os.path.join(app.static_folder, 'images', 'chiller.png')
        if os.path.exists(image_path):
            pdf.image(image_path, x='C', y=pdf.get_y(), w=150)
            pdf.ln(85)

        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, 'Chiller Details', 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font('helvetica', '', 10)
        table_width = 150
        col_width_key = 60
        col_width_value = 90
        start_x = (pdf.w - table_width) / 2
        details_to_show = {
            "Model Number": chiller_details.get('model_number'), "Serial Number": chiller_details.get('serial_number'),
            "Refrigerant": chiller_details.get('refrigerant'), "net WT" : chiller_details.get('net_weight'),
            "Compressor Model": chiller_details.get('compressor_model'), "Charge": chiller_details.get('charge')
        }
        for key, value in details_to_show.items():
            pdf.set_x(start_x)
            pdf.cell(col_width_key, 10, f'{key}:', 1, 0)
            pdf.cell(col_width_value, 10, str(value), 1, 1)
        pdf.ln(10)

        # --- Penambahan Halaman Customer On Call ---
        pdf.add_page()

        # Header block yang lebih kecil dengan latar belakang biru
        block_height = 10
        block_width = 60
        pdf.set_fill_color(0, 123, 255)
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(block_width, block_height, 'Customer On Call', 0, 0, 'L', 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(block_height + 5)

        # Tentukan lebar kolom dan header
        headers = ['No.', 'Date', 'Problem Reported', 'Initiation', 'Call in\nTime', 'Time Taken to\nComplete', 'Action Complete', 'Downtime\n(hours)', 'Remarks']

        # Atur lebar kolom secara manual dalam mm. Total harus 190mm untuk A4 portrait (w=210, margin 10x2)
        col_widths = [10, 20, 35, 20, 20, 25, 25, 15, 20]

        # Cetak header tabel dengan gaya dari gambar
        pdf.set_font('helvetica', 'B', 7)
        pdf.set_fill_color(0, 86, 179)
        pdf.set_text_color(255, 255, 255)

        # Cetak setiap sel header
        current_y = pdf.get_y()
        current_x = pdf.get_x()

        for i, header in enumerate(headers):
            pdf.set_xy(current_x, current_y)
            # Draw background and border
            pdf.cell(col_widths[i], block_height, '', 1, 0, 'C', True)
            
            # Calculate y position for vertically centered text
            line_height = 4 
            num_lines = header.count('\n') + 1
            text_height = num_lines * line_height
            y_text = current_y + (block_height - text_height) / 2
            
            # Set position and draw multi-line text
            pdf.set_xy(current_x, y_text)
            pdf.multi_cell(col_widths[i], line_height, header, 0, 'C')
            
            # Move to next cell's x position for the next iteration
            current_x += col_widths[i]

        pdf.set_y(current_y + block_height)  # Move position down below the header

        # Cetak grid kosong untuk diisi manual
        pdf.set_text_color(0, 0, 0)
        row_height = 10
        for i in range(1, 11):
            fill_color = 240 if i % 2 == 0 else 255
            pdf.set_fill_color(fill_color, fill_color, fill_color)
            
            if pdf.get_y() + row_height > pdf.page_break_trigger:
                pdf.add_page()
                pdf.set_fill_color(0, 86, 179)
                pdf.set_text_color(255, 255, 255)
                current_y_new_page = pdf.get_y()
                current_x_new_page = pdf.get_x()
                for i_h, header_h in enumerate(headers):
                    pdf.set_xy(current_x_new_page, current_y_new_page)
                    pdf.cell(col_widths[i_h], block_height, header_h, 1, 'C', True)
                    current_x_new_page += col_widths[i_h]
                pdf.ln(block_height)
                pdf.set_text_color(0, 0, 0)
                pdf.set_fill_color(255, 255, 255)

            pdf.cell(col_widths[0], row_height, str(i), 1, 0, 'C', True)
            
            for col_width in col_widths[1:]:
                pdf.cell(col_width, row_height, '', 1, 0, 'C', True)
            pdf.ln()

        pdf.ln(10)
        # --- Penambahan Halaman Work Order ---
        pdf.add_page()

        # Header block untuk Work Order
        block_height = 10
        block_width = 60
        pdf.set_fill_color(0, 123, 255)
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(block_width, block_height, 'Work Order', 0, 0, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(block_height + 5)

        # Konten teks Work Order
        pdf.set_font('helvetica', '', 10)
        work_order_text = f"""Pada bagian ini kami menyampaikan list work order terhadap chiller di {site_name}, high priority work order adalah work order yang kami sarankan untuk segera dilakukan untuk mencegah kerusakan lebih lanjut. Open work order adalah work order yang perlu dilakukan action sehingga bisa closed. Closed work order adalah list work order yang telah dilakukan sehingga bisa dilakukan analisa terhadap chiller tersebut"""
        pdf.multi_cell(0, 5, work_order_text)
        pdf.ln(10)
        # --- Penambahan High Priority WO ---

        # Header block untuk High Priority WO
        block_height = 10
        block_width = 60
        pdf.set_fill_color(255, 0, 0) # Red color
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(block_width, block_height, 'High Priority WO', 0, 0, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(block_height + 5)

        # Tabel High Priority WO
        wo_headers = ['WO NUMBER', 'DATE CREATED', 'DESCRIPTION', 'COMMENTS']
        wo_col_widths = [30, 30, 80, 50] # Total 190mm

        # Cetak header tabel
        pdf.set_font('helvetica', 'B', 7)
        pdf.set_fill_color(0, 123, 255) # Red background for header
        pdf.set_text_color(255, 255, 255)

        current_y = pdf.get_y()
        current_x = pdf.get_x()

        for i, header in enumerate(wo_headers):
            pdf.set_xy(current_x, current_y)
            # Draw background and border
            pdf.cell(wo_col_widths[i], block_height, '', 1, 0, 'C', True)
            
            # Calculate y position for vertically centered text
            line_height = 4 
            num_lines = header.count('\n') + 1
            text_height = num_lines * line_height
            y_text = current_y + (block_height - text_height) / 2
            
            # Set position and draw multi-line text
            pdf.set_xy(current_x, y_text)
            pdf.multi_cell(wo_col_widths[i], line_height, header, 0, 'C')
            
            # Move to next cell's x position
            current_x += wo_col_widths[i]

        pdf.set_y(current_y + block_height) # Move position down below the header

        # Cetak grid kosong untuk diisi manual (contoh 3 baris)
        pdf.set_text_color(0, 0, 0)
        row_height = 10
        for i in range(3): # Example 3 empty rows
            fill_color = 240 if i % 2 == 0 else 255
            pdf.set_fill_color(fill_color, fill_color, fill_color)
            
            if pdf.get_y() + row_height > pdf.page_break_trigger:
                pdf.add_page()
                # Re-print header on new page if it breaks
                pdf.set_font('helvetica', 'B', 7)
                pdf.set_fill_color(255, 0, 0)
                pdf.set_text_color(255, 255, 255)
                current_y_new_page = pdf.get_y()
                current_x_new_page = pdf.get_x()
                for i_h, header_h in enumerate(wo_headers):
                    pdf.set_xy(current_x_new_page, current_y_new_page)
                    pdf.cell(wo_col_widths[i_h], block_height, '', 1, 0, 'C', True)
                    pdf.set_xy(current_x_new_page, current_y_new_page + (block_height - (header_h.count('\n') + 1) * line_height) / 2)
                    pdf.multi_cell(wo_col_widths[i_h], line_height, header_h, 0, 'C')
                    current_x_new_page += wo_col_widths[i_h]
                pdf.set_y(current_y_new_page + block_height)
                pdf.set_text_color(0, 0, 0)
                pdf.set_fill_color(255, 255, 255)

            for col_width in wo_col_widths:
                pdf.cell(col_width, row_height, '', 1, 0, 'C', True)
            pdf.ln()
        pdf.ln(10)
        # --- Penambahan Open Work Order ---

        # Header block untuk Open Work Order
        block_height = 10
        block_width = 60
        pdf.set_fill_color(0, 123, 255) # Blue color
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(block_width, block_height, 'Open Work Order', 0, 0, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(block_height + 5)

        # Tabel Open Work Order
        wo_headers = ['No', 'WO NUMBER', 'DATE CREATED', 'DESCRIPTION', 'COMMENTS']
        wo_col_widths = [10, 30, 30, 80, 40] # Total 190mm

        # Cetak header tabel
        pdf.set_font('helvetica', 'B', 7)
        pdf.set_fill_color(0, 123, 255) # Blue background for header
        pdf.set_text_color(255, 255, 255)

        current_y = pdf.get_y()
        current_x = pdf.get_x()

        for i, header in enumerate(wo_headers):
            pdf.set_xy(current_x, current_y)
            # Draw background and border
            pdf.cell(wo_col_widths[i], block_height, '', 1, 0, 'C', True)
            
            # Calculate y position for vertically centered text
            line_height = 4 
            num_lines = header.count('\n') + 1
            text_height = num_lines * line_height
            y_text = current_y + (block_height - text_height) / 2
            
            # Set position and draw multi-line text
            pdf.set_xy(current_x, y_text)
            pdf.multi_cell(wo_col_widths[i], line_height, header, 0, 'C')
            
            # Move to next cell's x position
            current_x += wo_col_widths[i]

        pdf.set_y(current_y + block_height) # Move position down below the header

        # Cetak grid kosong untuk diisi manual (contoh 3 baris)
        pdf.set_text_color(0, 0, 0)
        row_height = 10
        for i in range(3): # Example 3 empty rows
            fill_color = 240 if i % 2 == 0 else 255
            pdf.set_fill_color(fill_color, fill_color, fill_color)
            
            if pdf.get_y() + row_height > pdf.page_break_trigger:
                pdf.add_page()
                # Re-print header on new page if it breaks
                pdf.set_font('helvetica', 'B', 7)
                pdf.set_fill_color(0, 123, 255)
                pdf.set_text_color(255, 255, 255)
                current_y_new_page = pdf.get_y()
                current_x_new_page = pdf.get_x()
                for i_h, header_h in enumerate(wo_headers):
                    pdf.set_xy(current_x_new_page, current_y_new_page)
                    pdf.cell(wo_col_widths[i_h], block_height, '', 1, 0, 'C', True)
                    pdf.set_xy(current_x_new_page, current_y_new_page + (block_height - (header_h.count('\n') + 1) * line_height) / 2)
                    pdf.multi_cell(wo_col_widths[i_h], line_height, header_h, 0, 'C')
                    current_x_new_page += wo_col_widths[i_h]
                pdf.set_y(current_y_new_page + block_height)
                pdf.set_text_color(0, 0, 0)
                pdf.set_fill_color(255, 255, 255)

            for col_width in wo_col_widths:
                pdf.cell(col_width, row_height, '', 1, 0, 'C', True)
            pdf.ln()
        pdf.ln(10)
        # --- Akhir Penambahan Open Work Order ---

        # --- Penambahan Closed Work Order ---

        # Header block untuk Closed Work Order
        block_height = 10
        block_width = 60
        pdf.set_fill_color(0, 123, 255) # Blue color
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(block_width, block_height, 'Closed Work Order', 0, 0, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(block_height + 5)

        # Tabel Closed Work Order
        wo_headers = ['No', 'WO NUMBER', 'DATE CREATED', 'DATE CLOSED', 'DESCRIPTION', 'COMMENTS']
        wo_col_widths = [10, 30, 30, 30, 50, 40] # Total 190mm

        # Cetak header tabel
        pdf.set_font('helvetica', 'B', 7)
        pdf.set_fill_color(0, 123, 255) # Blue background for header
        pdf.set_text_color(255, 255, 255)

        current_y = pdf.get_y()
        current_x = pdf.get_x()

        for i, header in enumerate(wo_headers):
            pdf.set_xy(current_x, current_y)
            # Draw background and border
            pdf.cell(wo_col_widths[i], block_height, '', 1, 0, 'C', True)
            
            line_height = 4 
            num_lines = header.count('\n') + 1
            text_height = num_lines * line_height
            y_text = current_y + (block_height - text_height) / 2
            
            # Set position and draw multi-line text
            pdf.set_xy(current_x, y_text)
            pdf.multi_cell(wo_col_widths[i], line_height, header, 0, 'C')
            
            # Move to next cell's x position
            current_x += wo_col_widths[i]

        pdf.set_y(current_y + block_height) # Move position down below the header

        # Cetak grid kosong untuk diisi manual (contoh 3 baris)
        pdf.set_text_color(0, 0, 0)
        row_height = 10
        for i in range(3): # Example 3 empty rows
            fill_color = 240 if i % 2 == 0 else 255
            pdf.set_fill_color(fill_color, fill_color, fill_color)
            
            if pdf.get_y() + row_height > pdf.page_break_trigger:
                pdf.add_page()
                # Re-print header on new page if it breaks
                pdf.set_font('helvetica', 'B', 7)
                pdf.set_fill_color(0, 123, 255)
                pdf.set_text_color(255, 255, 255)
                current_y_new_page = pdf.get_y()
                current_x_new_page = pdf.get_x()
                for i_h, header_h in enumerate(wo_headers):
                    pdf.set_xy(current_x_new_page, current_y_new_page)
                    pdf.cell(wo_col_widths[i_h], block_height, '', 1, 0, 'C', True)
                    pdf.set_xy(current_x_new_page, current_y_new_page + (block_height - (header_h.count('\n') + 1) * line_height) / 2)
                    pdf.multi_cell(wo_col_widths[i_h], line_height, header_h, 0, 'C')
                    current_x_new_page += wo_col_widths[i_h]
                pdf.set_y(current_y_new_page + block_height)
                pdf.set_text_color(0, 0, 0)
                pdf.set_fill_color(255, 255, 255)

            for col_width in wo_col_widths:
                pdf.cell(col_width, row_height, '', 1, 0, 'C', True)
            pdf.ln()
        pdf.ln(10)
        # --- Akhir Penambahan Closed Work Order ---

        # --- Penambahan Halaman Chiller Overview ---
        pdf.add_page()
        # Header block untuk Chiller Overview
        block_height = 10
        block_width = 60
        pdf.set_fill_color(0, 123, 255) # Blue color
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        chiller_num = chiller_details.get('chiller_num', chiller_id)
        pdf.cell(block_width, block_height, f'Chiller {chiller_num} Overview', 0, 0, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(block_height + 5)

        image_path = os.path.join(app.static_folder, 'images', 'chiller_page.png')
        if os.path.exists(image_path):
            pdf.image(image_path, x='C', y=pdf.get_y(), w=150) # Adjust width as needed
            pdf.ln(85) # Adjust line break after image
        # --- Akhir Penambahan Halaman Chiller Overview ---
        pdf.ln(10)
        # --- Akhir Penambahan High Priority WO ---
        # --- Akhir Penambahan Halaman Work Order ---
# --- Akhir Penambahan Halaman Customer On Call ---


        timestamps = [datetime.fromisoformat(d['timestamp']) for d in historical_data]
        for section_title, parameters_in_section in chart_sections.items():
            if not any(p['key'] in historical_data[0] for p in parameters_in_section):
                continue
            pdf.add_page()
            pdf.set_font('helvetica', 'B', 14)
            pdf.cell(0, 9, section_title, 0, 1, 'L')
            pdf.ln(2)
            for param in parameters_in_section:
                if param['key'] in historical_data[0] and historical_data[0][param['key']] is not None:
                    values = [d.get(param['key']) for d in historical_data]
                    plot_data = [(t, v) for t, v in zip(timestamps, values) if v is not None]
                    if not plot_data: continue
                    plot_timestamps, plot_values = zip(*plot_data)
                    if pdf.get_y() + 90 > pdf.page_break_trigger:
                        pdf.add_page()
                        pdf.set_font('helvetica', 'B', 14)
                        pdf.cell(0, 10, section_title, 0, 1, 'L')
                        pdf.ln(2)
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(plot_timestamps, plot_values, marker='.', linestyle='-', markersize=8, zorder=2)
                    if param['key'] in safe_ranges:
                        s_range = safe_ranges[param['key']]
                        ax.axhspan(s_range['min'], s_range['max'], color='green', alpha=0.2, label='Safe Range', zorder=1)
                        ax.legend()
                    ax.set_title(param['label'], fontsize=14)
                    ax.set_xlabel('Waktu', fontsize=10)
                    ax.set_ylabel(param['label'].split(' ')[-1], fontsize=10)
                    ax.grid(True)
                    fig.autofmt_xdate()
                    plt.tight_layout()
                    img_buffer = BytesIO()
                    fig.savefig(img_buffer, format='png', dpi=100)
                    img_buffer.seek(0)
                    pdf.image(img_buffer, x=None, y=None, w=190)
                    plt.close(fig)
                    pdf.ln(2)
                    note = notes.get(param['key'], '').strip()
                    pdf.set_font('helvetica', 'B', 10)
                    pdf.cell(0, 5, 'NOTE:', 0, 1, 'L')
                    pdf.set_font('helvetica', '', 10)
                    if note:
                        pdf.multi_cell(0, 5, note)
                    else:
                        pdf.multi_cell(0, 5, '-')
                    pdf.ln(10)

        if historical_data:
            parameters_to_plot = []
            for section_params in chart_sections.values():
                parameters_to_plot.extend(section_params)
            valid_parameters = [p for p in parameters_to_plot if p['key'] in historical_data[0] and any(d.get(p['key']) is not None for d in historical_data)]
            data_points_per_table =9
            data_chunks = [historical_data[i:i + data_points_per_table] for i in range(0, len(historical_data), data_points_per_table)]
            header_height = 8
            row_height = 5
            table_height = header_height + (len(valid_parameters) * row_height) + 2
            pdf.add_page(orientation='L')
            pdf.set_font('helvetica', 'B', 12)
            pdf.cell(0, 10, 'Data Historis', 0, 1, 'L')
            is_first_table_on_page = True
            for table_data in data_chunks:
                if not is_first_table_on_page and (pdf.get_y() + table_height > pdf.page_break_trigger):
                    pdf.add_page(orientation='L')
                    pdf.set_font('helvetica', 'B', 12)
                    pdf.cell(0, 10, 'Data Historis (Lanjutan)', 0, 1, 'L')
                    is_first_table_on_page = True
                if not is_first_table_on_page:
                    pdf.ln(2)
                timestamps = [datetime.fromisoformat(d['timestamp']).strftime('%H:%M %d-%m-%y') for d in table_data]
                header_labels = ['Parameter', 'Safe Range'] + timestamps # Added 'Safe Range'
                
                param_col_width = 55
                safe_range_col_width = 30 # New column width
                num_data_cols = len(table_data)
                remaining_width = pdf.w - 20 - param_col_width - safe_range_col_width # Adjusted remaining width
                data_col_width = remaining_width / num_data_cols if num_data_cols > 0 else 0
                col_widths = [param_col_width, safe_range_col_width] + [data_col_width] * num_data_cols # Adjusted col_widths
                
                pdf.set_font('helvetica', 'B', 8)
                y_start = pdf.get_y()
                x_start = pdf.get_x()
                
                current_x_header = x_start
                for i, header_text in enumerate(header_labels): # Loop through all headers
                    pdf.set_xy(current_x_header, y_start)
                    # Draw background and border
                    pdf.cell(col_widths[i], header_height, '', 1, 0, 'C', True)
                    
                    # Calculate y position for vertically centered text
                    line_height = 4 
                    num_lines = header_text.count('\n') + 1
                    text_height = num_lines * line_height
                    y_text = y_start + (header_height - text_height) / 2
                    
                    # Set position and draw multi-line text
                    pdf.set_xy(current_x_header, y_text)
                    pdf.multi_cell(col_widths[i], line_height, header_text, 0, 'C')
                    
                    current_x_header += col_widths[i]
                
                pdf.set_y(y_start + header_height)
                pdf.set_font('helvetica', '', 9)
                for param_info in valid_parameters:
                    param_key = param_info['key']
                    param_label = param_info['label']
                    
                    # Print Parameter label
                    pdf.cell(col_widths[0], row_height, param_label, 1)
                    
                    # Print Safe Range
                    safe_range_str = '-'
                    if param_key in safe_ranges:
                        s_range = safe_ranges[param_key]
                        if s_range['min'] is not None and s_range['max'] is not None:
                            safe_range_str = f"{s_range['min']:.2f} - {s_range['max']:.2f}"
                        elif s_range['min'] is not None:
                            safe_range_str = f"> {s_range['min']:.2f}"
                        elif s_range['max'] is not None:
                            safe_range_str = f"< {s_range['max']:.2f}"
                    pdf.cell(col_widths[1], row_height, safe_range_str, 1, align='C') # col_widths[1] for safe range
                    
                    # Print data values
                    for data_point in table_data:
                        value = data_point.get(param_key)
                        if value is None:
                            display_value = '-'
                        elif isinstance(value, float):
                            display_value = f'{value:.2f}'
                        else:
                            display_value = str(value)
                        pdf.cell(data_col_width, row_height, display_value, 1, align='C')
                    pdf.ln()
                is_first_table_on_page = False

        # --- Penambahan Halaman Checklist ---
        pdf.add_page()
        # Header block untuk Checklist
        block_height = 10
        block_width = 60
        pdf.set_fill_color(0, 123, 255) # Blue color
        pdf.set_font('helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(block_width, block_height, 'Checklist', 0, 0, 'L', True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(block_height + 5)

        image_path = os.path.join(app.static_folder, 'images', 'floor_layout.png')
        if os.path.exists(image_path):
            pdf.image(image_path, x='C', y=pdf.get_y(), w=200) # Adjust width as needed
            pdf.ln(85) # Adjust line break after image
        # --- Akhir Penambahan Halaman Checklist ---
        # --- Tambahkan Tabel Checklist seperti di gambar ---
        pdf.ln(10)  # Spasi dari gambar sebelumnya
        
        # Header tabel
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_fill_color(0, 123, 255)
        pdf.set_text_color(255, 255, 255)

        header_widths = [10, 60, 40, 40, 40]
        header_texts = ['NO', 'Description', 'Range', 'Remarks', 'Note']

        for i, header_text in enumerate(header_texts):
            pdf.cell(header_widths[i], 10, header_text, 1, 0, 'C', True)
        pdf.ln()

        # Data untuk tabel dari gambar
        checklist_sections = [
            {'title': 'Evaporator', 'items': [
                ('LWT Sensor', ''),
                ('Cek Sensor', 'Baik / Tidak'),
                ('Cek Sensor Well', 'Baik / Tidak'),
                ('Cek Socket Sensor', 'Baik / Tidak'),
                ('RWT Sensor', ''),
                ('Cek Sensor', 'Baik / Tidak'),
                ('Cek Sensor Well', 'Baik / Tidak'),
                ('Cek Socket Sensor', 'Baik / Tidak'),
                ('Inlet Pressure Gauge', ''),
                ('Cek Pressure Gauge', 'Baik / Tidak'),
                ('Cek Pressure Gauge Valve', 'Baik / Tidak'),
                ('Cek Pressure Gauge Pipa', 'Baik / Tidak'),
                ('Outlet Pressure Gauge', ''),
                ('Cek Pressure Gauge', 'Baik / Tidak'),
                ('Cek Pressure Gauge Valve', 'Baik / Tidak'),
                ('Cek Pressure Gauge Pipa', 'Baik / Tidak'),
                ('Flow Switch', ''),
                ('Cek kondisi Flow Switch', 'Baik / Tidak'),
                ('Flow Meter', ''),
                ('Cek Kondisi Flow meter', 'Baik / Tidak'),
                ('Water box', ''),
                ('Cek Kondisi Water Box', 'Baik / Tidak'),
                ('Cek Kanal Gasket', 'Baik / Tidak'),
                ('Cek Kondisi Endsheet', 'Baik / Tidak'),
                ('Evaporator Pressure Transducer', ''),
                ('Cek Kondisi Transducer', 'Baik / Tidak'),
                ('Cek Kondisi Socket Transducer', 'Baik / Tidak'),
                ('Evap Refrigerant Temp Sensor', ''),
                ('Cek Sensor', 'Baik / Tidak'),
                ('Cek Sensor Well', 'Baik / Tidak'),
                ('Cek Socket Sensor', 'Baik / Tidak'),
                ('Sight Glass', ''),
                ('Cek Kondisi Sight Glass', 'Baik / Tidak'),
                ('Cek Kondisi Koneksi Sight Glass', 'Baik / Tidak'),
                ('Evaporator Body', ''),
                ('Cek Kondisi Insulasi', 'Baik / Tidak'),
                ('Cek visual dari kebocoran', 'Baik / Tidak'),
            ]},
            # Tambahkan section lain jika ada
        ]

        row_height = 8
        no_counter = 1
        
        pdf.set_font('helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)

        for section in checklist_sections:
            # Print the main section row
            pdf.set_font('helvetica', 'B', 10)
            pdf.cell(header_widths[0], row_height, str(no_counter), 1, 0, 'C')
            pdf.cell(header_widths[1], row_height, section['title'], 1, 0, 'L')
            pdf.cell(header_widths[2] + header_widths[3] + header_widths[4], row_height, '', 1, 1, 'L')
            pdf.set_font('helvetica', '', 10)
            
            no_counter += 1
            
            # Print the sub-items
            for i, (description, range_val) in enumerate(section['items']):
                # Check for page break
                if pdf.get_y() + row_height > pdf.page_break_trigger:
                    pdf.add_page()
                    # Re-print header on new page
                    pdf.set_font('helvetica', 'B', 12)
                    pdf.set_fill_color(0, 123, 255)
                    pdf.set_text_color(255, 255, 255)
                    for h_i, h_text in enumerate(header_texts):
                        pdf.cell(header_widths[h_i], 10, h_text, 1, 0, 'C', True)
                    pdf.ln()
                    pdf.set_font('helvetica', '', 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_fill_color(255, 255, 255)

                # Use bold font for sub-headers like "LWT Sensor"
                if range_val == '':
                    pdf.set_font('helvetica', 'B', 10)
                    pdf.set_fill_color(240, 240, 240)
                else:
                    pdf.set_font('helvetica', '', 10)
                    pdf.set_fill_color(255, 255, 255)

                pdf.cell(header_widths[0], row_height, '', 1, 0, 'C', True)
                pdf.cell(header_widths[1], row_height, description, 1, 0, 'L', True)
                pdf.cell(header_widths[2], row_height, range_val, 1, 0, 'C', True)
                pdf.cell(header_widths[3], row_height, '', 1, 0, 'C', True)
                pdf.cell(header_widths[4], row_height, '', 1, 1, 'C', True)

        # Baris "Recommendation"
        pdf.ln(2) # Spasi kecil
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(header_widths[0] + header_widths[1], row_height, 'Recommendation:', 1, 0, 'L')
        pdf.cell(header_widths[2] + header_widths[3] + header_widths[4], row_height, '', 1, 1, 'C')
        pdf.ln(5) # Spasi setelah tabel

        # --- Akhir Tabel Checklist ---

        pdf_output = bytes(pdf.output())
        return Response(pdf_output, mimetype='application/pdf', headers={'Content-Disposition': f'inline; filename=report_{chiller_id}_{start_date.strftime("%Y%m%d")}.pdf'})

    except Exception as e:
        import traceback
        print(f"An error occurred during PDF generation for chiller {chiller_id}:")
        traceback.print_exc()
        flash(f"Gagal membuat laporan PDF karena kesalahan internal: {e}", "danger")
        return redirect(url_for('test', chiller_id=chiller_id))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/yvaa_type')
def yvaa_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YVAA'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('yvaa_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)

@app.route('/yvwa1_type')
def yvwa1_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YVWA1'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('yvwa1_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)

@app.route('/yvwa2_type')
def yvwa2_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YVWA2'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('yvwa2_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)

@app.route('/ys_sss_type')
def ys_sss_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YS-SSS'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('ys-sss_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)

@app.route('/yr_sss_type')
def yr_sss_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YR-SSS'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('yr-sss_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)

@app.route('/ylaa_type')
def ylaa_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YLAA'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('ylaa_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)

@app.route('/yk_sss_type')
def yk_sss_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YK-SSS'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('yk-sss_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)

@app.route('/yk_vsd_type')
def yk_vsd_type():
    dummy_data = {
        'evap_rwt': 12.5, 'evap_lwt': 7.2, 'evap_pressure': 450.1, 'evap_satur_temp': 5.3,
        'cond_rwt': 29.8, 'cond_lwt': 35.1, 'cond_pressure': 1200.5, 'cond_satur_temp': 38.2,
        'oil_sump_temp': 55.6, 'oil_feed_pressure': 850.3, 'oil_feed_temp': 50.1,
        'compressor_starts': 1234, 'compressor_hours': 5678, 'fla': 85.2,
        'safety_fault_desc': 'No Safety Faults Present', 'cycling_fault_desc': 'No Cycling Faults Present', 'warning_fault_desc': 'No Warning Present'
    }
    dummy_chiller = {
        'id': 'dummy_chiller', 'chiller_num': 'Dummy Chiller', 'model_number': 'DUMMY-123',
        'serial_number': 'DUMMY-SN-456', 'power_kW': 500, 'ton_of_refrigeration': 150,
        'image_name': 'chiller.png', 'chiller_type': 'YK-VSD'
    }
    chart_parameters = [
        { "key": "evap_lwt", "label": "Evap LWT", "unit": "°C" },
        { "key": "evap_rwt", "label": "Evap RWT", "unit": "°C" },
        { "key": "evap_pressure", "label": "Evap Pressure", "unit": "kPa" },
        { "key": "evap_satur_temp", "label": "Evap Sat. Temp", "unit": "°C" },
        { "key": "cond_lwt", "label": "Cond LWT", "unit": "°C" },
        { "key": "cond_rwt", "label": "Cond RWT", "unit": "°C" },
        { "key": "cond_pressure", "label": "Cond Pressure", "unit": "kPa" },
        { "key": "cond_satur_temp", "label": "Cond Sat. Temp", "unit": "°C" },
        { "key": "fla", "label": "FLA", "unit": "%" },
        { "key": "input_power", "label": "Input Power", "unit": "kW" },
        { "key": "oil_sump_temp", "label": "Oil Sump Temp", "unit": "°C" },
        { "key": "discharge_temp", "label": "Discharge Temp", "unit": "°C" },
        { "key": "number_of_start", "label": "Starts", "unit": "" }
    ]
    now = datetime.now()
    start_date = (now - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    end_date = (now + timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M')
    return render_template('yk-vsd_type.html', data=dummy_data, chiller=dummy_chiller, historical_data=[], start_date=start_date, end_date=end_date, last_updated_timestamp=now, chart_parameters=chart_parameters)


@app.route('/analyze_warning/<string:chiller_id>/<int:warning_code>')
def analyze_warning(chiller_id, warning_code):
    # Dapatkan deskripsi peringatan dari kode
    warning_description = warning_codes.get(warning_code, "Unknown Warning")

    # Dapatkan data chiller terbaru
    chiller_data = None
    try:
        response = requests.get(f'http://127.0.0.1:8000/chillers/{chiller_id}/latest_data')
        response.raise_for_status()
        chiller_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch chiller data for analysis: {e}")
        # Lanjutkan tanpa data chiller, atau kembalikan error
        pass # Lanjutkan tanpa data chiller

    # Dapatkan kunci API Groq dari variabel lingkungan
    groq_api_key = "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"
    if not groq_api_key:
        return jsonify({"error": "GROQ_API_KEY not set."})

    # Filter out null values from chiller_data
    if chiller_data:
        filtered_chiller_data = {k: v for k, v in chiller_data.items() if v is not None}
        chiller_data_str = json.dumps(filtered_chiller_data, indent=2)
    else:
        chiller_data_str = "No additional chiller data available."

    # Buat prompt untuk Groq AI
    prompt = f"""
    Analyze the following chiller warning and provide a detailed explanation and potential causes.
    The analysis should be in Indonesian.

    Warning: "{warning_description}" (Code: {warning_code})

    Here is the current data from the chiller for context:
    {chiller_data_str}

    Provide the analysis in the following format:
    ### Deskripsi Peringatan
    [Detailed description of the warning based on the code and data]

    ### Analisis Data Chiller
    [Analyze the provided chiller data and how it might relate to the warning]

    ### Kemungkinan Penyebab
    * [Cause 1 based on warning and data]
    * [Cause 2 based on warning and data]
    * [Cause 3 based on warning and data]

    ### Langkah-langkah yang Disarankan
    * [Step 1]
    * [Step 2]
    * [Step 3]
    """

    try:
        # Panggil Groq API
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
        )
        response.raise_for_status()
        analysis_result = response.json()['choices'][0]['message']['content']
        return jsonify({"analysis": analysis_result})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to call Groq API: {e}"})
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"})

if __name__ == '__main__':
    try:
        locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Indonesian_Indonesia.1252')
        except locale.Error:
            print("Warning: Indonesian locale not found. Date/time may not be formatted correctly.")
    
    app.run(debug=True, host='0.0.0.0', port="7500")