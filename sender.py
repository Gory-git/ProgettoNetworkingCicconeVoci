#!/usr/bin/python3
from time import sleep
import paho.mqtt.client as mqtt
import signal
import sys

topic = "#"

# Configurazione del client MQTT
mqtt_config = {
    "broker_address": "212.227.85.109",
    "port": 8883,
    "username": "spintel",
    "password": "Sp1nt3l_2022",
}

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