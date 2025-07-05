import sys
import socket
import json
import logging
import ssl
import os
import urllib.parse
import time

THREAD_POOL_PORT = 8885
PROCESS_POOL_PORT = 8889

SERVER_HOSTS = ['172.16.16.101', 'localhost', '127.0.0.1']
server_address = ('localhost', THREAD_POOL_PORT) 


def detect_active_server():
    """Auto-detect which server is currently running"""
    global server_address

    print("Auto-detecting active server...")
    
    for host in SERVER_HOSTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  
            result = sock.connect_ex((host, THREAD_POOL_PORT))
            sock.close()
            if result == 0:
                server_address = (host, THREAD_POOL_PORT)
                print(f"✓ Thread Pool Server detected on {host}:{THREAD_POOL_PORT}")
                return "Thread Pool"
        except Exception as e:
            pass

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  
            result = sock.connect_ex((host, PROCESS_POOL_PORT))
            sock.close()
            if result == 0:
                server_address = (host, PROCESS_POOL_PORT)
                print(f"✓ Process Pool Server detected on {host}:{PROCESS_POOL_PORT}")
                return "Process Pool"
        except Exception as e:
            pass

    # No server found
    print("✗ No active server detected on any host")
    for host in SERVER_HOSTS:
        print(f"  - {host}:{THREAD_POOL_PORT} (Thread Pool): Not responding")
        print(f"  - {host}:{PROCESS_POOL_PORT} (Process Pool): Not responding")
    print("\nPlease start one of the servers first:")
    print("  python server_thread_pool_http.py")
    print("  python server_process_pool_http.py")
    print("\nNote: If running in Docker, make sure server is running on mesin1")
    return None


def make_socket(destination_address='localhost', port=8885):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Increased timeout for cross-container communication
        server_addr = (destination_address, port)
        logging.warning(f"connecting to {server_addr}")
        sock.connect(server_addr)
        return sock
    except Exception as ee:
        logging.warning(f"error {str(ee)}")
        return None


def make_secure_socket(destination_address='localhost', port=10000):
    try:
        # get it from https://curl.se/docs/caextract.html

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_verify_locations(os.getcwd() + '/domain.crt')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        secure_socket = context.wrap_socket(sock, server_hostname=destination_address)
        logging.warning(secure_socket.getpeercert())
        return secure_socket
    except Exception as ee:
        logging.warning(f"error {str(ee)}")
        return None


def send_command(command_str, is_secure=False):
    alamat_server = server_address[0]
    port_server = server_address[1]

    if is_secure == True:
        sock = make_secure_socket(alamat_server, port_server)
    else:
        sock = make_socket(alamat_server, port_server)

    if sock is None:
        return False

    try:
        logging.warning(f"sending message ")
        sock.sendall(command_str.encode())
        logging.warning(command_str)
        # Look for the response, waiting until socket is done (no more data)
        data_received = ""  # empty string
        timeout_count = 0
        while True:
            # socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            try:
                sock.settimeout(5)  # 5 second timeout per recv
                data = sock.recv(2048)
                if data:
                    # data is not empty, concat with previous content
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    # no more data, stop the process by break
                    break
                timeout_count = 0  # Reset timeout count on successful recv
            except socket.timeout:
                timeout_count += 1
                if timeout_count > 3:  # Max 3 timeouts (15 seconds total)
                    logging.warning("Connection timeout after multiple attempts")
                    break
                continue
                
        # at this point, data_received (string) will contain all data coming from the socket
        hasil = data_received
        logging.warning("data received from server:")
        sock.close()
        return hasil
    except Exception as ee:
        logging.warning(f"error during data receiving {str(ee)}")
        try:
            sock.close()
        except:
            pass
        return False


def list_directory():
    """List files in the server directory"""
    cmd = "GET /listdir HTTP/1.1\r\nHost: localhost\r\n\r\n"
    return send_command(cmd)


def upload_file(filename, content):
    """Upload a file to the server"""
    encoded_filename = urllib.parse.quote(filename)
    cmd = f"POST /upload/{encoded_filename} HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(content)}\r\n\r\n{content}\r\n"
    return send_command(cmd)


def delete_file(filename):
    """Delete a file from the server"""
    encoded_filename = urllib.parse.quote(filename)
    cmd = f"DELETE /delete/{encoded_filename} HTTP/1.1\r\nHost: localhost\r\n\r\n"
    return send_command(cmd)


def show_client_menu():
    server_type = "Thread Pool" if server_address[1] == THREAD_POOL_PORT else "Process Pool"
    host_info = "mesin1" if server_address[0] == '172.16.16.101' else server_address[0]
    print(f"\n=== HTTP Client Operations ({server_type} Server: {host_info}:{server_address[1]}) ===")
    print("1. List Directory")
    print("2. Upload File")
    print("3. Delete File")
    print("4. Test Connection")
    print("5. Re-detect Server")
    print("6. Exit")
    print("===============================")


def start_client_ui():
    global server_address

    detected_server = detect_active_server()
    if detected_server is None:
        print("Exiting...")
        return

    while True:
        show_client_menu()
        choice = input("Select operation (1-6): ").strip()

        if choice == '1':
            print("Listing directory...")
            result = list_directory()
            if result:
                print("Server response:")
                print(result)
            else:
                print("Failed to get directory listing")

        elif choice == '2':
            filename = input("Enter filename to upload: ").strip()
            if not filename:
                print("Invalid filename")
                continue
            content = input("Enter file content: ").strip()
            print(f"Uploading file '{filename}'...")
            result = upload_file(filename, content)
            if result:
                print("Server response:")
                print(result)
            else:
                print("Failed to upload file")

        elif choice == '3':
            filename = input("Enter filename to delete: ").strip()
            if not filename:
                print("Invalid filename")
                continue
            print(f"Deleting file '{filename}'...")
            result = delete_file(filename)
            if result:
                print("Server response:")
                print(result)
            else:
                print("Failed to delete file")

        elif choice == '4':
            print("Testing connection...")
            cmd = "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
            result = send_command(cmd)
            if result:
                print("Connection successful!")
                print("Server response:")
                print(result)
            else:
                print("Connection failed")

        elif choice == '5':
            detected_server = detect_active_server()
            if detected_server is None:
                print("No server detected. Please start a server first.")

        elif choice == '6':
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please select 1-6.")


#> GET / HTTP/1.1
#> Host: www.its.ac.id
#> User-Agent: curl/8.7.1
#> Accept: */*
#>

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Original behavior for script execution
        cmd = f"""GET /rfc/rfc2616.txt HTTP/1.1
Host: www.ietf.org
User-Agent: myclient/1.1
Accept: */*

"""
        hasil = send_command(cmd, is_secure=True)
        print(hasil)
    else:
        # New interactive UI with auto-detection
        start_client_ui()