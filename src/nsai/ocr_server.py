"""Private, single-job OCR HTTP service; no database/model authorization."""
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import threading
import tempfile
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .ingestion import MAX_PARSER_OUTPUT_BYTES
from .upload_limits import ACTIVE

_job=threading.BoundedSemaphore(1)

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)
    def log_message(self,*args):pass  # No source paths/payloads or bearer material.
    def _reply(self,status,body):
        encoded=json.dumps(body,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(encoded)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers();self.wfile.write(encoded)
    def do_GET(self):
        self._reply(200 if self.path=='/healthz' else 404,{'status':'alive'} if self.path=='/healthz' else {'error':'Unknown route'})
    def do_POST(self):
        if self.path!='/ocr':self._reply(404,{'error':'Unknown route'});return
        try:
            expected=Path(os.environ['NSAI_OCR_TOKEN_FILE']).read_text(encoding='utf-8').strip()
            authorization=self.headers.get('Authorization','')
            if len(expected)<32:raise ValueError('Invalid service configuration')
            if len(authorization)>512 or not authorization.isascii() or not secrets.compare_digest(authorization,'Bearer '+expected):
                self._reply(401,{'error':'Unauthorized'});return
            if self.headers.get('Transfer-Encoding'):
                self._reply(400,{'error':'Transfer encoding unsupported'});return
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=ACTIVE.request_bytes:self._reply(413,{'error':'Input budget exceeded'});return
            if not _job.acquire(blocking=False):self._reply(429,{'error':'OCR busy'});return
            try:
                self.connection.settimeout(5)
                data=self.rfile.read(length)
                if len(data)!=length:raise ValueError('Incomplete request')
                payload=json.loads(data)
                if not isinstance(payload,dict) or set(payload)-{'filename','data','language'} or not isinstance(payload.get('filename'),str) or len(payload['filename'])>180 or not isinstance(payload.get('data'),str):
                    raise ValueError('Invalid OCR request')
                with tempfile.TemporaryFile() as output,tempfile.TemporaryFile() as errors:
                    process=subprocess.Popen([sys.executable,'-m','nsai.ocr_worker'],stdin=subprocess.PIPE,stdout=output,stderr=errors,start_new_session=True,
                        env={'PATH':'/usr/bin:/bin','PYTHONPATH':os.environ.get('PYTHONPATH',''),'PYTHONDONTWRITEBYTECODE':'1','OMP_THREAD_LIMIT':'1','NSAI_UPLOAD_PROFILE':ACTIVE.profile})
                    try:
                        process.communicate(data,timeout=125)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid,signal.SIGKILL)
                        process.wait()
                        raise
                    if process.returncode or output.tell()>MAX_PARSER_OUTPUT_BYTES or errors.tell()>65536:
                        self._reply(422,{'error':'OCR refused within safety limits'});return
                    output.seek(0)
                    self._reply(200,json.load(output))
            finally:_job.release()
        except subprocess.TimeoutExpired:
            self._reply(422,{'error':'OCR job deadline exceeded'})
        except (ValueError,OSError,KeyError,json.JSONDecodeError):
            self._reply(422,{'error':'OCR refused within safety limits'})

if __name__=='__main__':
    server=ThreadingHTTPServer(('0.0.0.0',8091),Handler)
    server.daemon_threads=True
    server.serve_forever()
