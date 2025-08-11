from flask import Flask, render_template, request, redirect, url_for, flash, session
from auth import auth_bp
from datetime import datetime, timedelta
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

# --- HARDCODED LOOKUP TABLES (Lengkap) ---
safety_codes = {
    0: "No Safety Faults Present",
    1: "Evaporator - Low Pressure",
    2: "Evaporator - Transducer Or Leaving Liquid Probe",
    3: "Evaporator - Transducer Or Temperature Sensor",
    4: "Condenser - High Pressure Contacts Open",
    5: "Condenser - High Pressure",
    6: "Condenser - Pressure Transducer Out Of Range",
    7: "Auxiliary Safety - Contacts Closed",
    8: "Discharge - Low Temperature",
    9: "Discharge - High Temperature",
    10: "Oil - High Sump Temperature",
    11: "Oil - Low Differential Pressure",
    12: "Oil - High Differential Pressure",
    13: "Oil - Pump Pressure Transducer Out Of Range",
    14: "Oil - Sump Pressure Transducer Out Of Range",
    15: "Motor - Lack Of Motor Oil Change",
    16: "Sales Order - Invalid Compressor Model",
    17: "Sales Order - Invalid Gear Code",
    18: "Oil - Differential Pressure Calibration",
    19: "Safety Stop",
    20: "Oil - Variable Speed Pump - Setpoint Not Achieved",
    21: "Control Panel - Power Failure",
    22: "Control Panel - Loss Of Control Voltage",
    23: "MOTOR OR STARTER - CURRENT IMBALANCE",
    24: "Thrust Bearing - Proximity Probe Clearance",
    25: "Thrust Bearing - Proximity Probe Uncalibrated",
    26: "Thrust Bearing - Proximity Probe Out Of Range",
    27: "Thrust Bearing - High Oil Temperature",
    28: "Thrust Bearing - Oil Temperature Sensor",
    29: "VSD - High Heatsink Temperature",
    30: "VSD - 105% MOTOR CURRENT OVERLOAD",
    31: "VSD - HIGH PHASE A INVERTER HEATSINK TEMPERATURE",
    32: "VSD - HIGH PHASE B INVERTER HEATSINK TEMPERATURE",
    33: "VSD - HIGH PHASE C INVERTER HEATSINK TEMPERATURE",
    34: "VSD - HIGH CONVERTER HEATSINK TEMPERATURE",
    35: "VSD - PRECHARGE LOCKOUT",
    36: "HARMONIC FILTER - HIGH HEATSINK TEMPERATURE",
    37: "HARMONIC FILTER - HIGH TOTAL DEMAND DISTORTION",
    38: "LCSSS - PHASE ROTATION",
    39: "LCSSS - MOTOR OR STARTER - CURRENT IMBALANCE",
    40: "LCSSS - 105% MOTOR CURRENT OVERLOAD",
    41: "LCSSS - HIGH INSTANTANEOUS CURRENT",
    42: "LCSSS - OPEN SCR",
    43: "LCSSS - PHASE A SHORTED SCR",
    44: "LCSSS - PHASE B SHORTED SCR",
    45: "LCSSS - PHASE C SHORTED SCR",
    46: "LCSSS - HIGH PHASE A HEATSINK TEMPERATURE",
    47: "LCSSS - HIGH PHASE B HEATSINK TEMPERATURE",
    48: "LCSSS - HIGH PHASE C HEATSINK TEMPERATURE",
    49: "Starter - Invalid Motor Selection",
    50: "Oil or Conduser Transducer Error",
    51: "Evaporator - Low Pressure",
    52: "Evaporator - low Pressure - Smart Freeze",
    53: "Surge Protection - Excess Surge",
    54: "VSD - HIGH INVERTER BASEPLATE TEMPERATURE",
    55: "HARMONIC FILTER - HIGH BASEPLATE TEMPERATURE",
    56: "Thrust Bearing - Proximity Probe Clearance",
    57: "Thrust Bearing - Limit Switch Open",
    58: "VGD Actuator - Positioning Fault",
    59: "Oil - Sump Or Pump Transducer Error",
    60: "Motor - High Housing Temperature",
    61: "Motor - High Winding Temperature",
    62: "Motor - High Bearing Temperature",
    63: "VSD - HIGH PHASE A INVERTER BASEPLATE TEMPERATURE",
    64: "VSD - HIGH PHASE B INVERTER BASEPLATE TEMPERATURE",
    65: "VSD - HIGH PHASE C INVERTER BASEPLATE TEMPERATURE",
    66: "VSD - MOTOR CURRENT IMBALANCE",
    67: "Condenser - High Pressure - Stopped",
    68: "OIL - HIGH SUPPLY TEMPERATURE",
    69: "Motor - High Bearing Vibration",
    70: "SALES ORDER - INVALID MODEL NUMBER",
    71: "LCSSS - PHASE A OPEN SCR",
    72: "LCSSS - PHASE B OPEN SCR",
    73: "LCSSS - PHASE C OPEN SCR",
    74: "Motor - Lack Of Bearing Lubrication",
    75: "VSD - LOW FREQUENCY DETECTED",
    76: "VSD - Feedback Sensor",
    77: "VSD - Control Fault",
    78: "VSD - Drive Boot Failure",
    79: "MVSSS - PHASE ROTATION",
    80: "MVSSS - MOTOR OR STARTER - CURRENT IMBALANCE",
    81: "MVSSS - 105% MOTOR CURRENT OVERLOAD",
    82: "MVSSS - HIGH INSTANTANEOUS CURRENT",
    83: "MVSSS - FAILED SCR",
    84: "MVSSS - HIGH HEATSINK TEMPERATURE",
    85: "MVSSS - GROUND FAULT",
    86: "MVSSS - CONTACTOR FAULT",
    87: "MVSSS - CONTROL BOARD FAULT",
    88: "MVSSS - DISCONNECT FAULT",
    89: "VSD - POWER TRANSFORMER HIGH TEMPERATURE",
    90: "VSD - HIGH OUTPUT FREQUENCY",
    91: "MVVSD - GROUND FAULT",
    92: "VSD - MAIN CONTROL BOARD FAULT",
    93: "MVVSD - CONTACTOR FAULT",
    94: "MVVSD - INTERLOCK FAULT",
    95: "VSD - LOGIC BOARD PLUG",
    96: "VSD - INPUT CURRENT OVERLOAD",
    97: "VSD - HIGH PHASE A INPUT BASEPLATE TEMPERATURE",
    98: "VSD - HIGH PHASE B INPUT BASEPLATE TEMPERATURE",
    99: "VSD - HIGH PHASE C INPUT BASEPLATE TEMPERATURE",
    100: "MOTOR - LOW WINDING TEMPERATURE",
    101: "VSD - INVALID PWM SOFTWARE",
    102: "VSD - BASEPLATE TEMPERATURE IMBALANCE",
    103: "VSD - DC BUS PRE-REGULATION LOCKOUT",
    104: "VSD - GROUND FAULT",
    105: "VSD - HIGH INSTANTANEOUS CURRENT",
    106: "MOTOR CURRENT > 15% FLA",
    107: "VSD - FREQUENCY > 0 HZ",
    108: "VSD - PHASE A INPUT DCCT",
    109: "VSD - PHASE B INPUT DCCT",
    110: "VSD - PHASE C INPUT DCCT",
    111: "VSD - HIGH TOTAL DEMAND DISTORTION",
    112: "Motor - Coiling Coil Leak",
    113: "MVVSD - Excessive Shutdowns",
    114: "Isolation Valves - Not Opened",
    115: "VSD - OUTPUT PHASE ROTATION",
    116: "VSD - Phase Locked Loop",
    117: "VSD - HIGH PHASE A INSTANTANEOUS CURRENT",
    118: "VSD - HIGH PHASE B INSTANTANEOUS CURRENT",
    119: "VSD - HIGH PHASE C INSTANTANEOUS CURRENT",
    120: "VSD - Line Voltage Phase Rotation",
    121: "VSD - INPUT DCCT OFFSET LOCKOUT",
    122: "VSD - LOGIC BOARD HARDWARE",
    123: "VSD - RECTIFIER PROGRAM FAULT",
    124: "VSD - INVERTER PROGRAM FAULT",
    125: "VSD - DC BUS LOCKOUT - DO NOT RECYCLE POWER",
    126: "VSD - MOTOR CURREN THD FAULT",
    127: "VSD - HIGH PHASE A MOTOR CURRENT",
    128: "VSD - HIGH PHASE B MOTOR CURRENT",
    129: "VSD - HIGH PHASE C MOTOR CURRENT",
    130: "VSD - HIGH PHASE A MOTOR BASEPLATE TEMPERATURE",
    131: "VSD - HIGH PHASE B MOTOR BASEPLATE TEMPERATURE",
    132: "VSD - HIGH PHASE C MOTOR BASEPLATE TEMPERATURE",
    133: "VSD - PHASE A MOTOR DCCT",
    134: "VSD - PHASE B MOTOR DCCT",
    135: "VSD - PHASE C MOTOR DCCT",
    136: "Oil - High Sump Pressure",
    137: "MBC - OVERSPEED FAULT",
    138: "MBC - WATCHDOG",
    139: "MBC - POWER SUPPLY FAULT",
    140: "MBC - HIGH HEATSINK TEMPERATURE",
    141: "MBC - HIGH DC BUS VOLTAGE",
    142: "MBC - AMPLIFIER FUSE",
    143: "MBC - HIGH BEARING J TEMPERATURE",
    144: "MBC - HIGH BEARING H1 TEMPERATURE",
    145: "MBC - HIGH BEARING H2 TEMPERATURE",
    146: "MBC - HIGH BEARING K TEMPERATURE",
    147: "MBC - GROUND FAULT",
    148: "MBC - LOW GATE VOLTAGE",
    149: "MBC - HIGH GATE VOLTAGE",
    150: "MBC - HIGH AMPLIFIER TEMPERATURE",
    151: "MBC - HIGH AMPLIFIER VOLTAGE",
    152: "MBC - FAULT CONTACTS OPEN",
    153: "MBC - INITIALIZATION FAILURE",
    154: "MBC - NOT LEVITATED",
    155: "SYSTEM - STARTUP FAILURE",
    156: "UPS - Battery Not Connected",
    157: "UPS - Inverter Low Battery Voltage",
    158: "MBC - SPEED SENSOR FAULT",
    159: "MBC - POWER FAIL LANDING",
    160: "COMPRESSOR - LOW DISCHARGE SUPERHEAT",
    161: "MVSSS - HIGH HEATSINK 1 TEMPERATURE",
    162: "MVSSS - HIGH HEATSINK 2 TEMPERATURE",
    163: "MVSSS - HIGH HEATSINK 3 TEMPERATURE",
    164: "MOTOR CONTROLLER - FAULT CONTACTS OPEN",
    165: "VSD - HIGH PHASE A2 INSTANTANEOUS CURRENT",
    166: "VSD - HIGH PHASE B2 INSTANTANEOUS CURRENT",
    167: "VSD - HIGH PHASE C2 INSTANTANEOUS CURRENT",
    168: "VSD - HIGH PHASE A2 INVERTER BASEPLATE TEMPERATURE",
    169: "VSD - HIGH PHASE B2 INVERTER BASEPLATE TEMPERATURE",
    170: "VSD - HIGH PHASE C2 INVERTER BASEPLATE TEMPERATURE",
    171: "VSD - HIGH CONVERTER 2 HEATSINK TEMPERATURE",
    172: "VSD - MOTOR CURRENT 2 IMBALANCE",
    173: "VSD - MOTOR CURRENT MISMATCH",
    174: "VSD - HIGH PHASE A INPUT CURRENT",
    175: "VSD - HIGH PHASE B INPUT CURRENT",
    176: "VSD - HIGH PHASE C INPUT CURRENT",
    177: "VSD - HIGH INPUT CURRENT TDD",
    178: "INTERNAL ERROR - NO TIMER HANDERS AVAILABLE",
    179: "WATCHDOG - SOFTWARE REBOOT",
    180: "VSD - PRECHARGE LOCKOUT 2",
    181: "VSD - BASEPLATE TEMPERATURE IMBALANCE 2",
    182: "OIL - VARIABLE SPEED PUMP - HIGH RATE OF CHANGE",
    183: "VSD - HIGH MOTOR HARMONICS",
    184: "VSD - CAPACITOR FAULT",
    185: "VSD - ELECTRICAL SGNATURE BOARD",
}

