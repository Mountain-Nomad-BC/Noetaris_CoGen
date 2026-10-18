"""Exact effective CPU runtime policy. No environment or credential values emitted."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
CPU={'api','db','parser','llama-cpp'}
SECRETS={'api':{'app_db_password','api_token','admin_token','reviewer_token','viewer_token','parser_token','model_token'},'db':{'db_password'},'parser':{'parser_token'},'llama-cpp':{'model_token'},'ocr':{'ocr_token'}}
FILES={'api':{'NSAI_DB_PASSWORD_FILE':'/run/secrets/app_db_password','NSAI_API_TOKEN_FILE':'/run/secrets/api_token','NSAI_ADMIN_TOKEN_FILE':'/run/secrets/admin_token','NSAI_REVIEWER_TOKEN_FILE':'/run/secrets/reviewer_token','NSAI_VIEWER_TOKEN_FILE':'/run/secrets/viewer_token','NSAI_PARSER_TOKEN_FILE':'/run/secrets/parser_token','NSAI_MODEL_API_KEY_FILE':'/run/secrets/model_token'},'db':{'POSTGRES_PASSWORD_FILE':'/run/secrets/db_password'},'parser':{'NSAI_PARSER_TOKEN_FILE':'/run/secrets/parser_token'},'llama-cpp':{},'ocr':{'NSAI_OCR_TOKEN_FILE':'/run/secrets/ocr_token'}}
def credential_files(environment):return {key:value for key,value in environment.items() if re.search(r'(?:PASSWORD|TOKEN|API_KEY)_FILE$',key)}
def host_path(value):
    value=str(value).replace('\\','/')
    for prefix in ('/run/desktop/mnt/host/','/host_mnt/'):
        if value.startswith(prefix):
            value=value[len(prefix):]
            if re.match(r'^[a-zA-Z]/',value):value=value[0]+':'+value[1:]
    return value.casefold().rstrip('/')
def size_bytes(value):
    if type(value) is int:return value
    match=re.fullmatch(r'(\d+)([kmgt]?)(?:b)?',str(value),re.I)
    if not match:raise ValueError('Invalid resource-size policy')
    return int(match[1])*(1024**('kmgt'.find(match[2].lower())+1) if match[2] else 1)
def caps(values):return {value.removeprefix('CAP_') for value in values or []}
def tmpfs_options(text):
    result={}
    for token in str(text).split(','):
        key,sep,value=token.partition('=')
        if key in result:raise ValueError('Duplicate tmpfs option')
        result[key]=size_bytes(value) if key=='size' else int(value,8) if key=='mode' else value if sep else True
    return result

def expected_policy(config,with_ocr=False):
    selected=CPU|({'ocr'} if with_ocr else set())
    active={name for name,item in config.get('services',{}).items() if not item.get('profiles')}
    if active!=selected:raise ValueError('Effective service set differs from selected CPU profile')
    result={}
    for name in sorted(selected):
        service=config['services'][name]
        if name!='db' and str(service.get('user',''))!=('10002:10002' if name=='ocr' else '10001:10001'):raise ValueError(name+': admitted nonroot user missing')
        if service.get('cap_add'):raise ValueError(name+': capability additions not admitted')
        expected_networks={'api':{'data_net','app_net','parser_net','model_net'}|({'ocr_net'} if with_ocr else set()),'db':{'data_net'},'parser':{'parser_net'},'llama-cpp':{'model_net'},'ocr':{'ocr_net'}}
        if set(service.get('networks',{}))!=expected_networks[name]:raise ValueError(name+': role-specific network scope differs')
        if name!='api' and service.get('ports'):raise ValueError(name+': private role must not publish ports')
        logging=service.get('logging') or {}
        if logging.get('driver')!='json-file' or size_bytes(logging.get('options',{}).get('max-size',0))<=0 or int(logging.get('options',{}).get('max-file',0))<=0:raise ValueError(name+': positive bounded logging required')
        files=FILES[name]|({'NSAI_OCR_TOKEN_FILE':'/run/secrets/ocr_token'} if name=='api' and with_ocr else {})
        if credential_files(service.get('environment',{}))!=files:raise ValueError(name+': canonical credential file bindings required')
        secret_names={item['source'] if isinstance(item,dict) else item for item in service.get('secrets',[])}
        if secret_names!=SECRETS[name]|({'ocr_token'} if name=='api' and with_ocr else set()):raise ValueError(name+': role secret policy differs from admitted baseline')
        if name!='db' and (not service.get('read_only') or caps(service.get('cap_drop'))!={'ALL'}):raise ValueError(name+': readonly/drop-all baseline missing')
        mounts={}
        for item in service.get('volumes',[]):
            source=item.get('source','');kind=item['type']
            source=config.get('volumes',{}).get(source,{}).get('name',source) if kind=='volume' else host_path(source)
            mounts[item['target']]={'type':kind,'source_identity':source,'readonly':bool(item.get('read_only',False))}
        for item in service.get('secrets',[]):
            item={'source':item} if isinstance(item,str) else item
            source=item['source'];target=item.get('target') or source
            if target not in {source,'/run/secrets/'+source}:raise ValueError(name+': canonical secret destination required')
            mounts[target if target.startswith('/') else '/run/secrets/'+target]={'type':'bind','source_identity':host_path(config['secrets'][source]['file']),'readonly':True}
        temp={}
        for value in service.get('tmpfs',[]):
            destination,sep,options=value.partition(':');temp[destination]=tmpfs_options(options if sep else '')
        ports={}
        for item in service.get('ports',[]):
            if item.get('host_ip')!='127.0.0.1':raise ValueError('Non-loopback publishing in selected profile')
            ports.setdefault(str(item['target'])+'/'+item.get('protocol','tcp'),[]).append({'HostIp':item['host_ip'],'HostPort':str(item['published'])})
        networks={config['networks'][key]['name']:bool(config['networks'][key].get('internal',False)) for key in service.get('networks',{})}
        if name in {'db','parser','llama-cpp','ocr'} and not all(networks.values()):raise ValueError(name+': private role network not internal')
        result[name]={'user':str(service.get('user','')),'readonly':bool(service.get('read_only',False)),'cap_drop':caps(service.get('cap_drop')),'cap_add':caps(service.get('cap_add')),'memory':size_bytes(service.get('mem_limit',0)),'nano_cpus':round(float(service.get('cpus',0))*1e9),'pids_limit':int(service.get('pids_limit',0)),'security_opt':set(service.get('security_opt',[])),'tmpfs':temp,'ports':ports,'networks':networks,'mounts':mounts,'logging':service.get('logging',{}),'credential_files':files,'command':service.get('command'),'init':bool(service.get('init',False)),'restart':service.get('restart','no')}
        if any(result[name][field]<=0 for field in ('memory','nano_cpus','pids_limit')):raise ValueError(name+': positive resource limits required')
    return result

def inspect_policy(expected,containers,networks):
    errors=[];items=[];by_service={}
    for data in containers:
        name=(data.get('Config',{}).get('Labels') or {}).get('com.docker.compose.service')
        if name in by_service:errors.append(str(name)+': duplicate service container')
        by_service[name]=data
    if set(by_service)!=set(expected):errors.append('Exact deployed service set mismatch')
    for name,policy in expected.items():
        data=by_service.get(name)
        if data is None:errors.append(name+': required container missing');continue
        host=data.get('HostConfig',{});configuration=data.get('Config',{});state=data.get('State',{})
        def check(condition,reason):
            if not condition:errors.append(name+': '+reason)
        check(state.get('Running') and state.get('Health',{}).get('Status')=='healthy','not running and healthy')
        check(configuration.get('User','')==policy['user'],'effective user drift')
        check(host.get('ReadonlyRootfs',False)==policy['readonly'],'readonly-root drift')
        check(not host.get('Privileged',False) and host.get('NetworkMode')!='host' and host.get('PidMode')!='host' and host.get('IpcMode')!='host','privileged/host namespace admitted')
        check(caps(host.get('CapDrop'))==policy['cap_drop'] and caps(host.get('CapAdd'))==policy['cap_add'],'capability-set drift')
        check(set(host.get('SecurityOpt') or [])==policy['security_opt'] and 'no-new-privileges:true' in (host.get('SecurityOpt') or []),'security-option drift')
        for actual,key in [('Memory','memory'),('NanoCpus','nano_cpus'),('PidsLimit','pids_limit')]:check(host.get(actual)==policy[key],actual+' differs from exact effective limit')
        check(bool(host.get('Init',False))==policy['init'],'init process drift')
        check(host.get('RestartPolicy',{}).get('Name','no')==policy['restart'],'restart policy drift')
        check(not host.get('Devices') and not host.get('DeviceRequests'),'device/GPU exposure not admitted')
        check((host.get('PortBindings') or {})==policy['ports'],'published-port drift')
        actual_temp={key:tmpfs_options(value) for key,value in (host.get('Tmpfs') or {}).items()}
        check(actual_temp==policy['tmpfs'],'tmpfs budget/flags/destination drift')
        logging=host.get('LogConfig') or {}
        check(logging.get('Type')==policy['logging'].get('driver') and logging.get('Config',{})==policy['logging'].get('options',{}),'bounded logging drift')
        actual_networks=set(data.get('NetworkSettings',{}).get('Networks',{}))
        check(actual_networks==set(policy['networks']),'network membership drift')
        for network,internal in policy['networks'].items():check(network in networks and bool(networks[network].get('Internal',False))==internal,'network internal-policy drift')
        observed={}
        for mount in data.get('Mounts',[]):
            if mount['Type']=='tmpfs':continue
            source=mount.get('Name') if mount['Type']=='volume' else host_path(mount.get('Source',''))
            destination=mount['Destination'];check(destination not in observed,'duplicate mount destination')
            observed[destination]={'type':mount['Type'],'source_identity':source,'readonly':not mount.get('RW',False)}
        check(observed==policy['mounts'],'exact role mount/secret/source drift')
        if policy['command'] is not None:check(configuration.get('Cmd')==policy['command'],'command drift')
        environment=dict(value.partition('=')[::2] for value in configuration.get('Env',[]) if '=' in value)
        check(credential_files(environment)==policy['credential_files'],'role credential-file binding drift')
        check(environment.get('NSAI_CENTRAL_SECURITY_ENABLED','false').lower()=='false','central security unexpectedly enabled')
        check(not any(value and re.search(r'(?:PASSWORD|TOKEN|API_KEY)$',key) for key,value in environment.items()),'inline credential environment not admitted')
        items.append({'service':name,'container_id':data.get('Id'),'image_id':data.get('Image'),'uid':configuration.get('User',''),'readonly':host.get('ReadonlyRootfs',False),'cap_drop':sorted(caps(host.get('CapDrop'))),'security_opt':host.get('SecurityOpt'),'privileged':host.get('Privileged',False),'pids_limit':host.get('PidsLimit'),'memory_bytes':host.get('Memory'),'nano_cpus':host.get('NanoCpus'),'mounts':[{'type':item['type'],'destination':destination,'readonly':item['readonly'],'source_id_sha256':hashlib.sha256(str(item['source_identity']).encode()).hexdigest()} for destination,item in observed.items()],'ports':host.get('PortBindings') or {},'networks':sorted(actual_networks),'tmpfs':actual_temp,'logging':logging,'health':state.get('Health',{}).get('Status','not configured')})
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'services':items,'scope':'exact selected effective CPU container policy; not source-image, exploitability, app RBAC or quality certification','environment_included':False,'secret_contents_included':False}

def docker(arguments):
    return subprocess.run(['docker',*arguments],cwd=ROOT,capture_output=True,text=True,check=True,timeout=30).stdout

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--with-ocr',action='store_true');parser.add_argument('--output',type=Path,default=ROOT/'evidence/implementation/runtime-inspection-current.json');args=parser.parse_args(argv)
    compose=['compose','-f','compose.yaml','-f','deploy/local/compose.cpu.yaml']
    if args.with_ocr:compose+=['-f','deploy/local/compose.ocr.yaml']
    try:
        config=json.loads(docker(compose+['config','--format','json']));expected=expected_policy(config,args.with_ocr)
        ids=docker(['ps','-a','--filter','label=com.docker.compose.project='+config['name'],'--format','{{.ID}}']).split()
        containers=json.loads(docker(['inspect',*ids])) if ids else []
        names={network for item in expected.values() for network in item['networks']}
        networks={record['Name']:record for record in json.loads(docker(['network','inspect',*sorted(names)]))}
        report=inspect_policy(expected,containers,networks)
        report['effective_config_sha256']=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    except (ValueError,KeyError,TypeError,OverflowError,OSError,subprocess.SubprocessError):report={'status':'FAIL','errors':['Effective configuration or runtime inspection could not be completed'],'services':[],'environment_included':False,'secret_contents_included':False}
    report['captured_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['inspector_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(report,indent=2,allow_nan=False));return 0 if report['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
