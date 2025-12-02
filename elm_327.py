import serial
import time
import datetime
import re

# CONFIG
PORTA = "/dev/rfcomm0"
BAUDRATE = 9600
READ_BUFFER_TIMEOUT = 0.8
LOG_FILE = "data_log.txt"

PIDS_DA_LEGGERE = {
    "0104": ("Carico Motore", "%"),
    "0105": ("Temp. Liquido Raffred.", "°C"),
    "010B": ("Pressione Turbo/MAP", "kPa"),
    "010C": ("Giri Motore (RPM)", "rpm"),
    "010D": ("Velocità Veicolo", "km/h"),
    "010F": ("Temp. Aria Aspirata", "°C"),
    "0110": ("MAF (Flusso Aria)", "g/s"),
    "0111": ("Posizione Farfalla", "%"),
    "0142": ("Voltaggio Centralina", "V"),
    "012F": ("Livello Carburante", "%"),
    "015C": ("Temp. Olio Motore", "°C"),
    "0133": ("Pressione Barometrica", "kPa"),
}

PID_FORMULAS = {
    "0104": lambda A, B: (A * 100) / 255,
    "0105": lambda A, B: A - 40,
    "010B": lambda A, B: A,
    "010C": lambda A, B: ((A * 256) + B) / 4,
    "010D": lambda A, B: A,
    "010F": lambda A, B: A - 40,
    "0110": lambda A, B: ((A * 256) + B) / 100,
    "0111": lambda A, B: (A * 100) / 255,
    "012F": lambda A, B: (A * 100) / 255,
    "0133": lambda A, B: A,
    "0142": lambda A, B: ((A * 256) + B) / 1000,
    "015C": lambda A, B: A - 40,
}

def init_adattatore(ser):
    for cmd in ["ATZ","ATE0","ATL0","ATSP6","0100"]:
        ser.write((cmd+"\r").encode())
        time.sleep(0.5)
        ser.read_all()
    time.sleep(0.5)

def read_all_until_timeout(ser, timeout=READ_BUFFER_TIMEOUT):
    deadline = time.time() + timeout
    buf = ""
    while time.time() < deadline:
        part = ser.read_all().decode('utf-8', errors='ignore')
        if part:
            buf += part
            deadline = time.time() + 0.08
        else:
            time.sleep(0.02)
    return re.sub(r'[\r\n]+', ' ', buf).strip()

def try_parse(pid, raw):
    if not raw: return None
    s = raw.upper()
    if "NO DATA" in s: return None
    pid_byte = pid[2:].upper()
    m = re.search(r'41\W+' + re.escape(pid_byte) + r'\W+([0-9A-F]{2})(?:\W+([0-9A-F]{2}))?', s)
    if m:
        try:
            A = int(m.group(1),16)
            B = int(m.group(2),16) if m.group(2) else 0
            fn = PID_FORMULAS.get(pid)
            return fn(A,B) if fn else None
        except:
            return None
    m2 = re.search(r'41\W+([0-9A-F]{2})\W+([0-9A-F]{2})', s)
    if m2:
        try:
            A = int(m2.group(1),16)
            B = int(m2.group(2),16)
            fn = PID_FORMULAS.get(pid)
            return fn(A,B) if fn else None
        except:
            return None
    return None

try:
    ser = serial.Serial(PORTA, BAUDRATE, timeout=1)
    init_adattatore(ser)

    print(f"{'TIMESTAMP':<15} | {'PID':<6} | {'DESCRIZIONE':<22} | {'VALORE':<18} | RAW")
    print("-"*120)

    while True:
        for pid, (desc, unit) in PIDS_DA_LEGGERE.items():
            ser.write((pid + '\r').encode())
            time.sleep(0.05)
            raw = read_all_until_timeout(ser, timeout=READ_BUFFER_TIMEOUT)
            raw_norm = raw.replace('>', ' ').strip()
            parsed = try_parse(pid, raw_norm)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if isinstance(parsed, (int,float)):
                valstr = f"{parsed:.2f} {unit}"
            else:
                valstr = "N/A"
            print(f"{timestamp:<15} | {pid:<6} | {desc:<22} | {valstr:<18} | {raw_norm}")

            # append log
            with open(LOG_FILE, "a") as f:
                f.write(f"{timestamp}, {pid}, {desc}, {valstr}, {raw_norm}\n")

            time.sleep(0.03)

except KeyboardInterrupt:
    if 'ser' in locals() and ser.is_open: ser.close()
except Exception as e:
    print("Errore:", e)
