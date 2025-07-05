from socket import *
import socket
import time
import sys
import logging
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection,address):
		rcv=""
		while True:
			try:
				data = connection.recv(1024)  # Increased buffer size for file uploads
				if data:
					#merubah input dari socket (berupa bytes) ke dalam string
					#agar bisa mendeteksi \r\n
					d = data.decode()
					rcv=rcv+d
					if rcv[-2:]=='\r\n':
						#end of command, proses string
						#logging.warning("data dari client: {}" . format(rcv))
						hasil = httpserver.proses(rcv)
						#hasil akan berupa bytes
						#untuk bisa ditambahi dengan string, maka string harus di encode
						hasil=hasil+"\r\n\r\n".encode()
						#logging.warning("balas ke  client: {}" . format(hasil))
						#hasil sudah dalam bentuk bytes
						connection.sendall(hasil)
						rcv=""
						connection.close()
						return
				else:
					break
			except OSError as e:
				pass
		connection.close()
		return

def Server(port=8885):
	the_clients = []
	my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	my_socket.bind(('0.0.0.0', port))
	my_socket.listen(1)
	
	print(f"Thread Pool HTTP Server running on port {port}")
	total_requests = 0

	with ThreadPoolExecutor(20) as executor:
		while True:
				connection, client_address = my_socket.accept()
				total_requests += 1
				print(f"Request #{total_requests} from {client_address}")
				
				p = executor.submit(ProcessTheClient, connection, client_address)
				the_clients.append(p)
				
				running_futures = [i for i in the_clients if i.running()]
				done_futures = [i for i in the_clients if i.done()]
				
				print(f"Thread Status - Running: {len(running_futures)}, Done: {len(done_futures)}")
				
				the_clients = [i for i in the_clients[-100:] if not i.done()]

def main():
	port = 8885
	if len(sys.argv) > 1:
		try:
			port = int(sys.argv[1])
		except:
			pass
	Server(port)

if __name__=="__main__":
	main()

