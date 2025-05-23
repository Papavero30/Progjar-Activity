import socket
import json
import base64
import logging
import os

server_address = ('172.18.0.2', 8889)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message: {command_str}")
        sock.sendall((command_str + "\r\n\r\n").encode())
        data_received = ""
        while True:
            data = sock.recv(32)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = json.loads(data_received.split("\r\n\r\n")[0])
        return hasil
    except Exception as e:
        logging.error(f"Error: {e}")
        return False
    finally:
        sock.close()

def remote_list():
    command_str = "LIST"
    hasil = send_command(command_str)
    if (hasil['status'] == 'OK'):
        print("Daftar file:")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print(f"Error: {hasil['data']}")
        return False

def remote_get(filename=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if (hasil['status'] == 'OK'):
        namafile = hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        if not os.path.exists('./downloads/'):
            os.makedirs('./downloads/')
        fp = open(f'./downloads/{namafile}', 'wb+')
        fp.write(isifile)
        fp.close()
        print(f"File {namafile} successfully downloaded to downloads folder")
        return True
    else:
        print(f"Error: {hasil['data']}")
        return False

def remote_upload(filepath=""):
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'rb') as fp:
            file_content = base64.b64encode(fp.read()).decode()
        command_str = f"UPLOAD {filename} {file_content}"
        hasil = send_command(command_str)
        if (hasil['status'] == 'OK'):
            print(f"Success: {hasil['data']}")
            return True
        else:
            print(f"Error: {hasil['data']}")
            return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if (hasil['status'] == 'OK'):
        print(f"Success: {hasil['data']}")
        return True
    else:
        print(f"Error: {hasil['data']}")
        return False

if __name__ == '__main__':
    while True:
        print("\nFile Client Menu:")
        print("1. List files")
        print("2. Download file")
        print("3. Upload file")
        print("4. Delete file")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            remote_list()
        elif choice == '2':
            filename = input("Enter file name to download: ")
            remote_get(filename)
        elif choice == '3':
            filepath = input("Enter path to the file to upload: ")
            remote_upload(filepath)
        elif choice == '4':
            filename = input("Enter file name to delete: ")
            remote_delete(filename)
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")
