"""Optional private author-source supplements; no archive extraction or TeX execution."""
from __future__ import annotations
import argparse
from io import BytesIO
import gzip
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import subprocess
import sys
import tarfile
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES=16*1024*1024
MAX_MEMBER_BYTES=2*1024*1024
MAX_MEMBERS=128
MAX_ARTIFACT_BYTES=8*1024*1024
PARSER_IMAGE='sha256:0df1ace1c8c5ae9ec3aa8609a87bfb5ff1ff736da4bb5cb106f27271ae4236b1'

def sha(data):return hashlib.sha256(data).hexdigest()

def safe_member_path(name):
    if not isinstance(name,str) or not 1<=len(name)<=240 or any(ord(c)<32 for c in name) or '\\' in name or ':' in name:
        raise ValueError('Unsafe archive member name')
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:raise ValueError('Unsafe archive member path')
    return path

def inspect_bundle(raw):
    """Read capped member bytes in memory. Never call extract/extractall."""
    if not isinstance(raw,bytes) or not 1<=len(raw)<=MAX_ARCHIVE_BYTES:raise ValueError('Source response exceeds16MiB or is empty')
    decoded=raw;compressed=False
    if raw.startswith(b'\x1f\x8b'):
        compressed=True
        with gzip.GzipFile(fileobj=BytesIO(raw)) as stream:decoded=stream.read(MAX_ARCHIVE_BYTES+1)
        if len(decoded)>MAX_ARCHIVE_BYTES:raise ValueError('Expanded source exceeds16MiB')
    if decoded.startswith(b'%PDF-'):return dict(format='gzip_pdf' if compressed else 'pdf',files=[],member_count=0,ignored_extensions={},unsupported=['Source endpoint returned PDF, not author TeX'])
    if decoded.lstrip().lower().startswith((b'<!doctype html',b'<html')):raise ValueError('Source response is HTML, not an author source archive')
    try:archive=tarfile.open(fileobj=BytesIO(decoded),mode='r:')
    except tarfile.ReadError:
        if len(decoded)>MAX_MEMBER_BYTES:raise ValueError('Plain TeX source exceeds2MiB')
        return dict(format='gzip_plain_source' if compressed else 'plain_source',files=[dict(member_path='source.tex',basename='source.tex',data=decoded,sha256=sha(decoded))],member_count=1,ignored_extensions={},unsupported=[])
    files=[];count=0;total=0;seen=set();ignored={}
    with archive:
        for member in archive:
            count+=1
            if count>MAX_MEMBERS:raise ValueError('Archive exceeds128members')
            path=safe_member_path(member.name);normalized=path.as_posix()
            if normalized in seen:raise ValueError('Duplicate normalized archive member')
            seen.add(normalized)
            if member.isdir():continue
            if not member.isfile() or member.issym() or member.islnk():raise ValueError('Archive links/devices/nonregular members refused')
            if type(member.size) is not int or member.size<0:raise ValueError('Invalid archive member size')
            total+=member.size
            if total>MAX_ARCHIVE_BYTES:raise ValueError('Archive total member bytes exceed16MiB')
            if path.suffix.lower()!='.tex':ignored[path.suffix.lower() or '(none)']=ignored.get(path.suffix.lower() or '(none)',0)+1;continue
            if member.size>MAX_MEMBER_BYTES:raise ValueError('TeX member exceeds2MiB')
            stream=archive.extractfile(member)
            if stream is None:raise ValueError('Missing regular member content')
            with stream:data=stream.read(min(member.size,MAX_MEMBER_BYTES)+1)
            if len(data)!=member.size or len(data)>MAX_MEMBER_BYTES:raise ValueError('TeX member size/custody mismatch')
            files.append(dict(member_path=member.name,basename=path.name,data=data,sha256=sha(data)))
    return dict(format='tar_gzip' if compressed else 'tar',files=files,member_count=count,ignored_extensions=ignored,unsupported=[])

