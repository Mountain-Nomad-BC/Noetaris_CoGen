"""Validate Docker's effective CPU profile; never approximate Compose merge semantics."""
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'api','db','parser','llama-cpp'}
DB_READY=['CMD','pg_isready','-h','127.0.0.1','-U','nsai','-d','nsai']
def validate(config):
    errors=[]
    services=config.get('services',{})
    if set(services)!=EXPECTED: errors.append('unexpected or missing active services')
    if services.get('db',{}).get('healthcheck',{}).get('test')!=DB_READY:
        errors.append('db: final TCP readiness probe required')
    for name,cfg in services.items():
        if cfg.get('privileged') or cfg.get('network_mode')=='host': errors.append(name+': forbidden privilege/network')
        if 'no-new-privileges:true' not in cfg.get('security_opt',[]): errors.append(name+': no-new-privileges missing')
        if any('/docker.sock' in str(m.get('target','')) for m in cfg.get('volumes',[])): errors.append(name+': Docker socket forbidden')
        if not cfg.get('pids_limit') or not cfg.get('mem_limit') or float(cfg.get('cpus',0))<=0: errors.append(name+': resource limits missing')
        for port in cfg.get('ports',[]):
            if name!='api' or port.get('host_ip')!='127.0.0.1': errors.append(name+': forbidden published port')
        if name in {'api','parser','llama-cpp'} and (cfg.get('user')!='10001:10001' or not cfg.get('read_only') or cfg.get('cap_drop')!=['ALL']): errors.append(name+': confinement missing')
    for name,network,secret in [('parser','parser_net','parser_token'),('llama-cpp','model_net','model_token')]:
        cfg=services.get(name,{})
        if set(cfg.get('networks',{}))!={network}: errors.append(name+': private network isolation missing')
        if not config.get('networks',{}).get(network,{}).get('internal'): errors.append(name+': network is not internal')
        if {item.get('source') for item in cfg.get('secrets',[])}!={secret}: errors.append(name+': secret isolation missing')
    return errors

def main():
    result=subprocess.run(['docker','compose','-f','compose.yaml','-f','deploy/local/compose.cpu.yaml','config','--format','json'],cwd=ROOT,capture_output=True,text=True,timeout=30,check=True)
    errors=validate(json.loads(result.stdout))
    print(json.dumps({'status':'FAIL' if errors else 'PASS','errors':errors}))
    return int(bool(errors))
if __name__=='__main__': raise SystemExit(main())
