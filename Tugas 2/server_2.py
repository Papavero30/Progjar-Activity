import sys
import socket
import logging
import threading
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def proses_request(request_string):
    balas = "ERROR\r\n"
    if request_string.startswith("TIME") and request_string.endswith("\r\n"):
        now = datetime.now()
        waktu = now.strftime("%H:%M:%S")
        balas = f"JAM {waktu}\r\n"
    elif request_string.startswith("QUIT") and request_string.endswith("\r\n"):
        balas = "XXX"
    return balas

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        logging.info(f"Processing client from {self.address}")
        buffer = ""
        try:
            while True:
                data = self.connection.recv(32)
                if not data:
                    break
                buffer += data.decode()
                while "\r\n" in buffer:
                    request_string, buffer = buffer.split("\r\n", 1)
                    request_string += "\r\n"
                    logging.info(f"received: {request_string.strip()}")
                    response = proses_request(request_string)
                    if response == "XXX":
                        logging.info("Client requested to quit")
                        self.connection.sendall("Goodbye\r\n".encode())
                        return
                    logging.info(f"sending: {response.strip()}")
                    self.connection.sendall(response.encode())
        except Exception as e:
            logging.error(f"Exception: {e}")
        finally:
            self.connection.close()
            logging.info(f"Connection from {self.address} closed")

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', 45000))
        self.my_socket.listen(5)
        logging.info("Time Server started on port 45000")
        while True:
            connection, client_address = self.my_socket.accept()
            logging.info(f"Connection from {client_address}")
            clt = ProcessTheClient(connection, client_address)
            clt.start()
            self.the_clients.append(clt)

def main():
    try:
        svr = Server()
        svr.start()
    except KeyboardInterrupt:
        logging.info("Server interrupted and shutting down.")
        sys.exit(0)

if __name__ == "__main__":
    main()
