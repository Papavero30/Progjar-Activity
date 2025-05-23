from socket import *
import socket
import threading
import logging
import time
import sys

from server_protocolNO3 import FileProtocol
fp = FileProtocol()

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        buffer = ""
        while True:
            data = self.connection.recv(32)
            if data:
                d = data.decode()
                buffer += d
                if "\r\n\r\n" in buffer:
                    command = buffer.split("\r\n\r\n")[0]
                    hasil = fp.proses_string(command)
                    hasil = hasil + "\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                    buffer = ""
            else:
                break
        self.connection.close()


class Server(threading.Thread):
    def __init__(self, ipaddress='0.0.0.0', port=8889):
        self.ipinfo = (ipaddress, port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning(f"connection from {self.client_address}")

            clt = ProcessTheClient(self.connection, self.client_address)
            clt.start()
            self.the_clients.append(clt)


def main():
    svr = Server(ipaddress='0.0.0.0', port=8889)
    svr.start()


if __name__ == "__main__":
    main()