cycling_codes = {
    0: "No Cycling Faults Present",
    1: "Multiunit Cycling - Contacts Open",
    2: "System Cycling - Contact Open",
    3: "Oil - Low Temperature Differntial",
    4: "Oil - Low Sump Temperature",
    5: "Control Panel - Power Failure",
    6: "Leaving Chilled Liquid - Low Temperature",
    7: "Leaving Chilled Liquid - Flow Switch Open",
    8: "Condenser - Flow Switch Open",
    9: "MOTOR CONTROLLER - FAULT CONTACTS OPEN",
    10: "MOTOR CONTROLLER - LOSS OF CURRENT",
    11: "POWER FAULT",
    12: "Control Panel - Schedule",
    13: "Starter - Low Supply Line Voltage",
    14: "Starter - High Supply Line Voltage",
    15: "Proximity Probe - Low Supply Voltage",
    16: "Oil - Variable Speed Pump - Drive Contacts Open",
    17: "VSD - INITIALIZATION FAILED",
    18: "VSD Shutdown - Requesting Fault Data",
    19: "VSD - HIGH PHASE A INSTANTANEOUS CURRENT",
    20: "VSD - HIGH PHASE B INSTANTANEOUS CURRENT",
    21: "VSD - HIGH PHASE C INSTANTANEOUS CURRENT",
    22: "VSD - PHASE A GATE DRIVER",
    23: "VSD - PHASE B GATE DRIVER",
    24: "VSD - PHASE C GATE DRIVER",
    25: "VSD - SINGLE PHASE INPUT POWER",
    26: "VSD - HIGH DC BUS VOLTAGE",
    27: "VSD - LOGIC BOARD POWER SUPPLY",
    28: "VSD - LOW DC BUS VOLTAGE",
    29: "VSD - DC BUS VOLTAGE IMBALANCE",
    30: "VSD - HIGH INTERNAL AMBIENT TEMPERATURE",
    31: "VSD - INVALID CURRENT SCALE SELECTION",
    32: "VSD - LOW PHASE A INVERTER HEATSINK TEMPERATURE",
    33: "VSD - LOW PHASE B INVERTER HEATSINK TEMPERATURE",
    34: "VSD - LOW PHASE C INVERTER HEATSINK TEMPERATURE",
    35: "VSD - LOW CONVERTER HEATSINK TEMPERATURE",
    36: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE",
    37: "VSD - PRECHARGE - LOW DC BUS VOLTAGE",
    38: "VSD - LOGIC BOARD PROCESSOR",
    39: "VSD - RUN SIGNAL",
    40: "VSD - SERIAL RECEIVE",
    41: "VSD - Stop Contacts Open",
    42: "Harmonic Filter - Logic Board Or Communications",
    43: "HARMONIC FILTER - HIGH DC BUS VOLTAGE",
    44: "HARMONIC FILTER - HIGH PHASE A CURRENT",
    45: "HARMONIC FILTER - HIGH PHASE B CURRENT",
    46: "HARMONIC FILTER - HIGH PHASE C CURRENT",
    47: "HARMONIC FILTER - PHASE LOCKED LOOP",
    48: "Harmonic Filter - Precharge - Low DC Bus Voltage",
    49: "HARMONIC FILTER - LOW DC BUS VOLTAGE",
    50: "HARMONIC FILTER - DC BUS VOLTAGE IMBALANCE",
    51: "HARMONIC FILTER - INPUT CURRENT OVERLOAD",
    52: "HARMONIC FILTER - LOGIC BOARD POWER SUPPLY",
    53: "HARMONIC FILTER - RUN SIGNAL",
    54: "HARMONIC FILTER - DC CURRENT TRANSFORMER 1",
    55: "HARMONIC FILTER - DC CURRENT TRANSFORMER 2",
    56: "LCSSS Initialization Failed",
    57: "LCSSS Shutdown - Requesting Full Data",
    58: "LCSSS - LOW PHASE A TEMPERATURE SENSOR",
    59: "LCSSS - LOW PHASE B TEMPERATURE SENSOR",
    60: "LCSSS - LOW PHASE C TEMPERATURE SENSOR",
    61: "LCSSS - PHASE LOCKED LOOP",
    62: "LCSSS - POWER FAULT",
    63: "LCSSS - HIGH SUPPLY LINE VOLTAGE",
    64: "LCSSS - LOW SUPPLY LINE VOLTAGE",
    65: "LCSSS - INVALID CURRENT SCALE SELECTION",
    66: "LCSSS - RUN SIGNAL",
    67: "LCSSS - SERIAL RECEIVE",
    68: "LCSSS - Stop Contacts Open",
    69: "Motor Auto Lubrication In Progress",
    70: "Control Panel - Loss Of Control Voltage",
    71: "LCSSS - LOGIC BOARD PROCESSOR",
    72: "LCSSS - LOGIC BOARD POWER SUPPLY",
    73: "VSD - Serial Communications",
    74: "LCSSS - Serial Communications",
    75: "LCSSS - PHASE LOSS",
    76: "VSD - LOW INVERTER BASEPLATE TEMPERATURE",
    77: "Expansion I/O - Serial Communications",
    78: "VSD - LOW PHASE A INVERTER BASEPLATE TEMPERATURE",
    79: "VSD - LOW PHASE B INVERTER BASEPLATE TEMPERATURE",
    80: "VSD - LOW PHASE C INVERTER BASEPLATE TEMPERATURE",
    81: "Motor Controller - Contacts Open",
    82: "MVVSD - Serial Communications",
    83: "VSD - Input Power Transformer",
    84: "VSD - Input Over-Voltage",
    85: "VSD - LOSS OF COOLING FAN",
    86: "VSD - HIGH INSTANTANEOUS CURRENT",
    87: "MVSSS - Initialization Failed",
    88: "MVSSS Shutdown - Requesting Full Data",
    89: "MVSSS - POWER FAULT",
    90: "MVSSS - HIGH SUPPLY LINE VOLTAGE",
    91: "MVSSS - LOW SUPPLY LINE VOLTAGE",
    92: "MVSSS - RUN SIGNAL",
    93: "MVSSS - Serial Communications",
    94: "MVSSS - Stop Contacts Open",
    95: "MVSSS - LOGIC BOARD POWER SUPPLY",
    96: "MVSSS - PHASE LOSS",
    97: "REFRIGERANT TYPE NOT SET",
    98: "VSD - Serial Communications",
    99: "LCSSS - Serial Comms",
    100: "VSD - Serial Communications",
    101: "Auto Detect - Serial Communications",
    102: "VSD - DC BUS VOLTAGE IMBALANCE - AU",
    103: "VSD - DC BUS VOLTAGE IMBALANCE - AL",
    104: "VSD - DC BUS VOLTAGE IMBALANCE - BU",
    105: "VSD - DC BUS VOLTAGE IMBALANCE - BL",
    106: "VSD - DC BUS VOLTAGE IMBALANCE - CU",
    107: "VSD - DC BUS VOLTAGE IMBALANCE - CL",
    108: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - AU",
    109: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - AL",
    110: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - BU",
    111: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - BL",
    112: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - CU",
    113: "VSD - PRECHARGE - DC BUS VOLTAGE IMBALANCE - CL",
    114: "VSD - HIGH DC BUS VOLTAGE - AU",
    115: "VSD - HIGH DC BUS VOLTAGE - AL",
    116: "VSD - HIGH DC BUS VOLTAGE - BU",
    117: "VSD - HIGH DC BUS VOLTAGE - BL",
    118: "VSD - HIGH DC BUS VOLTAGE - CU",
    119: "VSD - HIGH DC BUS VOLTAGE - CL",
    120: "VSD - GATE DRIVER - ANU",
    121: "VSD - GATE DRIVER - ANL",
    122: "VSD - GATE DRIVER - AMU",
    123: "VSD - GATE DRIVER - AML",
    124: "VSD - GATE DRIVER - BNU",
    125: "VSD - GATE DRIVER - BNL",
    126: "VSD - GATE DRIVER - BMU",
    127: "VSD - GATE DRIVER - BML",
    128: "VSD - GATE DRIVER - CNU",
    129: "VSD - GATE DRIVER - CNL",
    130: "VSD - GATE DRIVER - CMU",
    131: "VSD - GATE DRIVER - CML",
    132: "VSD - INPUT POWER SUPPLY",
    133: "VSD - HIGH PHASE A INPUT CURRENT",
    134: "VSD - HIGH PHASE B INPUT CURRENT",
    135: "VSD - HIGH PHASE C INPUT CURRENT",
    136: "VSD - HIGH PHASE A MOTOR CURRENT",
    137: "VSD - HIGH PHASE B MOTOR CURRENT",
    138: "VSD - HIGH PHASE C MOTOR CURRENT",
    139: "VSD - PHASE A INPUT GATE DRIVER",
    140: "VSD - PHASE B INPUT GATE DRIVER",
    141: "VSD - PHASE C INPUT GATE DRIVER",
    142: "VGD Actuator - Serial Communications",
    143: "VSD - INVALID VSD MODEL",
    144: "VSD - BASEPLATE TEMPERATURE IMBALANCE",
    145: "VSD - LOW PHASE A INPUT BASEPLATE TEMPERATURE",
    146: "VSD - LOW PHASE B INPUT BASEPLATE TEMPERATURE",
    147: "VSD - LOW PHASE C INPUT BASEPLATE TEMPERATURE",
    148: "VSD - PHASE LOCKED LOOP",
    149: "VSD - LINE VOLTAGE PHASE ROTATION",
    150: "VSD - PRECHARGE - LOW DC BUS VOLTAGE 1",
    151: "VSD - Input Voltage Imbalance",
    152: "VSD - DC BUS PRE-REGULATION",
    153: "VSD - LOGIC BOARD PROCESSOR",
    154: "MVSSS - SERIAL RECEIVE",
    155: "VSD - Identifying Drive",
    156: "Leaving Condensor Liquid - High Temperature",
    157: "Condenser - Freeze Threat - Flow Switch Open",
    158: "Isolation Valves - Not Closed",
    159: "VSD - PHASE A INPUT DCCT OFFSET",
    160: "VSD - PHASE B INPUT DCCT OFFSET",
    161: "VSD - PHASE C INPUT DCCT OFFSET",
    162: "VSD - INVALID SETPOINTS",
    163: "VSD - PRECHARGE - LOW DC BUS VOLTAGE 2",
    164: "VSD - SERIAL RECEIVE",
    165: "VSD - PHASE A MOTOR GATE DRIVER",
    166: "VSD - PHASE B MOTOR GATE DRIVER",
    167: "VSD - PHASE C MOTOR GATE DRIVER",
    168: "VSD - LOW PHASE A MOTOR BASEPLATE TEMPERATURE",
    169: "VSD - LOW PHASE B MOTOR BASEPLATE TEMPERATURE",
    170: "VSD - LOW PHASE C MOTOR BASEPLATE TEMPERATURE",
    171: "VSD - NOT RUNNING",
    172: "Motor - Lack Of Bearing Lubrication",
    173: "Evaporator - Low Pressure",
    174: "Expansion I/O - Serial Communications",
    175: "Evaporator - Low Pressure - Smart Freeze",
    176: "MBC - LOW DC BUS VOLTAGE",
    177: "MBC - J RADIAL POSITION",
    178: "MBC - K RADIAL POSITION",
    179: "MBC - H AXIAL POSITION",
    180: "MBC - FAULT CONTACTS OPEN",
    181: "MBC - SERIAL COMMUNICATIONS",
    182: "SYSTEM - STARTUP FAILURE",
    183: "UPS - Line Low Battery Voltage",
    184: "MBC - CALIBRATION FAULT",
    185: "MBC - BEARING CALIBRATION REQUIRED",
    186: "MOTOR CONTROLLER - INITIALIZATION FAILURE",
    187: "MOTOR CONTROLLER - SERIAL COMMUNICATION",
    188: "HARMONIC FILTER - PRECHARGE - LOW DC BUS VOLTAGE 1",
    189: "HARMONIC FILTER - PRECHARGE - LOW DC BUS VOLTAGE 2",
    190: "VSD - HIGH PHASE A2 INSTANTANEOUS CURRENT",
    191: "VSD - HIGH PHASE B2 INSTANTANEOUS CURRENT",
    192: "VSD - HIGH PHASE C2 INSTANTANEOUS CURRENT",
    193: "VSD - PHASE A2 GATE DRIVER",
    194: "VSD - PHASE B2 GATE DRIVER",
    195: "VSD - PHASE C2 GATE DRIVER",
    196: "VSD - HIGH DC BUS 2 VOLTAGE",
    197: "VSD - LOW DC BUS 2 VOLTAGE",
    198: "VSD - DC BUS 2 VOLTAGE IMBALANCE",
    199: "VSD - LOW PHASE A2 INVERTER BASEPLATE TEMPERATURE",
    200: "VSD - LOW PHASE B2 INVERTER BASEPLATE TEMPERATURE",
    201: "VSD - LOW PHASE C2 INVERTER BASEPLATE TEMPERATURE",
    202: "VSD - LOW CONVERTER 2 HEATSINK TEMPERATURE",
    203: "VSD - PRECHARGE - DC BUS 2 VOLTAGE IMBALANCE",
    204: "VSD - PRECHARGE - LOW DC BUS 2 VOLTAGE 1",
    205: "VSD - PRECHARGE - LOW DC BUS 2 VOLTAGE 2",
    206: "VSD - DC BUS VOLTAGE MISMATCH",
    207: "UPS - NOT CHARGING",
    208: "VSD - SINGLE PHASE INPUT POWER 2",
    209: "VSD - 105% MOTOR CURRENT OVERLOAD 2",
    210: "VSD - BASEPLATE TEMPERATURE IMBALANCE 2",
}

