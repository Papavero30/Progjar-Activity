import os
import json
import base64
from glob import glob


class FileInterface:
    def __init__(self):
        if not os.path.exists('files/'):
            os.makedirs('files/')
        os.chdir('files/')

    def list(self, params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK', data=filelist)
        except Exception as e:
            return dict(status='ERROR', data=str(e))

    def get(self, params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return dict(status='ERROR', data='Filename cannot be empty')
            fp = open(f"{filename}", 'rb')
            isifile = base64.b64encode(fp.read()).decode()
            fp.close()
            return dict(status='OK', data_namafile=filename, data_file=isifile)
        except Exception as e:
            return dict(status='ERROR', data=str(e))
    
    def upload(self, params=[]):
        try:
            filename = params[0]
            file_content = params[1]
            if (filename == ''):
                return dict(status='ERROR', data='Filename cannot be empty')
            decoded_content = base64.b64decode(file_content)
            with open(filename, 'wb') as fp:
                fp.write(decoded_content)
                
            return dict(status='OK', data=f"{filename} uploaded successfully")
        except Exception as e:
            return dict(status='ERROR', data=str(e))
    
    def delete(self, params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return dict(status='ERROR', data='Filename cannot be empty')
            
            if not os.path.exists(filename):
                return dict(status='ERROR', data=f"File {filename} not found")
            
            os.remove(filename)
            return dict(status='OK', data=f"{filename} deleted successfully")
        except Exception as e:
            return dict(status='ERROR', data=str(e))
