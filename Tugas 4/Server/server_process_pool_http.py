from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer
import threading

# Shared counter for active tasks
active_task_count = 0
task_lock = threading.Lock()

# Function untuk worker process yang akan dijalankan dalam ProcessPoolExecutor
def ProcessTheClient(request_data, client_address):
    """
    Function untuk memproses client dalam process pool
    Menerima data request sebagai string karena socket object tidak bisa di-pass ke worker process
    """
    global active_task_count
    
    try:
        # Import dan create HttpServer instance di dalam worker process
        from http import HttpServer
        httpserver = HttpServer()
        
        rcv = request_data
        if rcv[-2:] == '\r\n':
            # Process the request
            hasil = httpserver.proses(rcv)
            # hasil sudah berupa bytes dari httpserver.proses()
            hasil = hasil + "\r\n\r\n".encode()
            return hasil
        else:
            # Invalid request format
            error_response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
            return error_response.encode()
            
    except Exception as e:
        # Return error response jika terjadi error
        error_response = f"HTTP/1.0 500 Internal Server Error\r\n\r\nServer Error: {str(e)}"
        return error_response.encode()

def Server(port=8889):
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    my_socket.bind(('0.0.0.0', port))
    my_socket.listen(1)
    
    print(f"Process Pool HTTP Server running on port {port}")
    total_requests = 0

    with ProcessPoolExecutor(20) as executor:
        while True:
            try:
                connection, client_address = my_socket.accept()
                total_requests += 1
                print(f"Request #{total_requests} from {client_address}")
                
                # Read request data dari client di main process
                rcv = ""
                while True:
                    try:
                        data = connection.recv(1024)  # Increased buffer size for file uploads
                        if data:
                            # merubah input dari socket (berupa bytes) ke dalam string
                            # agar bisa mendeteksi \r\n
                            d = data.decode()
                            rcv = rcv + d
                            if rcv[-2:] == '\r\n':
                                # end of command, kirim ke worker process
                                break
                        else:
                            break
                    except OSError as e:
                        break
                
                if rcv:
                    # Extract method and path for logging
                    request_line = rcv.split('\r\n')[0] if '\r\n' in rcv else rcv.strip()
                    
                    # Submit processing ke worker process
                    print(f"Submitting to worker: {request_line}")
                    p = executor.submit(ProcessTheClient, rcv, client_address)
                    the_clients.append(p)
                    
                    # Get result dari worker process dan kirim response
                    try:
                        start_time = time.time()
                        hasil = p.result(timeout=10)  # 10 second timeout
                        process_time = time.time() - start_time
                        print(f"Worker completed in {process_time:.4f} seconds")
                        
                        connection.sendall(hasil)
                    except Exception as e:
                        print(f"Worker error: {e}")
                        # Send error response jika worker process gagal
                        error_response = "HTTP/1.0 500 Internal Server Error\r\n\r\nServer Error"
                        connection.sendall(error_response.encode())
                
                connection.close()
                
                # Enhanced monitoring
                running_futures = [i for i in the_clients if i.running()]
                done_futures = [i for i in the_clients if i.done()]
                pending_futures = [i for i in the_clients if not i.done() and not i.running()]
                
                print(f"Status - Running: {len(running_futures)}, Done: {len(done_futures)}, Pending: {len(pending_futures)}")
                
                # Clean up completed futures (keep last 100 for monitoring)
                the_clients = [i for i in the_clients[-100:] if not i.done()]
                
            except Exception as e:
                print(f"Error in main server loop: {e}")
                try:
                    connection.close()
                except:
                    pass
                continue

def main():
    port = 8889
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    Server(port)

if __name__=="__main__":
    main()

