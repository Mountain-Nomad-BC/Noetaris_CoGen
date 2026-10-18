"""Offline Compose policy smoke, not a substitute for docker compose config or runtime test."""
from pathlib import Path
import yaml


def main():

    root=Path(__file__).resolve().parents[1]
    compose=yaml.safe_load((root/'compose.yaml').read_text())
    gpu=yaml.safe_load((root/'deploy/amd/compose.amd.yaml').read_text())
    local=yaml.safe_load((root/'deploy/local/compose.ollama.yaml').read_text())
    cpu=yaml.safe_load((root/'deploy/local/compose.cpu.yaml').read_text())
    def merge(base, overlay):
        result=dict(base)
        for key,value in overlay.items():
            result[key]=merge(result[key],value) if isinstance(value,dict) and isinstance(result.get(key),dict) else value
        return result
    services={**merge(compose['services'],gpu['services']),**{'local_ollama':local['services']['ollama'],'llama-cpp':cpu['services']['llama-cpp']}}
    errors=[]
    for name,cfg in services.items():
        if cfg.get('privileged'):
            errors.append(f'{name}: privileged is forbidden')
        if cfg.get('network_mode')=='host':
            errors.append(f'{name}: host network is forbidden')
        if 'no-new-privileges:true' not in cfg.get('security_opt',[]):
            errors.append(f'{name}: no-new-privileges missing')
        if any('/var/run/docker.sock' in str(vol) for vol in cfg.get('volumes',[])):
            errors.append(f'{name}: Docker socket forbidden')
        for port in cfg.get('ports',[]):
            if not str(port).startswith('127.0.0.1:'):
                errors.append(f'{name}: non-loopback port publishing detected: {port}')
    if 'ports' in services['db'] or 'ports' in services['vllm'] or 'ports' in services['local_ollama']:
        errors.append('Database/inference services cannot publish host ports')
    if services['sandbox-smoke'].get('network_mode') != 'none':
        errors.append('Sandbox smoke must have network_mode none')
    if not services['api'].get('read_only') or 'ALL' not in services['api'].get('cap_drop',[]):
        errors.append('API read_only/cap_drop baseline missing')
    if not compose['networks']['data_net'].get('internal'):
        errors.append('Data network not private')
    if not compose['networks']['parser_net'].get('internal') or services['parser'].get('networks')!=['parser_net']:
        errors.append('Parser network must be private and isolated from data/model networks')
    for name in ('api','parser','sandbox-smoke','llama-cpp'):
        cfg=services[name]
        if cfg.get('user')!='10001:10001' or not cfg.get('read_only') or cfg.get('cap_drop')!=['ALL']:
            errors.append(f'{name}: nonroot/readonly/drop-all controls required')
        if not cfg.get('pids_limit') or not cfg.get('mem_limit') or not cfg.get('cpus'):
            errors.append(f'{name}: process/memory/CPU limits required')
    if services['parser'].get('secrets')!=['parser_token']:
        errors.append('Parser must receive only its dedicated authentication secret')
    if services['llama-cpp'].get('networks')!=['model_net'] or not cpu['networks']['model_net'].get('internal'):
        errors.append('CPU inference must use private model network only')
    if services['llama-cpp'].get('ports') or services['llama-cpp'].get('devices'):
        errors.append('CPU inference must not publish ports or bind GPU devices')
    if not all(v.get('read_only') for v in services['llama-cpp'].get('volumes',[])):
        errors.append('CPU model mounts must be read-only')
    if 'db_password' in services['api'].get('secrets',[]):
        errors.append('Owner DB password must not be mounted in API')
    if local['services']['ollama'].get('cap_drop') != ['ALL'] or not local['services']['ollama'].get('read_only'):
        errors.append('Local Ollama must be read-only with capabilities dropped')
    if local['services']['api']['environment'].get('NSAI_MODEL_URL') != 'http://ollama:11434/v1':
        errors.append('Local API Ollama URL mismatch')
    if 'api_token' not in compose['secrets'] or 'db_password' not in compose['secrets']:
        errors.append('Required Compose secrets not declared')
    for item in errors:print('FAIL:',item)
    if errors:raise SystemExit(1)
    print('STATIC SECURITY MANIFEST CHECK PASSED (runtime verification still required)')


if __name__ == "__main__":
    main()
