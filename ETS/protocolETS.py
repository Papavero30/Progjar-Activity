import json
import logging
import shlex
import threading
import os

from interfaceETS import FileInterface

class FileProtocol:
    def __init__(self):
        self.file = FileInterface()
        self.stats_lock = threading.Lock()
        self.success_count = 0
        self.error_count = 0
    
    def proses_string(self, string_datamasuk=''):
        logging.warning(f"Worker {threading.current_thread().ident} - string diproses: {string_datamasuk}")
        c = shlex.split(string_datamasuk.lower())
        try:
            c_request = c[0].strip()
            logging.warning(f"Worker {threading.current_thread().ident} - memproses request: {c_request}")
            
            if c_request == 'upload':
                filename = c[1].strip()
                file_content = ' '.join(c[2:])
                result = json.dumps(self.file.upload([filename, file_content]))
            else:
                params = [x for x in c[1:]]
                cl = getattr(self.file, c_request)(params)
                result = json.dumps(cl)
            
            # Update success counter
            with self.stats_lock:
                self.success_count += 1
            
            return result
        except Exception as e:
            logging.error(f"Worker {threading.current_thread().ident} - Error processing request: {e}")
            
            # Update error counter
            with self.stats_lock:
                self.error_count += 1
            
            return json.dumps(dict(status='ERROR', data='request tidak dikenali', worker_id=threading.current_thread().ident))
    
    def get_stats(self):
        with self.stats_lock:
            return {'success': self.success_count, 'error': self.error_count}
    
    def reset_stats(self):
        with self.stats_lock:
            self.success_count = 0
            self.error_count = 0