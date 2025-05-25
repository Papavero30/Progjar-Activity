from socket import *
import socket
import threading
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor

from protocolETS import FileProtocol

class ServerThreadingPool:
    def __init__(self, ipaddress='0.0.0.0', port=8889, max_workers=5):
        self.ipinfo = (ipaddress, port)
        self.max_workers = max_workers
        self.fp = FileProtocol()
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_connections = 0
        self.stats_lock = threading.Lock()
        logging.warning(f"Server initialized with {max_workers} thread workers")

    def handle_client(self, connection, address):
        """Handle single client connection"""
        with self.stats_lock:
            self.active_connections += 1
        
        logging.warning(f"Worker {threading.current_thread().ident} handling connection from {address}")
        
        try:
            buffer = ""
            while True:
                data = connection.recv(32)
                if data:
                    d = data.decode()
                    buffer += d
                    if "\r\n\r\n" in buffer:
                        command = buffer.split("\r\n\r\n")[0]
                        hasil = self.fp.proses_string(command)
                        hasil = hasil + "\r\n\r\n"
                        connection.sendall(hasil.encode())
                        buffer = ""
                else:
                    break
        except Exception as e:
            logging.error(f"Error handling client {address}: {e}")
        finally:
            connection.close()
            with self.stats_lock:
                self.active_connections -= 1
            logging.warning(f"Connection from {address} closed")

    def run(self):
        logging.warning(f"Threading Pool Server running on {self.ipinfo} with {self.max_workers} workers")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(50)  # Increased backlog
        
        try:
            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"New connection from {client_address}")
                
                # Submit to thread pool
                self.executor.submit(self.handle_client, connection, client_address)
                
        except KeyboardInterrupt:
            logging.warning("Server shutting down...")
        finally:
            self.executor.shutdown(wait=True)
            self.my_socket.close()
    
    def get_stats(self):
        stats = self.fp.get_stats()
        with self.stats_lock:
            stats['active_connections'] = self.active_connections
        return stats

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=5, help='Number of worker threads')
    parser.add_argument('--port', type=int, default=8889, help='Server port')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    
    svr = ServerThreadingPool(ipaddress='0.0.0.0', port=args.port, max_workers=args.workers)
    svr.run()

if __name__ == "__main__":
    main()