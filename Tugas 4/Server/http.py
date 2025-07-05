import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import json
import urllib.parse

class HttpServer:
	def __init__(self):
		self.sessions={}
		self.types={}
		self.types['.pdf']='application/pdf'
		self.types['.jpg']='image/jpeg'
		self.types['.txt']='text/plain'
		self.types['.html']='text/html'
	def response(self,kode=404,message='Not Found',messagebody=bytes(),headers={}):
		tanggal = datetime.now().strftime('%c')
		resp=[]
		resp.append("HTTP/1.0 {} {}\r\n" . format(kode,message))
		resp.append("Date: {}\r\n" . format(tanggal))
		resp.append("Connection: close\r\n")
		resp.append("Server: myserver/1.0\r\n")
		resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
		for kk in headers:
			resp.append("{}:{}\r\n" . format(kk,headers[kk]))
		resp.append("\r\n")

		response_headers=''
		for i in resp:
			response_headers="{}{}" . format(response_headers,i)
		#menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
		if (type(messagebody) is not bytes):
			messagebody = messagebody.encode()

		response = response_headers.encode() + messagebody
		#response adalah bytes
		return response

	def proses(self,data):
		requests = data.split("\r\n")
		#print(requests)

		baris = requests[0]
		#print(baris)

		all_headers = [n for n in requests[1:] if n!='']

		j = baris.split(" ")
		try:
			method=j[0].upper().strip()
			if (method=='GET'):
				object_address = j[1].strip()
				return self.http_get(object_address, all_headers)
			if (method=='POST'):
				object_address = j[1].strip()
				post_body = ""
				if len(requests) > 1:
					body_start = False
					for line in requests:
						if body_start:
							post_body += line + "\r\n"
						if line == "":
							body_start = True
				return self.http_post(object_address, all_headers, post_body)
			if (method=='DELETE'):
				object_address = j[1].strip()
				return self.http_delete(object_address, all_headers)
			else:
				return self.response(400,'Bad Request','',{})
		except IndexError:
			return self.response(400,'Bad Request','',{})
	def http_get(self,object_address,headers):
		files = glob('./*')
		#print(files)
		thedir='./'
		if (object_address == '/'):
			return self.response(200,'OK','Ini Adalah web Server percobaan',dict())

		if (object_address == '/video'):
			return self.response(302,'Found','',dict(location='https://youtu.be/katoxpnTf04'))
		if (object_address == '/santai'):
			return self.response(200,'OK','santai saja',dict())

		if (object_address == '/listdir'):
			return self.list_directory('./folder')

		object_address=object_address[1:]
		if thedir+object_address not in files:
			return self.response(404,'Not Found','',{})
		fp = open(thedir+object_address,'rb') #rb => artinya adalah read dalam bentuk binary
		#harus membaca dalam bentuk byte dan BINARY
		isi = fp.read()
		
		fext = os.path.splitext(thedir+object_address)[1]
		content_type = self.types[fext]
		
		headers={}
		headers['Content-type']=content_type
		
		return self.response(200,'OK',isi,headers)
	
	def http_post(self,object_address,headers, post_body=""):
		if object_address.startswith('/upload/'):
			filename = object_address[8:]  
			return self.upload_file(filename, post_body)
		
		headers ={}
		isi = "kosong"
		return self.response(200,'OK',isi,headers)
	
	def http_delete(self, object_address, headers):
		if object_address.startswith('/delete/'):
			filename = object_address[8:]  
			return self.delete_file(filename)
		
		return self.response(404,'Not Found','',{})
	
	def list_directory(self, directory_path):
		"""List files in the specified directory"""
		try:
			if not os.path.exists(directory_path):
				os.makedirs(directory_path)
			
			files = []
			for item in os.listdir(directory_path):
				item_path = os.path.join(directory_path, item)
				if os.path.isfile(item_path):
					files.append({
						'name': item,
						'size': os.path.getsize(item_path),
						'modified': os.path.getmtime(item_path)
					})
			
			response_data = json.dumps(files, indent=2)
			headers = {'Content-Type': 'application/json'}
			return self.response(200, 'OK', response_data, headers)
		
		except Exception as e:
			return self.response(500, 'Internal Server Error', str(e), {})
	
	def upload_file(self, filename, file_content):
		"""Upload a file to the folder directory"""
		try:
			folder_path = './folder'
			if not os.path.exists(folder_path):
				os.makedirs(folder_path)
			
			filename = urllib.parse.unquote(filename)
			file_path = os.path.join(folder_path, filename)
			
			with open(file_path, 'w') as f:
				f.write(file_content.strip())
			
			return self.response(200, 'OK', f'File {filename} uploaded successfully', {})
		
		except Exception as e:
			return self.response(500, 'Internal Server Error', str(e), {})
	
	def delete_file(self, filename):
		"""Delete a file from the folder directory"""
		try:
			folder_path = './folder'
			filename = urllib.parse.unquote(filename)
			file_path = os.path.join(folder_path, filename)
			
			if not os.path.exists(file_path):
				return self.response(404, 'Not Found', 'File not found', {})
			
			os.remove(file_path)
			return self.response(200, 'OK', f'File {filename} deleted successfully', {})
		
		except Exception as e:
			return self.response(500, 'Internal Server Error', str(e), {})

#>>> import os.path
#>>> ext = os.path.splitext('/ak/52.png')

if __name__=="__main__":
	httpserver = HttpServer()
	d = httpserver.proses('GET testing.txt HTTP/1.0')
	print(d)
	d = httpserver.proses('GET donalbebek.jpg HTTP/1.0')
	print(d)
	#d = httpserver.http_get('testing2.txt',{})
	#print(d)
#	d = httpserver.http_get('testing.txt')
#	print(d)















