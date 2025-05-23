import sys
import socket
import logging
import os

# Set basic logging
logging.basicConfig(level=logging.INFO)

try:
    # 1. Buat socket dan connect ke server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('172.18.0.2', 32444)
    logging.info(f"connecting to {server_address}")
    sock.connect(server_address)

    # 2. Kirim pesan teks seperti biasa
    message = 'INI ADALAH DATA YANG DIKIRIM ABCDEFGHIJKLMNOPQ'
    logging.info(f"sending {message}")
    sock.sendall(message.encode())

    # 3. Terima echo dari server untuk pesan teks
    amount_received = 0
    amount_expected = len(message)
    while amount_received < amount_expected:
        data = sock.recv(16)
        if not data:
            break
        amount_received += len(data)
        logging.info(f"{data}")

    # 4. Kirim file, jika ada
    file_path = 'file_mesin2.txt'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                sock.sendall(chunk)
        logging.info(f"File '{file_path}' sent successfully.")
    else:
        logging.warning(f"File '{file_path}' not found. Skipping file send.")

    # 5. Laporkan ke server bahwa kita selesai mengirim semua data
    sock.shutdown(socket.SHUT_WR)

    # 6. Baca semua balasan dari server (misalnya echo file)
    while True:
        data = sock.recv(32)
        if not data:
            break
        logging.info(f"{data}")

except Exception as ee:
    logging.info(f"ERROR: {str(ee)}")
    sys.exit(1)

finally:
    logging.info("closing")
    sock.close()