def build_supplement(raw,*,pdf_sha256,document_id,revision):
    try:from scientific_math import extract_latex_math
    except ModuleNotFoundError:from nsai.scientific_math import extract_latex_math
    bundle=inspect_bundle(raw);archive_hash=sha(raw);files=[];records=[];failures=[];complete=not bundle['unsupported']
    for entry in bundle['files']:
        metadata={k:v for k,v in entry.items() if k!='data'}
        try:
            artifact=extract_latex_math(entry['data'],entry['basename'],pdf_sha256=pdf_sha256,source_archive_sha256=archive_hash,document_id=document_id,revision=revision)
            metadata.update(status=artifact['status'],coverage=artifact['coverage'],processing_complete=artifact['processing_complete'])
            for record in artifact['records']:
                record['source']['archive_member_path']=entry['member_path']
                record['id']=sha(json.dumps(dict(extractor_record_id=record['id'],archive_member_path=entry['member_path']),sort_keys=True,separators=(',',':')).encode())
            records.extend(artifact['records']);complete &= artifact['processing_complete']
        except (ValueError,UnicodeError) as error:
            metadata.update(status='REFUSED',error_type=type(error).__name__,reason=str(error));failures.append(metadata);complete=False
        files.append(metadata)
        if len(records)>5000 or len(json.dumps(dict(records=records,files=files),ensure_ascii=False,allow_nan=False).encode())>MAX_ARTIFACT_BYTES-8192:
            raise ValueError('Aggregate author math artifact exceeds bounded record/JSON capacity; document partial')
    if not files:complete=False
    result=dict(schema_version='nsai-arxiv-author-math/1',document_id=document_id,revision=revision,pdf_sha256=pdf_sha256,
        source_archive_sha256=archive_hash,source_format=bundle['format'],source_kind='author_source_tex_not_pdf',pdf_alignment='not_verified',
        records=records,files=files,status='candidate' if complete else 'partial_candidate',processing_complete=complete,review_required=True,authority_granted=False,
        coverage=dict(archive_members=bundle['member_count'],tex_members=len(files),refused_tex_members=len(failures),ignored_extensions=bundle['ignored_extensions'],unsupported=bundle['unsupported'],exhaustive=False),
        limitations=['Supplemental author source is not proof of PDF-page equations or rendering equivalence','No filesystem extraction, includes, macro execution, typesetting or external-resource loading','Non-TeX members deliberately ignored; UTF-8 decoding never guesses other encodings','Not all PDF mathematics can be guaranteed; no symbolic/dimensional/correctness validation','Private local research only; original rights apply and redistribution is not approved'])
    if len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())>MAX_ARTIFACT_BYTES:raise ValueError('Aggregate author math JSON exceeds8MiB')
    return result

def source_identity(paper):
    revision=paper['id']
    if not isinstance(revision,str) or not re.fullmatch(r'(?:[0-9]{4}\.[0-9]{4,5}|[a-z-]+(?:\.[A-Z]{2})?/[0-9]{7})v[1-9][0-9]{0,2}',revision):raise ValueError('Versioned arXiv source identity required')
    if not isinstance(paper.get('pdf_sha256'),str) or not re.fullmatch(r'[a-f0-9]{64}',paper['pdf_sha256']):raise ValueError('Original PDF SHA256 required')
    return hashlib.sha256((revision+':'+paper['pdf_sha256']).encode()).hexdigest()[:32],revision

