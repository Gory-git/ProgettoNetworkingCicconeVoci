#!/usr/bin/python3
import paho.mqtt.client as mqtt
import ssl
import signal
import sys

topic = "Networking/5g/vehicles"

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


def log_message(message):
    with open('log.txt', 'a') as log_file:
        log_file.write(message)
        log_file.flush()

# Callback quando si riceve un messaggio
def on_message(client, userdata, message):
    msg = f"Topic: {message.topic}\nMessage: {message.payload.decode()}\n"
    print(msg)
    log_message(msg)

# Callback quando si connette
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    client.subscribe(topic)

def inizializza():
    client.tls_set_context(tls_context)
    client.username_pw_set(mqtt_config["username"], mqtt_config["password"])
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_config["broker_address"], mqtt_config["port"])

def stop(signum, frame):
    print("Terminazione in corso...")
    client.loop_stop()
    client.disconnect()
    sys.exit(0)

# Imposta il gestore per la terminazione del programma
signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

if __name__ == "__main__":
    inizializza()
    client.loop_forever()