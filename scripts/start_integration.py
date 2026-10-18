"""Start the isolated synthetic-data integration stack, never the release stack.

Uses fresh project-owned credentials and a separate database volume. Release
launchers and their independent admission requirements remain unchanged.
"""
import hashlib
import argparse
import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import time
from datetime import datetime,timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'state/integration'
PROJECT = 'noetaris-integration'


def run(args, *, body=None, timeout=120):
    # Windows text-mode pipes rewrite LF SQL into CRLF, changing stored
    # function bodies and correctly failing the exact access-definition check.
    payload = body.encode('utf-8') if isinstance(body, str) else body
    result = subprocess.run(args, cwd=ROOT, input=payload, capture_output=True,
                            timeout=timeout)
    if result.returncode:
        # SQL can contain credentials. Never forward command diagnostics.
        raise RuntimeError('Integration command failed: ' + ' '.join(args[:3]))
    return result.stdout.decode('utf-8').strip()


def image(tag):
    return run(['docker', 'image', 'inspect', '--format', '{{.Id}}', tag])


def load_gemma_config(path):
    config=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(config,dict) or set(config)!={'model_id','artifact_path','sha256'}:
        raise ValueError('Gemma config requires model_id, artifact_path and sha256')
    model_id=config['model_id']
    if not isinstance(model_id,str) or not model_id.lower().startswith(('gemma','google/gemma')):
        raise ValueError('Integration target requires an explicitly selected Gemma model')
    digest=config['sha256']
    if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Gemma artifact requires an exact SHA-256')
    artifact=config['artifact_path']
    if not isinstance(artifact,str) or not Path(artifact).is_absolute():
        raise ValueError('Gemma artifact_path must be absolute')
    return config


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-config',type=Path,required=True,
                        help='Private JSON selecting model_id, absolute artifact_path and sha256 for Gemma CPU')
    parser.add_argument('--model-memory',choices=['4g','6g','8g'],default='6g',
                        help='Bounded CPU inference container memory limit')
    args=parser.parse_args()
    selection=load_gemma_config(args.model_config)
    model=Path(selection['artifact_path'])
    if not model.is_file():
        raise ValueError('Declared Gemma file missing')
    with model.open('rb') as stream:
        model_digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if model_digest!=selection['sha256']:
        raise ValueError('Gemma model bytes do not match declared digest')
    # Verify data-only GGUF metadata as well as its label and hash. Renaming a
    # different architecture must not turn it into an admitted Gemma artifact.
    from prepare_cpu_model import gguf_metadata
    metadata=gguf_metadata(model)
    architecture=metadata['declared'].get('general.architecture','')
    if not isinstance(architecture,str) or not architecture.startswith('gemma'):
        raise ValueError('Selected GGUF is not a Gemma architecture')
    STATE.mkdir(parents=True, exist_ok=True)
    private = STATE / 'secrets'
    private.mkdir(exist_ok=True)
    for name in ('db', 'app_db', 'operator', 'reviewer', 'admin', 'viewer', 'parser', 'model', 'encoder'):
        path = private / (name + '.txt')
        if not path.exists():
            with path.open('x', encoding='ascii') as stream:
                stream.write(secrets.token_hex(32))
    api_image = image('noetaris-api:candidate-20261017')
    db_image = image('noetaris-db:candidate-20261017')
    ui_image = image('noetaris-ui:candidate-20261017')
    encoder_image = image('noetaris-encoder:candidate-20261017')
    # Bind the commissioned local provider bytes, rather than resolving a tag remotely.
    model_image = image('ghcr.io/ggml-org/llama.cpp:server@sha256:89f180f16f295ee496fe00924ec2118cae2efec519d1a82c605420af09d2a6df')
    def hardened(reference, memory='768m', user='10001:10001'):
        return dict(image=reference, pull_policy='never', init=True, restart='unless-stopped',
                    user=user, read_only=True, cap_drop=['ALL'],
                    security_opt=['no-new-privileges:true'], pids_limit=128,
                    cpus=2, mem_limit=memory,
                    tmpfs=['/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777'],
                    logging=dict(driver='json-file', options={'max-size':'5m','max-file':'3'}))
    def health(port):
        return dict(test=['CMD','python','-c',f"import urllib.request; urllib.request.urlopen('http://127.0.0.1:{port}/healthz',timeout=3)"],
                    interval='5s',timeout='4s',retries=12,start_period='15s')
    db = hardened(db_image, '1024m', '70:70')
    db.update(environment={'POSTGRES_USER':'nsai','POSTGRES_DB':'nsai',
                           'POSTGRES_PASSWORD_FILE':'/run/secrets/db','PGDATA':'/var/lib/postgresql/data/pgdata'},
              secrets=['db'],volumes=['integration_data:/var/lib/postgresql/data'],
              networks=['data'],healthcheck=dict(test=['CMD','pg_isready','-h','127.0.0.1','-U','nsai','-d','nsai'],interval='5s',timeout='3s',retries=15))
    db['tmpfs'].append('/var/run/postgresql:rw,nosuid,nodev,size=8m,mode=1777')
    parser = hardened(api_image, '384m')
    parser.update(command=['uvicorn','nsai.parser:app','--host','0.0.0.0','--port','8788','--no-access-log'],
                  environment={'NSAI_PARSER_TOKEN_FILE':'/run/secrets/parser'},secrets=['parser'],
                  networks=['parser'],healthcheck=health(8788))
    provider = hardened(model_image, args.model_memory)
    provider['cpus']=4
    provider.update(command=['-m','/models/model.gguf','--alias','nsai-local-gemma','--host','0.0.0.0','--port','8080',
                             '--ctx-size','8192','--parallel','1','--threads','4','--n-gpu-layers','0',
                             '--no-ui','--no-agent','--no-slots','--api-key-file','/run/secrets/model','--timeout','120'],
                    secrets=['model'],networks=['model'],
                    volumes=[dict(type='bind',source=model.as_posix(),target='/models/model.gguf',read_only=True,bind={'create_host_path':False})],
                    healthcheck=dict(test=['CMD','curl','-f','http://127.0.0.1:8080/health'],interval='5s',timeout='3s',retries=30,start_period='60s'))
    api = hardened(api_image)
    api.update(environment={'NSAI_PUBLIC_DEMO':'true','NSAI_GENERATIONS_PER_DAY':'100','NSAI_DB_HOST':'db','NSAI_DB_NAME':'nsai','NSAI_DB_USER':'nsai_app',
                            'NSAI_DB_PASSWORD_FILE':'/run/secrets/app_db','NSAI_API_TOKEN_FILE':'/run/secrets/operator',
                            'NSAI_REVIEWER_TOKEN_FILE':'/run/secrets/reviewer','NSAI_ADMIN_TOKEN_FILE':'/run/secrets/admin',
                            'NSAI_VIEWER_TOKEN_FILE':'/run/secrets/viewer','NSAI_PARSER_TOKEN_FILE':'/run/secrets/parser',
                            'NSAI_PARSER_URL':'http://parser:8788','NSAI_CENTRAL_SECURITY_ENABLED':'false',
                            'NSAI_MODEL_URL':'http://llama-cpp:8080/v1','NSAI_MODEL_NAME':'nsai-local-gemma',
                            'NSAI_MODEL_PROVIDER':'local-llamacpp-cpu','NSAI_MODEL_API_KEY_FILE':'/run/secrets/model',
                            'NSAI_MODEL_CONTEXT_TOKENS':'8192','NSAI_OPERATION_COORDINATION':'true',
                            'NSAI_MODEL_ANSWER_STRATEGY':'source-selection',
                            'NSAI_ENCODER_URL':'http://encoder:8092','NSAI_ENCODER_TOKEN_FILE':'/run/secrets/encoder',
                            'NSAI_INDEX_WORKER_ENABLED':'true','NSAI_INDEX_CONCURRENCY':'1'},
               secrets=['app_db','operator','reviewer','admin','viewer','parser','model','encoder'],
               networks=['data','parser','model','edge','encoder'],healthcheck=health(8787))
    api['healthcheck']['test'][-1]=api['healthcheck']['test'][-1].replace('/healthz','/readyz')
    encoder = hardened(encoder_image, '768m')
    encoder.update(environment={'NSAI_ENCODER_MODEL_DIR':'/models','NSAI_ENCODER_TOKEN_FILE':'/run/secrets/encoder'},
        secrets=['encoder'],networks=['encoder'],healthcheck=health(8092),
        volumes=[dict(type='bind',source=(ROOT/'state/models/all-MiniLM-L6-v2').as_posix(),target='/models',read_only=True,bind={'create_host_path':False})])
    ui = hardened(ui_image,'128m','101:101')
    ui.update(networks=['edge','front'],ports=['127.0.0.1:8790:8080'],
              healthcheck=dict(test=['CMD','wget','-q','-O','/dev/null','http://127.0.0.1:8080/'],interval='5s',timeout='3s',retries=12))
    partner_secrets={}
    for partner in ('evolus','amd','openrouter'):
        key_path=ROOT/'secrets'/(partner+'_api_key.txt')
        if key_path.is_file():
            name='partner_'+partner
            partner_secrets[name]=dict(file=key_path.as_posix())
            api['secrets'].append(name)
            api['environment']['NSAI_'+partner.upper()+'_API_KEY_FILE']='/run/secrets/'+name
    evolus_config=STATE/'evolus.json'
    if evolus_config.is_file():
        # Invalid binding files fail before replacing the current configuration.
        import sys
        sys.path.insert(0,str(ROOT/'src'))
        from nsai.integrations.configuration import evolus_configuration
        evolus_configuration(evolus_config)
        partner_secrets['evolus_bindings']=dict(file=evolus_config.as_posix())
        api['secrets'].append('evolus_bindings')
        api['environment']['NSAI_EVOLUS_CONFIG_FILE']='/run/secrets/evolus_bindings'
    config = dict(name=PROJECT,services={'db':db,'parser':parser,'llama-cpp':provider,'api':api,'ui':ui,'encoder':encoder},
                  secrets={p.stem:dict(file=p.as_posix()) for p in private.glob('*.txt')},
                  volumes={'integration_data':{'labels':{'nsai.scope':'synthetic-integration'}}},
                  networks={n:dict(internal=n!='front') for n in ['data','parser','model','edge','front','encoder']})
    config['secrets'].update(partner_secrets)
    target = STATE / 'compose.json'
    target.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    compose=['docker','compose','--project-name',PROJECT,'-f',str(target)]
    run(compose+['up','-d','--wait','db'],timeout=120)
    database = run(compose+['ps','-q','db'])
    label = run(['docker','inspect','--format','{{index .Config.Labels "com.docker.compose.project"}}',database])
    mounts = json.loads(run(['docker','inspect',database]))[0]['Mounts']
    if label != PROJECT or not any(m.get('Name')==PROJECT+'_integration_data' for m in mounts):
        raise RuntimeError('Refusing migrations outside owned integration database')
    spec=importlib.util.spec_from_file_location('integration_migrate',ROOT/'scripts/migrate.py')
    migrate=importlib.util.module_from_spec(spec);spec.loader.exec_module(migrate)
    existing=run(['docker','exec',database,'psql','-X','-qAt','-U','nsai','-d','nsai',
                  '-c',"SELECT to_regclass('public.nsai_schema_migrations') IS NOT NULL"])
    backup=None
    if existing=='t':
        backups=STATE/'backups';backups.mkdir(exist_ok=True)
        backup=backups/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex+'.sql')
        migrate.stream_backup(['docker','exec',database,'pg_dump','-U','nsai','-d','nsai'],backup)
    elif existing!='f':
        raise RuntimeError('Could not identify owned integration migration state')
    # Pure SQL helpers are also used by the owned qualification fixtures. The
    # release migration CLI is unchanged; this DB contains synthetic data only.
    sql=migrate.migration_sql(ROOT)+migrate.role_sql((private/'app_db.txt').read_text())
    run(['docker','exec','-i',database,'psql','-X','-q','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],body=sql)
    run(compose+['up','-d','--wait'],timeout=240)
    (STATE/'identity.json').write_text(json.dumps(dict(project=PROJECT,url='http://127.0.0.1:8790',
        scope='synthetic integration only',release_admitted=False,images=dict(api=api_image,ui=ui_image,db=db_image,model=model_image,encoder=encoder_image),
        model_id=selection['model_id'],model_architecture=architecture,model_sha256=selection['sha256'],
        migration_backup=str(backup.relative_to(ROOT)) if backup else None,
        compose_sha256=hashlib.sha256(target.read_bytes()).hexdigest()),indent=2)+'\n')
    print('Integration stack ready: http://127.0.0.1:8790')
    print('Local login credential file: state/integration/secrets/operator.txt')
    print('Synthetic integration only; release admission unchanged.')


if __name__ == '__main__':
    main()
