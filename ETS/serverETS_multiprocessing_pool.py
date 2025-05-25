from socket import *
import socket
import multiprocessing
import logging
import time
import sys
import os
from concurrent.futures import ProcessPoolExecutor
import signal

from protocolETS import FileProtocol

def handle_client_process(client_socket, client_address):
    """Process pool worker function to handle client connection"""
    try:
        logging.warning(f"Process {multiprocessing.current_process().pid} handling client from {client_address}")
        
        fp = FileProtocol()  # Each process has its own protocol instance
        buffer = ""
        
        while True:
            data = client_socket.recv(32)
            if data:
                d = data.decode()
                buffer += d
                if "\r\n\r\n" in buffer:
                    command = buffer.split("\r\n\r\n")[0]
                    hasil = fp.proses_string(command)
                    hasil = hasil + "\r\n\r\n"
                    client_socket.sendall(hasil.encode())
                    buffer = ""
            else:
                break
                
    except Exception as e:
        logging.error(f"Process {multiprocessing.current_process().pid} error: {e}")
    finally:
        try:
            client_socket.close()
        except:
            pass
        logging.warning(f"Process {multiprocessing.current_process().pid} closed connection from {client_address}")

class ServerMultiprocessingPool:
    def __init__(self, ipaddress='0.0.0.0', port=8889, max_workers=5):
        self.ipinfo = (ipaddress, port)
        self.max_workers = max_workers
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # We're using ProcessPoolExecutor for better process management
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        logging.warning(f"Server initialized with {max_workers} process workers")

    def run(self):
        logging.warning(f"Multiprocessing Pool Server running on {self.ipinfo} with {self.max_workers} workers")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(50)
        
        # For clean shutdown
        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGINT, original_sigint_handler)
        
        try:
            while True:
                try:
                    client_socket, client_address = self.my_socket.accept()
                    logging.warning(f"New connection from {client_address}")
                    
                    # Submit to the process pool
                    self.executor.submit(handle_client_process, client_socket, client_address)
                    
                except KeyboardInterrupt:
                    logging.warning("Received keyboard interrupt, shutting down...")
                    break
                    
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            logging.warning("Shutting down server...")
            self.executor.shutdown(wait=False)
            self.my_socket.close()
            logging.warning("Server shut down complete")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=5, help='Number of worker processes')
    parser.add_argument('--port', type=int, default=8889, help='Server port')
    args = parser.parse_args()
    
    # Set log level to warning
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Use the improved server with process pool
    svr = ServerMultiprocessingPool(ipaddress='0.0.0.0', port=args.port, max_workers=args.workers)
    svr.run()

if __name__ == "__main__":
    # This is important for multiprocessing on Windows
    multiprocessing.freeze_support()
    main()