warning_codes = {
    0: "No Safety Faults Present",
    1: "Evaporator - Low Pressure",
    2: "Evaporator - Transducer Or Leaving Liquid Probe",
    3: "Evaporator - Transducer Or Temperature Sensor",
    4: "Condenser - High Pressure Contacts Open",
    5: "Condenser - High Pressure",
    6: "Condenser - Pressure Transducer Out Of Range",
    7: "Auxiliary Safety - Contacts Closed",
    8: "Discharge - Low Temperature",
    9: "Discharge - High Temperature",
    10: "Oil - High Sump Temperature",
    11: "Oil - Low Differential Pressure",
    12: "Oil - High Differential Pressure",
    13: "Oil - Pump Pressure Transducer Out Of Range",
    14: "Oil - Sump Pressure Transducer Out Of Range",
    15: "Motor - Lack Of Motor Oil Change",
    16: "Sales Order - Invalid Compressor Model",
    17: "Sales Order - Invalid Gear Code",
    18: "Oil - Differential Pressure Calibration",
    19: "Safety Stop",
    20: "Oil - Variable Speed Pump - Setpoint Not Achieved",
    21: "Control Panel - Power Failure",
    22: "Control Panel - Loss Of Control Voltage",
    23: "MOTOR OR STARTER - CURRENT IMBALANCE",
    24: "Thrust Bearing - Proximity Probe Clearance",
    25: "Thrust Bearing - Proximity Probe Uncalibrated",
    26: "Thrust Bearing - Proximity Probe Out Of Range",
    27: "Thrust Bearing - High Oil Temperature",
    28: "Thrust Bearing - Oil Temperature Sensor",
    29: "VSD - High Heatsink Temperature",
    30: "VSD - 105% MOTOR CURRENT OVERLOAD",
    31: "VSD - HIGH PHASE A INVERTER HEATSINK TEMPERATURE",
    32: "VSD - HIGH PHASE B INVERTER HEATSINK TEMPERATURE",
    33: "VSD - HIGH PHASE C INVERTER HEATSINK TEMPERATURE",
    34: "VSD - HIGH CONVERTER HEATSINK TEMPERATURE",
    35: "VSD - PRECHARGE LOCKOUT",
    36: "HARMONIC FILTER - HIGH HEATSINK TEMPERATURE",
    37: "HARMONIC FILTER - HIGH TOTAL DEMAND DISTORTION",
    38: "LCSSS - PHASE ROTATION",
    39: "LCSSS - MOTOR OR STARTER - CURRENT IMBALANCE",
    40: "LCSSS - 105% MOTOR CURRENT OVERLOAD",
    41: "LCSSS - HIGH INSTANTANEOUS CURRENT",
    42: "LCSSS - OPEN SCR",
    43: "LCSSS - PHASE A SHORTED SCR",
    44: "LCSSS - PHASE B SHORTED SCR",
    45: "LCSSS - PHASE C SHORTED SCR",
    46: "LCSSS - HIGH PHASE A HEATSINK TEMPERATURE",
    47: "LCSSS - HIGH PHASE B HEATSINK TEMPERATURE",
    48: "LCSSS - HIGH PHASE C HEATSINK TEMPERATURE",
    49: "Starter - Invalid Motor Selection",
    50: "Oil or Conduser Transducer Error",
    51: "Evaporator - Low Pressure",
    52: "Evaporator - low Pressure - Smart Freeze",
    53: "Surge Protection - Excess Surge",
    54: "VSD - HIGH INVERTER BASEPLATE TEMPERATURE",
    55: "HARMONIC FILTER - HIGH BASEPLATE TEMPERATURE",
    56: "Thrust Bearing - Proximity Probe Clearance",
    57: "Thrust Bearing - Limit Switch Open",
    58: "VGD Actuator - Positioning Fault",
    59: "Oil - Sump Or Pump Transducer Error",
    60: "Motor - High Housing Temperature",
    61: "Motor - High Winding Temperature",
    62: "Motor - High Bearing Temperature",
    63: "VSD - HIGH PHASE A INVERTER BASEPLATE TEMPERATURE",
    64: "VSD - HIGH PHASE B INVERTER BASEPLATE TEMPERATURE",
    65: "VSD - HIGH PHASE C INVERTER BASEPLATE TEMPERATURE",
    66: "VSD - MOTOR CURRENT IMBALANCE",
    67: "Condenser - High Pressure - Stopped",
    68: "OIL - HIGH SUPPLY TEMPERATURE",
    69: "Motor - High Bearing Vibration",
    70: "SALES ORDER - INVALID MODEL NUMBER",
    71: "LCSSS - PHASE A OPEN SCR",
    72: "LCSSS - PHASE B OPEN SCR",
    73: "LCSSS - PHASE C OPEN SCR",
    74: "Motor - Lack Of Bearing Lubrication",
    75: "VSD - LOW FREQUENCY DETECTED",
    76: "VSD - Feedback Sensor",
    77: "VSD - Control Fault",
    78: "VSD - Drive Boot Failure",
    79: "MVSSS - PHASE ROTATION",
    80: "MVSSS - MOTOR OR STARTER - CURRENT IMBALANCE",
    81: "MVSSS - 105% MOTOR CURRENT OVERLOAD",
    82: "MVSSS - HIGH INSTANTANEOUS CURRENT",
    83: "MVSSS - FAILED SCR",
    84: "MVSSS - HIGH HEATSINK TEMPERATURE",
    85: "MVSSS - GROUND FAULT",
    86: "MVSSS - CONTACTOR FAULT",
    87: "MVSSS - CONTROL BOARD FAULT",
    88: "MVSSS - DISCONNECT FAULT",
    89: "VSD - POWER TRANSFORMER HIGH TEMPERATURE",
    90: "VSD - HIGH OUTPUT FREQUENCY",
    91: "MVVSD - GROUND FAULT",
    92: "VSD - MAIN CONTROL BOARD FAULT",
    93: "MVVSD - CONTACTOR FAULT",
    94: "MVVSD - INTERLOCK FAULT",
    95: "VSD - LOGIC BOARD PLUG",
    96: "VSD - INPUT CURRENT OVERLOAD",
    97: "VSD - HIGH PHASE A INPUT BASEPLATE TEMPERATURE",
    98: "VSD - HIGH PHASE B INPUT BASEPLATE TEMPERATURE",
    99: "VSD - HIGH PHASE C INPUT BASEPLATE TEMPERATURE",
    100: "MOTOR - LOW WINDING TEMPERATURE",
    101: "VSD - INVALID PWM SOFTWARE",
    102: "VSD - BASEPLATE TEMPERATURE IMBALANCE",
    103: "VSD - DC BUS PRE-REGULATION LOCKOUT",
    104: "VSD - GROUND FAULT",
    105: "VSD - HIGH INSTANTANEOUS CURRENT",
    106: "MOTOR CURRENT > 15% FLA",
    107: "VSD - FREQUENCY > 0 HZ",
    108: "VSD - PHASE A INPUT DCCT",
    109: "VSD - PHASE B INPUT DCCT",
    110: "VSD - PHASE C INPUT DCCT",
    111: "VSD - HIGH TOTAL DEMAND DISTORTION",
    112: "Motor - Coiling Coil Leak",
    113: "MVVSD - Excessive Shutdowns",
    114: "Isolation Valves - Not Opened",
    115: "VSD - OUTPUT PHASE ROTATION",
    116: "VSD - Phase Locked Loop",
    117: "VSD - HIGH PHASE A INSTANTANEOUS CURRENT",
    118: "VSD - HIGH PHASE B INSTANTANEOUS CURRENT",
    119: "VSD - HIGH PHASE C INSTANTANEOUS CURRENT",
    120: "VSD - Line Voltage Phase Rotation",
    121: "VSD - INPUT DCCT OFFSET LOCKOUT",
    122: "VSD - LOGIC BOARD HARDWARE",
    123: "VSD - RECTIFIER PROGRAM FAULT",
    124: "VSD - INVERTER PROGRAM FAULT",
    125: "VSD - DC BUS LOCKOUT - DO NOT RECYCLE POWER",
    126: "VSD - MOTOR CURREN THD FAULT",
    127: "VSD - HIGH PHASE A MOTOR CURRENT",
    128: "VSD - HIGH PHASE B MOTOR CURRENT",
    129: "VSD - HIGH PHASE C MOTOR CURRENT",
    130: "VSD - HIGH PHASE A MOTOR BASEPLATE TEMPERATURE",
    131: "VSD - HIGH PHASE B MOTOR BASEPLATE TEMPERATURE",
    132: "VSD - HIGH PHASE C MOTOR BASEPLATE TEMPERATURE",
    133: "VSD - PHASE A MOTOR DCCT",
    134: "VSD - PHASE B MOTOR DCCT",
    135: "VSD - PHASE C MOTOR DCCT",
    136: "Oil - High Sump Pressure",
    137: "MBC - OVERSPEED FAULT",
    138: "MBC - WATCHDOG",
    139: "MBC - POWER SUPPLY FAULT",
    140: "MBC - HIGH HEATSINK TEMPERATURE",
    141: "MBC - HIGH DC BUS VOLTAGE",
    142: "MBC - AMPLIFIER FUSE",
    143: "MBC - HIGH BEARING J TEMPERATURE",
    144: "MBC - HIGH BEARING H1 TEMPERATURE",
    145: "MBC - HIGH BEARING H2 TEMPERATURE",
    146: "MBC - HIGH BEARING K TEMPERATURE",
    147: "MBC - GROUND FAULT",
    148: "MBC - LOW GATE VOLTAGE",
    149: "MBC - HIGH GATE VOLTAGE",
    150: "MBC - HIGH AMPLIFIER TEMPERATURE",
    151: "MBC - HIGH AMPLIFIER VOLTAGE",
    152: "MBC - FAULT CONTACTS OPEN",
    153: "MBC - INITIALIZATION FAILURE",
    154: "MBC - NOT LEVITATED",
    155: "SYSTEM - STARTUP FAILURE",
    156: "UPS - Battery Not Connected",
    157: "UPS - Inverter Low Battery Voltage",
    158: "MBC - SPEED SENSOR FAULT",
    159: "MBC - POWER FAIL LANDING",
    160: "COMPRESSOR - LOW DISCHARGE SUPERHEAT",
    161: "MVSSS - HIGH HEATSINK 1 TEMPERATURE",
    162: "MVSSS - HIGH HEATSINK 2 TEMPERATURE",
    163: "MVSSS - HIGH HEATSINK 3 TEMPERATURE",
    164: "MOTOR CONTROLLER - FAULT CONTACTS OPEN",
    165: "VSD - HIGH PHASE A2 INSTANTANEOUS CURRENT",
    166: "VSD - HIGH PHASE B2 INSTANTANEOUS CURRENT",
    167: "VSD - HIGH PHASE C2 INSTANTANEOUS CURRENT",
    168: "VSD - HIGH PHASE A2 INVERTER BASEPLATE TEMPERATURE",
    169: "VSD - HIGH PHASE B2 INVERTER BASEPLATE TEMPERATURE",
    170: "VSD - HIGH PHASE C2 INVERTER BASEPLATE TEMPERATURE",
    171: "VSD - HIGH CONVERTER 2 HEATSINK TEMPERATURE",
    172: "VSD - MOTOR CURRENT 2 IMBALANCE",
    173: "VSD - MOTOR CURRENT MISMATCH",
    174: "VSD - HIGH PHASE A INPUT CURRENT",
    175: "VSD - HIGH PHASE B INPUT CURRENT",
    176: "VSD - HIGH PHASE C INPUT CURRENT",
    177: "VSD - HIGH INPUT CURRENT TDD",
    178: "INTERNAL ERROR - NO TIMER HANDERS AVAILABLE",
    179: "WATCHDOG - SOFTWARE REBOOT",
    180: "VSD - PRECHARGE LOCKOUT 2",
    181: "VSD - BASEPLATE TEMPERATURE IMBALANCE 2",
    182: "OIL - VARIABLE SPEED PUMP - HIGH RATE OF CHANGE",
    183: "VSD - HIGH MOTOR HARMONICS",
    184: "VSD - CAPACITOR FAULT",
    185: "VSD - ELECTRICAL SGNATURE BOARD",
}

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
                       power_kW, ton_of_refrigeration, image_name AS gambar_url
                FROM chillers
                WHERE site_id = %s
            """, (site_id,))
            chillers = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Error saat mengambil daftar chiller: {err}", 'danger')
        finally:
            if cursor:
                cursor.close()
            if conn:
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
    if chiller_details and chiller_details.get('chiller_type'):
        specific_template = f"{chiller_details['chiller_type'].lower()}_type.html"
        if os.path.exists(os.path.join(app.template_folder, specific_template)):
            template_to_render = specific_template
        else:
            print(f"Warning: Template {specific_template} not found. Falling back to default_type.html.")

    return render_template(
        template_to_render, 
        active_page='chiller_monitor', 
        current_time=current_time, 
        chiller=chiller_details,
        data=latest_chiller_data,
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date,
        last_updated_timestamp=last_updated_timestamp
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


if __name__ == '__main__':
    try:
        locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Indonesian_Indonesia.1252')
        except locale.Error:
            print("Warning: Indonesian locale not found. Date/time may not be formatted correctly.")
    app.run(debug=True, host='0.0.0.0')