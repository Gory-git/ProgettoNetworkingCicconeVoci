#!/usr/bin/python3
from time import sleep
import paho.mqtt.client as mqtt
import ssl

topic = "#"

# Configurazione del client MQTT
mqtt_config = {
    "broker_address": "212.227.85.109",
    "port": 8883,
    "username": "spintel",
    "password": "Sp1nt3l_2022",
    "tls_certfile": "certs/client.crt",
    "tls_keyfile": "certs/client.key",
}

# Configurazione del contesto SSL per il supporto TLS
tls_context = ssl.create_default_context()
tls_context.check_hostname = False
tls_context.verify_mode = ssl.CERT_NONE
tls_context.load_cert_chain(certfile=mqtt_config["tls_certfile"], keyfile=mqtt_config["tls_keyfile"])

# Creazione del client MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Funzione di callback quando si riceve un messaggio
def on_message(client, userdata, message):
    print(f"Topic: {message.topic}\nMessage: {message.payload.decode()}\n")


def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    # Subscrive nel caso di riconnessione, se necessario
    client.subscribe(topic)


# Funzione per pubblicare un messaggio su un topic specifico
def publish_message(client, message, topic):
    result = client.publish(topic, message)
    status = result.rc
    if status == mqtt.MQTT_ERR_SUCCESS:
        print(f"✅ Messaggio '{message}' inviato al topic '{topic}'")
    else:
        print(f"❌ Errore nell'inviare il messaggio '{message}' al topic '{topic}'")


def set_topic(topic_new):
    global topic
    topic = topic_new

def inizializza():
    # Imposta il contesto TLS
    client.tls_set_context(tls_context)

    # Imposta le credenziali
    client.username_pw_set(mqtt_config["username"], mqtt_config["password"])

    # Imposta i callback
    client.on_connect = on_connect
    client.on_message = on_message

    # Connessione al broker MQTT
    client.connect(mqtt_config["broker_address"], mqtt_config["port"])


# Funzione per leggere il file di log e inviare i messaggi MQTT
def publish_from_log(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                # Suddividi il topic e il messaggio
                try:
                    topic_prefix, message = line.split(':', 1)
                    topic = f"sumo/{topic_prefix}"

                    publish_message(client, topic, message)

                    # Pausa di 1 secondo tra i messaggi
                    sleep(1)

                except ValueError:
                    print(f"❌ Riga non valida nel file di log: {line}")

    except FileNotFoundError:
        print(f"❌ File non trovato: {file_path}")
    except Exception as e:
        print(f"❌ Errore durante la lettura del file: {e}")

def run():
    # Esegui il client in modalità non bloccante
    client.loop_start()

# Percorso del file di log
log_file_path = 'log.txt'  # Sostituisci con il percorso reale del tuo file di log
# publish_from_log(log_file_path)

# Termina il loop del client dopo la pubblicazione
def stop():
    client.loop_stop()
    client.disconnect()