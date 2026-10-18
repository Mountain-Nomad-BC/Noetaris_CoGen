"""Offline exact-member archive review; never certifies IP or authorizes publication."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from zipfile import ZipFile
import unicodedata
SECRET=re.compile(rb'(?i)(?:sk-[a-z0-9_-]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?-i:(?:AKIA|ASIA)[A-Z0-9]{16}))')
PRIVATE_PATH=re.compile(rb'(?i)(?:[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]|/home/[^/\s]+/|/Users/[^/\s]+/)')
FORBIDDEN_PARTS={'.git','.venv','__pycache__','.pytest_cache','node_modules','secrets','state','plans','evidence','attachments','rie_remy_codebase','pacify-x-main','dva_ey'}
MAX_MEMBER=15*1024*1024
MAX_TOTAL=64*1024*1024
MANIFEST='ARCHIVE_MANIFEST.json'

def member_name(name):
    if not isinstance(name,str) or '\\' in name or '\x00' in name:raise ValueError('Invalid archive member path')
    path=PurePosixPath(name)
    if path.is_absolute() or not name or any(part in {'','..','.'} for part in name.split('/')) or ':' in name:raise ValueError('Unsafe archive member path')
    reserved={'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}
    if any(part.endswith(('.', ' ')) or part.split('.')[0].casefold() in reserved for part in path.parts):raise ValueError('Windows-ambiguous or reserved archive path')
    if any(part.casefold() in FORBIDDEN_PARTS for part in path.parts) or path.name.casefold().startswith('.env'):raise ValueError('Private or excluded archive member')
    if path.suffix.casefold() in {'.gguf','.pkl','.pickle','.dump','.sql.gz','.pem','.key'}:raise ValueError('Private model/credential/database artifact excluded')
    return path.as_posix()

def audit_payloads(payloads,*,forbidden_values=()):
    seen=set();total=0;records=[]
    for name,data in payloads:
        name=member_name(name);folded=unicodedata.normalize('NFC',name).casefold()
        if folded in seen:raise ValueError('Duplicate or case-colliding archive member')
        seen.add(folded);total+=len(data)
        if len(data)>MAX_MEMBER or total>MAX_TOTAL:raise ValueError('Archive exceeds review size budget')
        if SECRET.search(data):raise ValueError('Potential secret detected in archive member: '+name)
        if PRIVATE_PATH.search(data):raise ValueError('Private absolute user path detected in archive member: '+name)
        if any(value and len(value)>=8 and value in data for value in forbidden_values):raise ValueError('Known local secret detected in archive member: '+name)
        records.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    return records

def audit_archive(path,*,expected_allowlist=None,forbidden_values=()):
    with ZipFile(path) as archive:
        infos=archive.infolist()
        if len(infos)>2000 or sum(info.file_size for info in infos)>MAX_TOTAL:raise ValueError('Archive exceeds review budget')
        if any(info.flag_bits&1 for info in infos):raise ValueError('Encrypted archive members cannot be reviewed')
        if any((info.external_attr>>16)&0o170000==0o120000 for info in infos):raise ValueError('Archive symlink member is excluded')
        payloads=[(info.filename,archive.read(info)) for info in infos]
    records=audit_payloads(payloads,forbidden_values=forbidden_values)
    manifest_payload=next((data for name,data in payloads if name==MANIFEST),None)
    if manifest_payload is None:raise ValueError('Exact archive manifest is required')
    try:manifest=json.loads(manifest_payload)
    except (ValueError,UnicodeError):raise ValueError('Invalid archive manifest') from None
    if not isinstance(manifest,dict) or manifest.get('publication_approved') is not False or manifest.get('privacy_qualification')!='offline-limited':raise ValueError('Invalid archive qualification contract')
    actual=[record for record in records if record['path']!=MANIFEST]
    if manifest.get('members')!=actual:raise ValueError('Archive member digest/size manifest mismatch')
    if expected_allowlist is not None and sorted(record['path'] for record in actual)!=sorted(expected_allowlist):raise ValueError('Archive member allowlist mismatch')
    return {'status':'PASS','scope':'exact archive membership, hashes, bounded privacy/secret patterns','members':actual,'archive_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'published':False,'publication_approved':False,'license_qualification':'not-certified','privacy_qualification':'offline-limited'}

def audit_checkout(root,*,strict=False):
    """Compatibility hygiene check; this cannot replace exact archive review."""
    root=Path(root).resolve();checked=0;errors=[]
    ignored={'.git','.venv','__pycache__','.pytest_cache','node_modules','state','evidence','plans','.mypy_cache'}
    for path in root.rglob('*'):
        if not path.is_file() or set(path.relative_to(root).parts)&ignored:continue
        name=path.relative_to(root).as_posix()
        if name.startswith('secrets/') or path.name.startswith('.env'):
            if strict and name!='secrets/.gitkeep':errors.append('Local credential artifact must be excluded: '+name)
            continue
        if path.is_symlink():errors.append('Unreviewed source symlink: '+name);continue
        if path.stat().st_size>MAX_MEMBER:errors.append('Oversize source artifact: '+name);continue
        if SECRET.search(path.read_bytes()):errors.append('Potential secret pattern: '+name)
        checked+=1
    return {'status':'FAIL' if errors else 'PASS','scope':'limited checkout credential-pattern hygiene only; NOT exact archive, privacy, license or publication clearance','checked_files':checked,'errors':errors,'publication_approved':False}

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('target',type=Path);parser.add_argument('--strict',action='store_true');args=parser.parse_args(argv)
    try:report=audit_checkout(args.target,strict=args.strict) if args.target.is_dir() else audit_archive(args.target)
    except (ValueError,OSError) as error:print('FAIL:',error);return 1
    print(json.dumps(report,indent=2));return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
