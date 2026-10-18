"""Read-only OCI template lint and canonical release gate; never starts Docker."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

from start_integration import ROOT
from check_release_readiness import validate


def inspect_profile(config,with_oauth=False):
    errors=[];services=config.get('services',{})
    if set(services)!={'api','db','encoder','parser','edge'}:errors.append('Unexpected OCI service inventory')
    for name,service in services.items():
        image=service.get('image','')
        if not isinstance(image,str) or re.fullmatch(r'[a-zA-Z0-9./_-]+(?::[0-9]+)?/[a-zA-Z0-9./_-]+@sha256:[a-f0-9]{64}',image) is None:
            errors.append(name+': exact registry digest required')
        if service.get('platform')!='linux/arm64':errors.append(name+': real ARM64 image qualification required')
        if (service.get('privileged') or service.get('cap_add') or service.get('read_only') is not True or
            'ALL' not in service.get('cap_drop',[]) or service.get('user') not in {'10001:10001','70:70','101:101'} or
            'no-new-privileges:true' not in service.get('security_opt',[])):
            errors.append(name+': privilege policy differs')
        if not service.get('mem_limit') or not service.get('cpus') or not 0<service.get('pids_limit',0)<=128:
            errors.append(name+': resource bounds missing')
        ports=service.get('ports',[])
        if name!='edge' and ports:errors.append(name+': internal port published')
        if name=='edge' and (len(ports)!=1 or str(ports[0].get('published'))!='443' or ports[0].get('target')!=8443):
            errors.append('Only the HTTPS edge port may be published')
        for mount in service.get('volumes',[]):
            if isinstance(mount,str):socket='/var/run/docker.sock' in mount.split(':')
            elif isinstance(mount,dict):socket=mount.get('target')=='/var/run/docker.sock' or mount.get('source')=='/var/run/docker.sock'
            else:errors.append(name+': invalid mount declaration');socket=False
            if socket:
                errors.append('Docker socket must not enter containers')
    environment=services.get('api',{}).get('environment',{})
    if any(name in environment for name in ['NSAI_API_TOKEN','NSAI_API_TOKEN_FILE','NSAI_ADMIN_TOKEN_FILE','NSAI_REVIEWER_TOKEN_FILE','NSAI_VIEWER_TOKEN_FILE']):
        errors.append('Shared local role credentials are not production identity')
    if with_oauth and any(environment.get('NSAI_OAUTH_'+provider+'_ENABLED')!='true' for provider in ['GOOGLE','GITHUB']):
        errors.append('Both registered OAuth providers must be enabled for this production profile')
    nets=config.get('networks',{})
    if any(v.get('internal',False) is not (name not in {'front','oauth_egress'}) for name,v in nets.items()):errors.append('Internal network isolation differs')
    for name,service in services.items():
        attached=set(service.get('networks',{}))
        if name!='api' and 'oauth_egress' in attached:errors.append(name+': unauthorized OAuth egress network')
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path,required=True)
    parser.add_argument('--with-oauth',action='store_true')
    args=parser.parse_args()
    command=['docker','compose','--project-name','noetaris-oci','--env-file',str(args.env_file),'-f',str(ROOT/'deploy/oci/compose.yaml')]
    if args.with_oauth:
        for provider in ['google','github']:command+=['-f',str(ROOT/('deploy/oci/compose.oauth-'+provider+'.yaml'))]
    errors=[]
    try:
        result=subprocess.run(command+['config','--format','json'],capture_output=True,timeout=30)
        if result.returncode:raise ValueError('Explicit OCI configuration is incomplete')
        errors=inspect_profile(json.loads(result.stdout),args.with_oauth)
    except (OSError,ValueError,TypeError,subprocess.SubprocessError):errors=['Explicit OCI configuration is incomplete or invalid']
    gate=validate()
    report=dict(status='DENY' if errors or gate['status']!='ADMITTED' else 'CONFIGURATION_CHECKED',
        release_gate=gate['status'],findings=len(gate['errors']),configuration_errors=errors,
        physical_arm64_and_live_provider_acceptance_not_established_by_this_check=True,
        cloud_resources_modified=False)
    print(json.dumps(report,indent=2))
    return 0 if not errors and gate['status']=='ADMITTED' else 2


if __name__=='__main__':raise SystemExit(main())
