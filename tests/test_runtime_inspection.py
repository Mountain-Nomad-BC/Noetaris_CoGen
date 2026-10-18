"""Exact runtime-policy fixtures; no Docker daemon or live configuration changes."""
import copy,importlib.util,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('exact_runtime',ROOT/'scripts/inspect_runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

def fixture():
    names={'api':['data_net','app_net','parser_net','model_net'],'db':['data_net'],'parser':['parser_net'],'llama-cpp':['model_net']}
    limits={'api':(2,768*1024**2,128),'db':(1,1024**3,128),'parser':(1,384*1024**2,32),'llama-cpp':(6,8*1024**3,128)}
    config={'name':'fixture','services':{},'networks':{name:{'name':'fixture_'+name,'internal':name!='app_net'} for name in ['data_net','app_net','parser_net','model_net']},'secrets':{name:{'file':'C:/private-fixture/secrets/'+name+'.txt'} for secrets in runtime.SECRETS.values() for name in secrets},'volumes':{}}
    for name in runtime.CPU:
        cpu,memory,pids=limits[name]
        config['services'][name]={'user':'' if name=='db' else '10001:10001','read_only':name!='db','cap_drop':['NET_RAW','SYS_PTRACE','SYS_ADMIN','MKNOD'] if name=='db' else ['ALL'],'security_opt':['no-new-privileges:true'],'cpus':cpu,'mem_limit':memory,'pids_limit':pids,'logging':{'driver':'json-file','options':{'max-size':'5m','max-file':'3'}},'networks':{network:{} for network in names[name]},'secrets':[{'source':secret} for secret in sorted(runtime.SECRETS[name])],'tmpfs':[] if name=='db' else ['/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777'],'restart':'unless-stopped','init':name!='db','environment':copy.deepcopy(runtime.FILES[name])}
        if name=='api':config['services'][name]['ports']=[{'target':8787,'published':'18787','host_ip':'127.0.0.1','protocol':'tcp'}]
    expected=runtime.expected_policy(config)
    containers=[]
    for name,policy in expected.items():
        mounts=[{'Type':item['type'],'Destination':destination,'RW':not item['readonly'],'Source':item['source_identity']} for destination,item in policy['mounts'].items()]
        host={'Privileged':False,'NetworkMode':'fixture_'+names[name][0],'ReadonlyRootfs':policy['readonly'],'CapDrop':list(policy['cap_drop']),'SecurityOpt':list(policy['security_opt']),'Memory':policy['memory'],'NanoCpus':policy['nano_cpus'],'PidsLimit':policy['pids_limit'],'Init':policy['init'],'RestartPolicy':{'Name':policy['restart']},'PortBindings':copy.deepcopy(policy['ports']),'Tmpfs':{} if name=='db' else {'/tmp':'rw,nosuid,nodev,noexec,size=67108864,mode=1777'},'LogConfig':{'Type':'json-file','Config':{'max-size':'5m','max-file':'3'}}}
        containers.append({'Id':'fixture-'+name,'Image':'sha256:'+'a'*64,'State':{'Running':True,'Health':{'Status':'healthy'}},'Config':{'User':policy['user'],'Labels':{'com.docker.compose.service':name},'Env':['PRIVATE_CONTEXT=PRIVATE_ENV_SENTINEL','NSAI_CENTRAL_SECURITY_ENABLED=false']+[key+'='+value for key,value in policy['credential_files'].items()]},'HostConfig':host,'Mounts':mounts,'NetworkSettings':{'Networks':{network:{} for network in policy['networks']}}})
    networks={item['name']:{'Internal':item['internal']} for item in config['networks'].values()}
    return config,expected,containers,networks

def api(containers):return next(item for item in containers if item['Config']['Labels']['com.docker.compose.service']=='api')

def test_exact_policy_passes_and_redacts_environment_and_host_paths():
    config,expected,containers,networks=fixture();report=runtime.inspect_policy(expected,containers,networks)
    assert report['status']=='PASS'
    text=json.dumps(report)
    assert 'PRIVATE_ENV_SENTINEL' not in text and 'private-fixture' not in text
    assert report['environment_included'] is False

@pytest.mark.parametrize('key,value',[('Memory',123),('NanoCpus',1),('PidsLimit',0),('ReadonlyRootfs',False),('CapDrop',[]),('CapAdd',['SYS_ADMIN']),('SecurityOpt',['seccomp=unconfined']),('Privileged',True),('NetworkMode','host'),('PidMode','host'),('IpcMode','host'),('Init',False),('Devices',[{'PathOnHost':'/dev/example'}]),('DeviceRequests',[{'Count':-1}])])
def test_individual_effective_host_drift_fails(key,value):
    config,expected,containers,networks=fixture();api(containers)['HostConfig'][key]=value
    assert runtime.inspect_policy(expected,containers,networks)['status']=='FAIL'

@pytest.mark.parametrize('case',['user','published-port','foreign-network','private-network-egress','log-growth','scratch-size','scratch-exec','extra-secret','wrong-secret-source','writable-secret','inline-credential','central-enabled','missing-service','duplicate-service','swapped-role-token'])
def test_roles_ports_mounts_network_logging_and_missing_service_fail_closed(case):
    config,expected,containers,networks=fixture();target=api(containers)
    if case=='user':target['Config']['User']='0:0'
    elif case=='published-port':target['HostConfig']['PortBindings']['8787/tcp'][0]['HostIp']='0.0.0.0'
    elif case=='foreign-network':target['NetworkSettings']['Networks']['foreign_net']={}
    elif case=='private-network-egress':networks['fixture_parser_net']['Internal']=False
    elif case=='log-growth':target['HostConfig']['LogConfig']['Config']['max-file']='999'
    elif case=='scratch-size':target['HostConfig']['Tmpfs']['/tmp']='rw,nosuid,nodev,noexec,size=128m,mode=1777'
    elif case=='scratch-exec':target['HostConfig']['Tmpfs']['/tmp']='rw,nosuid,nodev,size=64m,mode=1777'
    elif case=='extra-secret':target['Mounts'].append({'Type':'bind','Source':'C:/private-fixture/unexpected','Destination':'/run/secrets/owner','RW':False})
    elif case=='wrong-secret-source':target['Mounts'][0]['Source']='C:/private-fixture/wrong'
    elif case=='writable-secret':target['Mounts'][0]['RW']=True
    elif case=='inline-credential':target['Config']['Env'].append('NSAI_API_TOKEN=PRIVATE_ENV_SENTINEL')
    elif case=='central-enabled':target['Config']['Env']=['NSAI_CENTRAL_SECURITY_ENABLED=true']
    elif case=='missing-service':containers.remove(target)
    elif case=='swapped-role-token':target['Config']['Env']=[value.replace('NSAI_ADMIN_TOKEN_FILE=/run/secrets/admin_token','NSAI_ADMIN_TOKEN_FILE=/run/secrets/api_token') for value in target['Config']['Env']]
    elif case=='duplicate-service':containers.append(copy.deepcopy(target))
    report=runtime.inspect_policy(expected,containers,networks)
    assert report['status']=='FAIL' and 'PRIVATE_ENV_SENTINEL' not in json.dumps(report)

@pytest.mark.parametrize('case',['privileged-parser-network','owner-secret-in-api','root-user','capability-addition','unbounded-logs','private-role-port','wrong-secret-target','extra-service'])
def test_selected_config_cannot_admit_weakened_role_baseline(case):
    config,_,_,_=fixture()
    if case=='privileged-parser-network':config['services']['parser']['networks']['data_net']={}
    elif case=='owner-secret-in-api':config['services']['api']['secrets'].append({'source':'db_password'})
    elif case=='root-user':config['services']['api']['user']='0:0'
    elif case=='capability-addition':config['services']['api']['cap_add']=['SYS_ADMIN']
    elif case=='unbounded-logs':config['services']['api']['logging']['options']={}
    elif case=='private-role-port':config['services']['parser']['ports']=[{'target':8788,'published':'8788','host_ip':'127.0.0.1'}]
    elif case=='wrong-secret-target':config['services']['parser']['secrets'][0]['target']='/run/secrets/db_password'
    elif case=='extra-service':config['services']['extra']={}
    with pytest.raises(ValueError):runtime.expected_policy(config)

def test_windows_engine_host_path_and_unit_normalization():
    assert runtime.host_path('/run/desktop/mnt/host/c/Private-Fixture/secrets/key.txt')==runtime.host_path('C:\\Private-Fixture\\secrets\\key.txt')
    assert runtime.size_bytes('768m')==805306368
    assert runtime.tmpfs_options('size=64m,mode=1777,noexec')==runtime.tmpfs_options('mode=01777,noexec,size=67108864')