def isolated_supplement(archive,paper,image):
    name='nsai-arxiv-source-'+uuid4().hex[:12];owner=uuid4().hex
    document_id,revision=source_identity(paper)
    options=['docker','run','-d','--name',name,'--label','nsai.source.owner='+owner,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001','--cpus','1','--memory','384m','--pids-limit','32','--tmpfs','/tmp:rw,noexec,nosuid,size=16m',
        '--mount',f'type=bind,source={archive},target=/fixtures/source.bin,readonly','--mount',f'type=bind,source={Path(__file__).resolve()},target=/qualified/acquire_arxiv_sources.py,readonly','--mount',f'type=bind,source={ROOT / "src/nsai/scientific_math.py"},target=/qualified/scientific_math.py,readonly','--env','PYTHONPATH=/qualified','--entrypoint','python',image,'/qualified/acquire_arxiv_sources.py','--process-archive','/fixtures/source.bin','--pdf-sha256',paper['pdf_sha256'],'--document-id',document_id,'--revision',revision]
    artifact=None
    try:
        subprocess.run(options,check=True,capture_output=True,timeout=30)
        waited=subprocess.run(['docker','wait',name],check=True,capture_output=True,timeout=30)
        logs=subprocess.run(['docker','logs',name],check=True,capture_output=True,timeout=15)
        if len(logs.stdout)>MAX_ARTIFACT_BYTES:raise ValueError('Isolated source response exceeds artifact bound')
        if int(waited.stdout):
            diagnostic=json.loads(logs.stdout) if logs.stdout else {}
            raise ValueError('Isolated source refusal: '+str(diagnostic.get('error_type','unknown'))+': '+str(diagnostic.get('reason','no complete result admitted'))[:180])
        artifact=json.loads(logs.stdout)
    finally:
        inspected=subprocess.run(['docker','inspect',name],capture_output=True,timeout=15)
        if inspected.returncode==0:
            info=json.loads(inspected.stdout)[0]
            if info['Config']['Labels'].get('nsai.source.owner')!=owner:raise RuntimeError('Refused cleanup of unowned source parser')
            subprocess.run(['docker','rm','-f',name],check=True,capture_output=True,timeout=15)
            if artifact is not None:artifact['parser_qualification']=dict(image_id=image,network='none',cpu_cap=1,memory_mib=384,owned_cleanup_verified=True)
    if artifact is not None and len(json.dumps(artifact,ensure_ascii=False,allow_nan=False).encode())>MAX_ARTIFACT_BYTES:raise ValueError('Author source artifact plus parser receipt exceeds8MiB')
    return artifact

