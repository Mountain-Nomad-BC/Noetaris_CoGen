"""Owned PostgreSQL credential rehearsal. Never defaults to production or live secrets."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import psycopg
ROOT=Path(__file__).resolve().parents[1]
OWNER_VALUES={'implementation','qualification','implementation/qualification'}

class RotationCancelled(RuntimeError):pass
class RotationRecoveryError(RuntimeError):pass

def credential(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,256}',value):raise ValueError('Credential requires 32-256 ASCII URL-safe characters')
    return value

def bounded_secret(path,root=None):
    original_root=Path(root or ROOT/'evidence/implementation/tempCredentials').absolute()
    for component in [original_root,*original_root.parents]:
        if component.is_symlink() or (hasattr(component,'is_junction') and component.is_junction()):raise ValueError('Owned credential workspace must not traverse links')
    root=original_root.resolve();path=Path(path).absolute()
    if not path.is_relative_to(root):raise ValueError('Rotation secret must be inside the explicitly owned fixture workspace')
    for component in [path,*path.parents]:
        if component.is_symlink() or (hasattr(component,'is_junction') and component.is_junction()):raise ValueError('Rotation secret path must not traverse links')
        if component==root:break
    path=path.resolve(strict=True)
    if not path.is_relative_to(root):raise ValueError('Resolved rotation secret escaped owned fixture workspace')
    if not path.is_file() or path.stat().st_size>4096:raise ValueError('Rotation secret must be a bounded existing regular file')
    raw=path.read_bytes()
    if not raw.endswith(b'\n'):raise ValueError('Credential fixture must contain one LF-terminated line')
    raw=raw[:-1]
    if b'\r' in raw or b'\n' in raw:raise ValueError('Credential file requires one LF-terminated line')
    return credential(raw.decode('ascii'))

def require_private_file(path):
    """Check the owned staged file and its parent without changing live ACLs."""
    path=Path(path)
    if os.name!='nt':
        for candidate in [path,path.parent]:
            info=candidate.stat()
            if info.st_uid!=os.getuid() or info.st_mode&0o077:raise ValueError('Staged credentials require owner-only file/directory permissions')
        return
    environment=os.environ.copy();environment['NSAI_ROTATION_ACL_PATH']=str(path)
    command="$ErrorActionPreference='Stop';$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value;foreach($path in @($env:NSAI_ROTATION_ACL_PATH,(Split-Path -Parent $env:NSAI_ROTATION_ACL_PATH))){$acl=Get-Acl -LiteralPath $path;if($acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -ne $sid){exit 2};$rules=@($acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier]));if(@($rules|Where-Object{$_.IdentityReference.Value -notin @($sid,'S-1-5-18') -or $_.AccessControlType -ne 'Allow'}).Count -ne 0){exit 3};if(@($rules.IdentityReference.Value|Select-Object -Unique).Count -ne 2){exit 4}}"
    result=subprocess.run(['powershell','-NoProfile','-Command',command],env=environment,capture_output=True,text=True,timeout=15)
    if result.returncode:raise ValueError('Staged credential file and parent require current-account/SYSTEM-only DACL')

def atomic_credential(path,value):
    value=credential(value);path=Path(path)
    with tempfile.NamedTemporaryFile(prefix='.rotation-',dir=path.parent,delete=False) as stream:
        temporary=Path(stream.name);stream.write((value+'\n').encode('ascii'));stream.flush();os.fsync(stream.fileno())
    try:
        if os.name!='nt':temporary.chmod(0o600)
        os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)

def rotate_transaction(*,secret_path,new_secret,set_database_password,verify_login,ensure_quiescent,phase=lambda _:None,read_secret=None):
    """Compensated change with verified rollback; dependency admission stays closed."""
    old=credential(read_secret() if read_secret else bounded_secret(secret_path));new=credential(new_secret)
    if Path(secret_path).read_bytes()!=(old+'\n').encode('ascii'):raise ValueError('Original credential file must be the exact LF-terminated staged value')
    initial_stat=Path(secret_path).stat()
    initial_fingerprint=(initial_stat.st_dev,initial_stat.st_ino,initial_stat.st_mtime_ns,initial_stat.st_size,initial_stat.st_ctime_ns)
    if old==new:raise ValueError('Replacement credential must differ')
    ensure_quiescent();verify_login(old);changed=False;events=[]
    def checkpoint(name):events.append(name);phase(name)
    try:
        checkpoint('dependencies-quiescent')
        changed=True;set_database_password(new);checkpoint('database-changed')
        verify_login(new);checkpoint('replacement-login-verified')
        ensure_quiescent();atomic_credential(secret_path,new);checkpoint('file-replaced')
        if Path(secret_path).read_bytes()!=(new+'\n').encode():raise ValueError('Credential file verification failed')
        verify_login(new);checkpoint('settled')
    except BaseException as error:
        if changed:
            try:
                ensure_quiescent();set_database_password(old);atomic_credential(secret_path,old);verify_login(old)
                if Path(secret_path).read_bytes()!=(old+'\n').encode():raise ValueError('Rollback file mismatch')
                events.append('rollback-verified')
            except BaseException:raise RotationRecoveryError('Rotation failed and rollback requires manual recovery; dependents must remain stopped') from None
        raise error
    final_stat=Path(secret_path).stat()
    return {'status':'PASS','phases':events,'credential_file_sha256':hashlib.sha256(Path(secret_path).read_bytes()).hexdigest(),'pool_fingerprint_changed':initial_fingerprint!=(final_stat.st_dev,final_stat.st_ino,final_stat.st_mtime_ns,final_stat.st_size,final_stat.st_ctime_ns),'scope':'owned stopped-dependency rehearsal; no production rotation admitted'}

def docker_json(arguments):
    result=subprocess.run(['docker',*arguments],capture_output=True,text=True,timeout=30,check=True)
    return json.loads(result.stdout)

def owned_target(name):
    if not re.fullmatch(r'nsai-rotation-[a-z0-9-]{8,80}',name):raise ValueError('Explicit owned nsai-rotation target name required')
    details=docker_json(['inspect',name])[0];labels=details.get('Config',{}).get('Labels') or {}
    if labels.get('nsai.owner') not in OWNER_VALUES or labels.get('nsai.rotation')!='fixture-only':raise ValueError('Target does not carry required owned fixture labels')
    if not details.get('State',{}).get('Running'):raise ValueError('Owned PostgreSQL target must be running')
    return details

def require_quiescent(name):
    details=owned_target(name)
    for network in details['NetworkSettings']['Networks']:
        info=docker_json(['network','inspect',network])[0]
        if (info.get('Labels') or {}).get('nsai.owner') not in OWNER_VALUES:raise ValueError('Rotation target network is not owned')
        for container_id in (info.get('Containers') or {}):
            if container_id!=details['Id'] and docker_json(['inspect',container_id])[0]['State']['Running']:raise ValueError('Dependent container is running; reject rotation until stopped')
    return details

@dataclass
class PostgreSQLRotation:
    container:str
    role:str
    administrator_role:str
    administrator_secret:str
    database:str='postgres'
    def connection(self,password,role):
        details=owned_target(self.container)
        ports=details['NetworkSettings']['Ports'].get('5432/tcp') or []
        if len(ports)!=1 or ports[0]['HostIp']!='127.0.0.1':raise ValueError('Fixture requires one loopback-only PostgreSQL port')
        return psycopg.connect(host='127.0.0.1',port=int(ports[0]['HostPort']),dbname=self.database,user=role,password=password,connect_timeout=5,options='-c statement_timeout=5000')
    def set_password(self,password):
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',self.role) or self.role==self.administrator_role:raise ValueError('Validated non-administrator role required')
        with self.connection(self.administrator_secret,self.administrator_role) as conn:
            conn.execute("SELECT set_config('nsai.rotation.role',%s,true),set_config('nsai.rotation.password',%s,true)",(self.role,credential(password)))
            conn.execute("DO $$ BEGIN EXECUTE format('ALTER ROLE %I LOGIN PASSWORD %L',current_setting('nsai.rotation.role'),current_setting('nsai.rotation.password')); END $$")
    def verify(self,password):
        with self.connection(credential(password),self.role) as conn:
            if conn.execute('SELECT current_user').fetchone()[0]!=self.role:raise ValueError('Login identity mismatch')

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--target-container',required=True);parser.add_argument('--role',required=True);parser.add_argument('--administrator-role',required=True);parser.add_argument('--administrator-secret-file',required=True,type=Path);parser.add_argument('--secret-file',required=True,type=Path);parser.add_argument('--replacement-file',required=True,type=Path);args=parser.parse_args(argv)
    try:
        require_quiescent(args.target_container)
        for path in [args.administrator_secret_file,args.secret_file,args.replacement_file]:
            bounded_secret(path);require_private_file(path)
        adapter=PostgreSQLRotation(args.target_container,args.role,args.administrator_role,bounded_secret(args.administrator_secret_file))
        report=rotate_transaction(secret_path=args.secret_file,new_secret=bounded_secret(args.replacement_file),set_database_password=adapter.set_password,verify_login=adapter.verify,ensure_quiescent=lambda:require_quiescent(args.target_container))
    except RotationRecoveryError:print('FAIL: rollback could not be verified; dependent applications must remain stopped and manual recovery is required.');return 2
    except (Exception,KeyboardInterrupt):print('FAIL: credential rehearsal rejected or verified rollback completed. No live credentials were selected.');return 1
    print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
