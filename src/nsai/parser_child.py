"""Fixed parser program, never generated code; OS limits complement container limits."""
import base64
import json
import sys
from .ingestion import parse_source, MAX_PARSER_OUTPUT_BYTES
from .upload_limits import ACTIVE

if sys.platform == 'linux':
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
payload = json.loads(sys.stdin.buffer.read(ACTIVE.request_bytes+1))
result = parse_source(base64.b64decode(payload['data'], validate=True), payload['filename'])
encoded = json.dumps(result, ensure_ascii=False).encode('utf-8')
if len(encoded) > MAX_PARSER_OUTPUT_BYTES:
    raise ValueError('Parser output exceeds envelope budget')
sys.stdout.buffer.write(encoded)
