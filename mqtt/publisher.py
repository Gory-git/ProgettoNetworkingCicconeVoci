from datetime import time
import pub
from mqtt.pub import log_file_path
from mqtt.subscriber import inizializza

log_list = []
log_file_path = "log_b.txt"

def read_data():
    timestamp = time.time()
    dati = str(timestamp) + ""
    log_list.append(dati)

def connect():
    pub.inizializza()
    pub.run()

def send_buffer():
    if pub.client.connected_flag:
        pub.publish_from_log(log_list)
    else:
        with open("log_b.txt", "a") as log_file:
            list_old_logs = log_file.readlines()
            log_file.write(log_list)

def main():
    connect()
    read_data()
    send_buffer()


if __name__ == "__main__":
    main()