import sys
import socket
import logging

logging.basicConfig(level=logging.INFO)

def request_time(sock):
    try:
        message = "TIME\r\n"
        logging.info(f"Requesting time with: {message.strip()}")
        sock.sendall(message.encode())
        data = sock.recv(64)
        if data:
            response = data.decode()
            logging.info(f"Received time: {response.strip()}")
            return response
        else:
            logging.warning("No response received from server.")
            return None
    except Exception as e:
        logging.error(f"Error during time request: {str(e)}")
        return None

def send_quit(sock):
    try:
        message = "QUIT\r\n"
        logging.info(f"Sending: {message.strip()}")
        sock.sendall(message.encode())
        return True
    except Exception as e:
        logging.error(f"Error sending QUIT: {str(e)}")
        return False

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('172.18.0.2', 45000)
    logging.info(f"Connecting to {server_address}")
    sock.connect(server_address)

    for i in range(3):
        response = request_time(sock)
        logging.info(f"Time request {i+1} completed")

    send_quit(sock)

except Exception as ee:
    logging.error(f"ERROR: {str(ee)}")
    sys.exit(1)

finally:
    logging.info("Closing connection")
    sock.close()
