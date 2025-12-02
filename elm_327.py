import serial
import time
import datetime
import sys

# --- CONFIGURAZIONE ---
PORTA = "/dev/rfcomm0"  # O 'COM3' su Windows
BAUDRATE = 38400
# ----------------------

# Dizionario dei PID per Golf 7 (Mode 01)
PIDS_DA_LEGGERE = {
    "0104": ("Carico Motore", "%"),
    "0105": ("Temp. Liquido Raffred.", "°C"),
    "010B": ("Pressione Turbo/MAP", "kPa"), # Importante per TSI/TDI
    "010C": ("Giri Motore (RPM)", "rpm"),
    "010D": ("Velocità Veicolo", "km/h"),
    "010F": ("Temp. Aria Aspirata", "°C"),
    "0110": ("MAF (Flusso Aria)", "g/s"),
    "0111": ("Posizione Farfalla", "%"),
    "0142": ("Voltaggio Centralina", "V"),
    # Questi sotto potrebbero non andare su tutte le Golf 7:
    "012F": ("Livello Carburante", "%"), 
    "015C": ("Temp. Olio Motore", "°C"), 
    "0133": ("Pressione Barometrica", "kPa"),
}

# --- FORMULE DI CONVERSIONE (Dictionary Dispatch) ---
# Mappa il PID a una funzione lambda che accetta A e B
PID_FORMULAS = {
    "0104": lambda A, B: (A * 100) / 255,          # Carico Motore
    "0105": lambda A, B: A - 40,                   # Temp Acqua
    "010B": lambda A, B: A,                        # MAP
    "010C": lambda A, B: ((A * 256) + B) / 4,      # RPM
    "010D": lambda A, B: A,                        # Velocità
    "010F": lambda A, B: A - 40,                   # Temp Aria
    "0110": lambda A, B: ((A * 256) + B) / 100,    # MAF
    "0111": lambda A, B: (A * 100) / 255,          # Farfalla
    "012F": lambda A, B: (A * 100) / 255,          # Carburante
    "0133": lambda A, B: A,                        # Press. Barometrica
    "0142": lambda A, B: ((A * 256) + B) / 1000,   # Voltaggio
    "015C": lambda A, B: A - 40,                   # Temp Olio
}

# Teniamo traccia dei PID che sappiamo già non essere supportati per non intasare il log
pids_non_supportati = set()

def init_adattatore(ser):
    """Inizializza l'ELM327"""
    comandi = [
        "ATZ",      # Reset
        "ATE0",     # Echo Off
        "ATL0",     # Linefeeds Off
        "ATSP6",    # Protocollo ISO 15765-4 CAN (Golf 7)
        "ATSH7E0",  # Header 7E0 (Standard Engine ECU per VW)
        "0100"      # Handshake di prova
    ]
    print("🔌 Inizializzazione OBD (Golf 7 Profile)...")
    for cmd in comandi:
        ser.write((cmd + '\r').encode('utf-8'))
        time.sleep(0.2)
        ser.read_all()
    print("✅ Connesso. Inizio scansione...")
    time.sleep(1)

def chiedi_pid(ser, pid):
    """Richiede un PID specifico"""
    ser.write((pid + '\r').encode('utf-8'))
    time.sleep(0.08) # Ottimizzato per CAN bus veloce
    raw = ser.read_all().decode('utf-8', errors='ignore')
    return raw.replace('\r', '').replace('\n', '').replace('>', '').strip()

def interpreta_dati(pid, hex_data):
    """Applica la formula corretta in base al PID"""
    try:
        parts = hex_data.split()
        
        # Gestione risposta "NO DATA" (PID non supportato dalla Golf)
        if "NO DATA" in hex_data:
            return "UNSUPPORTED"

        # Verifica header risposta (41 + PID)
        expected_header = "41" + pid[2:]
        
        # Controllo robustezza: deve contenere l'header corretto
        if len(parts) < 3 or expected_header not in parts[0] + parts[1]:
            return None

        # Trova dove inizia la risposta dati
        try:
            if parts[0] == expected_header:
                idx = 1
            elif parts[0] + parts[1] == expected_header:
                idx = 2
            else:
                idx = parts.index(expected_header) + 1 # Fallback
        except ValueError:
            # A volte capita se la stringa è sporca
            return None

        dati = [int(x, 16) for x in parts[idx:]]
        if not dati: return None
        
        A = dati[0]
        B = dati[1] if len(dati) > 1 else 0

        # --- CALCOLO VALORE ---
        # Cerca la formula nel dizionario ed eseguila direttamente
        if pid in PID_FORMULAS:
            return PID_FORMULAS[pid](A, B)

    except Exception:
        return None
    return None

# --- MAIN LOOP ---
try:
    ser = serial.Serial(PORTA, BAUDRATE, timeout=0.5)
    init_adattatore(ser)

    print(f"{'TIMESTAMP':<15} | {'PID':<6} | {'DESCRIZIONE':<22} | {'VALORE':<15} | {'NOTE'}")
    print("-" * 80)

    while True:
        for pid_code, (descrizione, unita) in PIDS_DA_LEGGERE.items():
            
            # Se sappiamo già che la Golf non supporta questo PID, saltiamolo per velocizzare
            if pid_code in pids_non_supportati:
                continue

            raw_response = chiedi_pid(ser, pid_code)
            valore = interpreta_dati(pid_code, raw_response)
            
            if valore == "UNSUPPORTED":
                # Lo segniamo come non supportato e lo stampiamo una volta sola
                pids_non_supportati.add(pid_code)
                print(f"{'---':<15} | {pid_code:<6} | {descrizione:<22} | {'NON SUPPORTATO':<15} | NO DATA")
            
            elif isinstance(valore, (int, float)):
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                str_valore = f"{valore:.2f} {unita}"
                print(f"{timestamp:<15} | {pid_code:<6} | {descrizione:<22} | {str_valore:<15} | {raw_response}")
            
            # Piccola pausa anti-flood
            time.sleep(0.02) 

except KeyboardInterrupt:
    print("\nChiusura connessione.")
    if 'ser' in locals() and ser.is_open:
        ser.close()
except Exception as e:
    print(f"Errore critico: {e}")