import json
import logging
import shlex

from interfaceNO3 import FileInterface

class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
    
    def proses_string(self, string_datamasuk=''):
        logging.warning(f"string diproses: {string_datamasuk}")
        c = shlex.split(string_datamasuk.lower())
        try:
            c_request = c[0].strip()
            logging.warning(f"memproses request: {c_request}")
            
            if c_request == 'upload':
                filename = c[1].strip()
                file_content = ' '.join(c[2:])
                return json.dumps(self.file.upload([filename, file_content]))
            else:
                params = [x for x in c[1:]]
                cl = getattr(self.file, c_request)(params)
                return json.dumps(cl)
        except Exception as e:
            logging.error(f"Error processing request: {e}")
            return json.dumps(dict(status='ERROR', data='request tidak dikenali'))
