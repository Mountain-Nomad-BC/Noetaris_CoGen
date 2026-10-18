"""Render a private Compute Engine Compose bundle; never provision or publish.

Registry digests and Linux artifact locations must be supplied explicitly.
The original release gate remains authoritative and is never synthesized.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
from uuid import uuid4

from start_integration import ROOT,STATE
from check_release_readiness import validate,source_snapshot


def render(source,config):
    required={'project_id','zone','images','model_file','encoder_directory'}
    if not isinstance(config,dict) or set(config)!=required:
        raise ValueError('Google configuration requires project_id, zone, images and Linux model paths')
    project=config['project_id']
    if not isinstance(project,str) or re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]',project) is None:
        raise ValueError('Invalid Google project ID')
    if not isinstance(config['zone'],str) or re.fullmatch(r'[a-z]+-[a-z]+[0-9]+-[a-z]',config['zone']) is None:
        raise ValueError('Invalid Google zone')
    images=config['images']
    if not isinstance(images,dict) or set(images)!={'api','ui','db','encoder','model'}:
        raise ValueError('Five explicit registry image digests are required')
    for value in images.values():
        if not isinstance(value,str) or re.fullmatch(r'[a-z0-9-]+-docker\.pkg\.dev/'+re.escape(project)+r'/[a-z0-9_./-]+@sha256:[a-f0-9]{64}',value) is None:
            raise ValueError('Exact Artifact Registry project/image digests are required')
    for key in ('model_file','encoder_directory'):
        value=config[key]
        if (not isinstance(value,str) or not value.startswith('/srv/noetaris/models/') or
            '..' in PurePosixPath(value).parts or '\\' in value or any(ord(c)<32 for c in value)):
            raise ValueError('Linux model paths must be inside /srv/noetaris/models')
    expected={'api','ui','db','parser','encoder','llama-cpp'}
    if source.get('name')!='noetaris-integration' or set(source.get('services',{}))!=expected:
        raise ValueError('Owned six-service integration template required')
    result=copy.deepcopy(source);result['name']='noetaris-cloud'
    roles={'api':'api','parser':'api','ui':'ui','db':'db','encoder':'encoder','llama-cpp':'model'}
    for service,key in roles.items():
        result['services'][service]['image']=images[key]
        result['services'][service]['pull_policy']='missing'
    for name in result['secrets']:
        if re.fullmatch(r'[a-z_]+',name) is None:raise ValueError('Invalid template secret identity')
        result['secrets'][name]={'file':'/etc/noetaris/secrets/'+name}
    result['services']['llama-cpp']['volumes'][0]['source']=config['model_file']
    result['services']['encoder']['volumes'][0]['source']=config['encoder_directory']
    result['services']['ui']['ports']=['127.0.0.1:8790:8080']
    result['volumes']['integration_data']['labels']={'nsai.scope':'cloud-owned-data'}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    args=parser.parse_args()
    try:
        compose_bytes=(STATE/'compose.json').read_bytes()
        identity=json.loads((STATE/'identity.json').read_text())
        if identity.get('project')!='noetaris-integration' or identity.get('compose_sha256')!=hashlib.sha256(compose_bytes).hexdigest():
            raise ValueError('Integration source identity does not match Compose bytes')
        rendered=render(json.loads(compose_bytes),json.loads(args.config.read_text()))
    except (OSError,ValueError,TypeError):
        print(json.dumps(dict(status='CONFIGURATION_REQUIRED',cloud_resources_modified=False,
            reason='Supply valid project/zone, five exact Artifact Registry digests and Linux model paths'),indent=2))
        return 2
    folder=ROOT/'state/google-deployment'/uuid4().hex;folder.mkdir(parents=True)
    encoded=(json.dumps(rendered,indent=2)+'\n').encode()
    (folder/'compose.json').write_bytes(encoded)
    gate=validate()
    report=dict(status='NOT_READY',bundle_kind='private Compute Engine preparation only',
        cloud_resources_modified=False,images_pushed=False,credentials_copied=False,data_exported=False,
        compose_sha256=hashlib.sha256(encoded).hexdigest(),
        source_runtime_images=identity['images'],
        required_model={key:identity[key] for key in ['model_id','model_sha256','model_architecture']},
        source_snapshot_sha256=hashlib.sha256(json.dumps(source_snapshot(ROOT),sort_keys=True).encode()).hexdigest(),
        release_gate=gate['status'],release_findings=len(gate['errors']),
        required_secret_names=sorted(rendered['secrets']),
        remaining=['Authenticated registry digest/image qualification and model-byte transfer verification',
                   'Cloud IAM, private networking, certificate/OIDC identity commissioning',
                   'Owned database migration/backup/restore commissioning on the target',
                   'Two external database service identities, roles and adapters',
                   'Evolus and AMD workflow/allowance/export/dispatch commissioning',
                   'Independent security, rights and release admission'])
    (folder/'preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],bundle=str(folder),release_gate=gate['status']),indent=2))
    return 2


if __name__=='__main__':raise SystemExit(main())