def run(manifest_path,download=False):
    from download_arxiv_corpus import Fetcher,paper_id,utc
    manifest_path=manifest_path.resolve();corpus=(ROOT/'data/arxiv-corpus').resolve()
    if not manifest_path.is_relative_to(corpus) or manifest_path.name!='manifest.json':raise ValueError('Expected private corpus download manifest')
    with manifest_path.open('rb') as stream:manifest_bytes=stream.read(MAX_ARTIFACT_BYTES+1)
    if len(manifest_bytes)>MAX_ARTIFACT_BYTES:raise ValueError('Acquisition manifest exceeds8MiB')
    manifest=json.loads(manifest_bytes)
    if manifest.get('status')=='RUNNING':raise ValueError('PDF acquisition still running; wait before sharing arXiv requests')
    papers=manifest.get('papers',[])
    if not isinstance(papers,list) or not 1<=len(papers)<=21:raise ValueError('Expected1..21 acquired papers')
    identities=set()
    for paper in papers:
        identity=paper_id(paper['id'])
        if identity in identities:raise ValueError('Duplicate source paper')
        identities.add(identity)
        path=(manifest_path.parent/paper['pdf_relative_path']).resolve()
        if not path.is_relative_to(manifest_path.parent):raise ValueError('Original PDF path outside corpus run')
        with path.open('rb') as stream:pdf=stream.read(MAX_MEMBER_BYTES+1)
        if len(pdf)>MAX_MEMBER_BYTES or not pdf.startswith(b'%PDF-') or sha(pdf)!=paper['pdf_sha256']:raise ValueError('Original PDF custody mismatch')
    if not download:
        print(json.dumps(dict(status='PLAN_ONLY',papers=len(papers),urls=['https://arxiv.org/src/'+p['id'] for p in papers],maximum_bytes=MAX_ARCHIVE_BYTES,polite_delay_seconds=3.1)));return 0
    image=json.loads(subprocess.run(['docker','image','inspect',PARSER_IMAGE],capture_output=True,check=True,timeout=15).stdout)[0]['Id']
    destination=manifest_path.parent/'author-sources';destination.mkdir(exist_ok=False)
    events=[];fetcher=Fetcher(events,delay=3.1);fetcher.last_end=time.monotonic();receipt=dict(status='RUNNING',requested_papers=len(papers),papers=[],fetches=events,parser_image=image,manifest_sha256=sha(manifest_bytes),script_sha256=sha(Path(__file__).read_bytes()),math_module_sha256=sha((ROOT/'src/nsai/scientific_math.py').read_bytes()),rights='Private supplemental originals; no redistribution approval')
    def save():(destination/'manifest.json').write_text(json.dumps(receipt,indent=2,allow_nan=False),encoding='utf-8')
    save()
    for paper in papers:
        entry=dict(id=paper['id'],pdf_sha256=paper['pdf_sha256'],status='ATTEMPTED');receipt['papers'].append(entry)
        safe_id=paper['id'].replace('/','_');folder=destination/safe_id;folder.mkdir()
        try:
            url='https://arxiv.org/src/'+paper['id'];raw,final=fetcher.fetch(url,MAX_ARCHIVE_BYTES)
            if final!=url:raise ValueError('Source redirect changed exact versioned URL')
            archive=folder/'original-source.bin';archive.write_bytes(raw);entry.update(source_archive_sha256=sha(raw),source_bytes=len(raw),archive_relative_path=archive.relative_to(destination).as_posix())
            artifact=isolated_supplement(archive,paper,image);target=folder/'formulas-author-source.json';target.write_text(json.dumps(artifact,ensure_ascii=False,allow_nan=False),encoding='utf-8')
            entry.update(status=artifact['status'],processing_complete=artifact['processing_complete'],formula_candidates=len(artifact['records']),artifact_sha256=sha(target.read_bytes()),artifact_relative_path=target.relative_to(destination).as_posix(),coverage=artifact['coverage'])
        except Exception as error:
            entry.update(status='REFUSED_OR_FETCH_FAILED',error_type=type(error).__name__,reason=str(error)[:240] if isinstance(error,ValueError) else 'Operation failed; private command diagnostics are not published',http_status=getattr(error,'code',None));save()
            if getattr(error,'code',None) in {403,429}:break
        save();print(json.dumps(dict(id=entry['id'],status=entry['status'],formula_candidates=entry.get('formula_candidates'))),flush=True)
    unchanged=receipt['script_sha256']==sha(Path(__file__).read_bytes()) and receipt['math_module_sha256']==sha((ROOT/'src/nsai/scientific_math.py').read_bytes())
    receipt.update(status='CANDIDATES_ACQUIRED' if unchanged and len(receipt['papers'])==len(papers) and all(p.get('processing_complete') for p in receipt['papers']) else 'PARTIAL',source_bindings_unchanged=unchanged,unattempted_papers=len(papers)-len(receipt['papers']),completed_at=utc(),polite_fetch_spacing_verified=all(e['gap_after_previous_end_seconds'] is None or e['gap_after_previous_end_seconds']>=3 for e in events));save()
    print(json.dumps(dict(status=receipt['status'],papers=len(receipt['papers']),candidate_records=sum(p.get('formula_candidates',0) for p in receipt['papers']))));return 0 if receipt['status']=='CANDIDATES_ACQUIRED' else 1

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path);parser.add_argument('--download',action='store_true');parser.add_argument('--process-archive',type=Path,help=argparse.SUPPRESS);parser.add_argument('--pdf-sha256');parser.add_argument('--document-id');parser.add_argument('--revision');args=parser.parse_args()
    if args.process_archive:
        with args.process_archive.open('rb') as stream:raw=stream.read(MAX_ARCHIVE_BYTES+1)
        try:result=build_supplement(raw,pdf_sha256=args.pdf_sha256,document_id=args.document_id,revision=args.revision)
        except (ValueError,tarfile.TarError,EOFError,OSError) as error:
            print(json.dumps(dict(refused=True,error_type=type(error).__name__,reason=str(error)[:240])));return 2
        print(json.dumps(result,ensure_ascii=False,allow_nan=False));return 0
    if args.manifest is None:parser.error('--manifest is required')
    return run(args.manifest,args.download)

if __name__=='__main__':raise SystemExit(main())
