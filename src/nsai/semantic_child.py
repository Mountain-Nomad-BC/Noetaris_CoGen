"""Sequential offline encoder child. JSON-lines in/out; no source text in errors."""
import json
import os
import sys
from .semantic_encoder import LocalSemanticEncoder,PINNED_MODEL_SHA256


def emit(value):
    raw=json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()+b'\n'
    if len(raw)>2*1024*1024:raise ValueError('Encoder response frame exceeded')
    sys.stdout.buffer.write(raw);sys.stdout.buffer.flush()


def main():
    encoder=LocalSemanticEncoder(os.environ['NSAI_ENCODER_MODEL_DIR'])
    if encoder.identity['sha256']!=PINNED_MODEL_SHA256:raise ValueError('Unexpected encoder identity')
    emit(dict(status='ready',model_identity=encoder.identity))
    while True:
        raw=sys.stdin.buffer.readline(1200*1024+1)
        if not raw:return
        if len(raw)>1200*1024 or not raw.endswith(b'\n'):raise ValueError('Encoder request frame exceeded')
        try:
            from .assembly import strict_json
            request=strict_json(raw,max_bytes=1200*1024,max_items=10000,max_depth=4)
            if (not isinstance(request,dict) or set(request)!={'texts'} or
                not isinstance(request['texts'],list) or not 1<=len(request['texts'])<=8):
                raise ValueError('Invalid encoder request')
            emit(dict(status='ok',result=encoder.encode(request['texts'])))
        except Exception as error:
            emit(dict(status='error',error_type=type(error).__name__))


if __name__=='__main__':main()
