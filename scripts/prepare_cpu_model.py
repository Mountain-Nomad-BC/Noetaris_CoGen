"""Verify a pre-existing GGUF by mandatory digest; never copy or license weights."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import struct
from contextlib import nullcontext
ROOT=Path(__file__).resolve().parents[1]

def original_model_path(value):
    path=Path(value).expanduser().absolute()
    for candidate in [path,*path.parents]:
        if candidate.is_symlink() or (hasattr(candidate,'is_junction') and candidate.is_junction()):
            raise ValueError('Model path and parents must not be symlinks or junctions')
    resolved=path.resolve(strict=True)
    if not resolved.is_file():raise ValueError('Model path must identify a regular existing file')
    return resolved

def gguf_metadata(path):
    """Bounded, data-only GGUF header inspection. No model execution or pickle."""
    consumed=0
    with (nullcontext(path) if hasattr(path,'read') else Path(path).open('rb')) as stream:
        def read(length):
            nonlocal consumed
            if length<0 or consumed+length>16*1024*1024:raise ValueError('GGUF metadata exceeds inspection budget')
            data=stream.read(length);consumed+=length
            if len(data)!=length:raise ValueError('Truncated GGUF metadata')
            return data
        def unpack(fmt):return struct.unpack('<'+fmt,read(struct.calcsize('<'+fmt)))[0]
        def string():
            length=unpack('Q')
            if length>1024*1024:raise ValueError('GGUF metadata string exceeds budget')
            return read(length).decode('utf-8')
        scalar={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
        def value(kind,depth=0):
            if kind in scalar:return unpack(scalar[kind])
            if kind==8:return string()
            if kind==9:
                if depth:raise ValueError('Nested GGUF arrays are unsupported')
                element,count=unpack('I'),unpack('Q')
                if count>1000000:raise ValueError('GGUF metadata array exceeds budget')
                for _ in range(count):value(element,depth+1)
                return {'array_count':count,'element_type':element}
            raise ValueError('Unsupported GGUF metadata type')
        if read(4)!=b'GGUF':raise ValueError('Not a GGUF artifact')
        version=unpack('I')
        if version not in {2,3}:raise ValueError('Unsupported GGUF format version')
        tensors,fields=unpack('Q'),unpack('Q')
        if fields>4096 or tensors>100000:raise ValueError('GGUF header count exceeds budget')
        selected={};seen=set()
        allowed={'general.name','general.architecture','general.basename','general.size_label','general.file_type','general.quantization_version','general.license','general.license.name','general.license.link','general.source.url'}
        for _ in range(fields):
            key=string()
            if key in seen:raise ValueError('Duplicate GGUF metadata key')
            seen.add(key);item=value(unpack('I'))
            if key in allowed and isinstance(item,(str,int,bool)):selected[key]=item
        return {'format_version':version,'tensor_count':tensors,'metadata_fields':fields,'inspection_bytes':consumed,'declared':selected}

def verify_model(path,expected):
    if not isinstance(expected,str) or not re.fullmatch('[a-fA-F0-9]{64}',expected):raise ValueError('NSAI_GGUF_SHA256 must be an explicit 64-character SHA256 digest')
    model=original_model_path(path)
    with model.open('rb') as stream:
        before=os.fstat(stream.fileno())
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=expected.lower():raise ValueError('Model digest mismatch')
        stream.seek(0);metadata=gguf_metadata(stream)
        after=os.fstat(stream.fileno())
        if (before.st_ino,before.st_dev,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_dev,after.st_size,after.st_mtime_ns):raise ValueError('Model changed during verification')
    declared=metadata['declared']
    return {'status':'PASS','artifact_verification':'sha256-and-bounded-gguf-header','artifact_id':'sha256:'+digest,'model_file_name':model.name,'sha256':digest,'bytes':before.st_size,'metadata':metadata,'runtime':'llama.cpp CPU-only','weights_bundled':False,'cpu_gpu_layers':0,'license':declared.get('general.license') or declared.get('general.license.name'),'license_status':'artifact-declared-unreviewed' if declared.get('general.license') or declared.get('general.license.name') else 'unknown','redistribution_approved':False,'publication_approved':False}

def require_gemma(report):
    architecture=report.get('metadata',{}).get('declared',{}).get('general.architecture')
    if not isinstance(architecture,str) or re.fullmatch(r'gemma[0-9]*(?:n)?',architecture) is None:
        raise ValueError('CPU deployment requires a hash-verified Gemma GGUF architecture')
    return report


def main():
    try:
        report=require_gemma(verify_model(os.environ.get('NSAI_GGUF_PATH',''),os.environ.get('NSAI_GGUF_SHA256')))
    except (ValueError,OSError,UnicodeError,struct.error):
        print('FAIL: model verification requires an existing nonsymlink GGUF with mandatory matching digest and a bounded Gemma architecture header. No license or deployment approval granted.')
        return 1
    target=ROOT/'evidence/raw/cpu-model-provenance.json';target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        try:historical=json.loads(target.read_text())
        except (OSError,ValueError):historical={}
        if historical.get('sha256')==report['sha256'] and historical.get('license'):
            report['historical_license_declaration']={'value':historical['license'],'status':'historical-unreviewed','source':'previous exact-digest receipt'}
    target.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(report,indent=2,allow_nan=False));return 0

if __name__=='__main__':raise SystemExit(main())
