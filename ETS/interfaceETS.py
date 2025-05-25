import os
import json
import base64
import threading
from glob import glob


class FileInterface:
    def __init__(self):
        if not os.path.exists('files/'):
            os.makedirs('files/')
        os.chdir('files/')
        self.lock = threading.Lock()  # Thread safety untuk file operations

    def list(self, params=[]):
        try:
            with self.lock:
                filelist = glob('*.*')
            return dict(status='OK', data=filelist, worker_id=threading.current_thread().ident)
        except Exception as e:
            return dict(status='ERROR', data=str(e), worker_id=threading.current_thread().ident)

    def get(self, params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return dict(status='ERROR', data='Filename cannot be empty', worker_id=threading.current_thread().ident)
            
            with self.lock:
                fp = open(f"{filename}", 'rb')
                isifile = base64.b64encode(fp.read()).decode()
                fp.close()
            
            return dict(status='OK', data_namafile=filename, data_file=isifile, worker_id=threading.current_thread().ident)
        except Exception as e:
            return dict(status='ERROR', data=str(e), worker_id=threading.current_thread().ident)
    
    def upload(self, params=[]):
        try:
            filename = params[0]
            file_content = params[1]
            if (filename == ''):
                return dict(status='ERROR', data='Filename cannot be empty', worker_id=threading.current_thread().ident)
            
            decoded_content = base64.b64decode(file_content)
            
            with self.lock:
                with open(filename, 'wb') as fp:
                    fp.write(decoded_content)
                
            return dict(status='OK', data=f"{filename} uploaded successfully", worker_id=threading.current_thread().ident)
        except Exception as e:
            return dict(status='ERROR', data=str(e), worker_id=threading.current_thread().ident)
    
    def delete(self, params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return dict(status='ERROR', data='Filename cannot be empty', worker_id=threading.current_thread().ident)
            
            with self.lock:
                if not os.path.exists(filename):
                    return dict(status='ERROR', data=f"File {filename} not found", worker_id=threading.current_thread().ident)
                
                os.remove(filename)
            
            return dict(status='OK', data=f"{filename} deleted successfully", worker_id=threading.current_thread().ident)
        except Exception as e:
            return dict(status='ERROR', data=str(e), worker_id=threading.current_thread().ident)