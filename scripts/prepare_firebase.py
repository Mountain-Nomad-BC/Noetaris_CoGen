"""Build a private static Firebase preparation bundle; never deploy or certify."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urlsplit
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai.oauth_providers import _https_origin


def firebase_config(config):
    keys={'project_id','site_id','app_origin','api_origin','deployment_site'}
    if not isinstance(config,dict) or set(config)!=keys:raise ValueError('Invalid Firebase deployment fields')
    if not isinstance(config['project_id'],str) or re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]',config['project_id']) is None:
        raise ValueError('Explicit Firebase project required')
    if not isinstance(config['site_id'],str) or re.fullmatch(r'[a-z0-9][a-z0-9-]{0,61}[a-z0-9]',config['site_id']) is None:
        raise ValueError('Explicit Firebase hosting site required')
    app=_https_origin(config['app_origin']);api=_https_origin(config['api_origin']);site=config['deployment_site']
    if (not isinstance(site,str) or re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',site) is None or
        '.' not in site or urlsplit(api).hostname!='api.'+site or urlsplit(app).hostname not in {'app.'+site,site}):
        raise ValueError('Owned same-site app/API domains required')
    csp=("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
         "font-src 'self' data:; img-src 'self' data: blob:; connect-src 'self' "+api+"; "
         "worker-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; "
         "form-action 'self' "+api)
    security=[dict(key='Content-Security-Policy',value=csp),dict(key='X-Content-Type-Options',value='nosniff'),
        dict(key='Referrer-Policy',value='no-referrer'),dict(key='X-Frame-Options',value='DENY'),
        dict(key='Strict-Transport-Security',value='max-age=31536000'),
        dict(key='Permissions-Policy',value='camera=(), microphone=(), geolocation=()'),
        dict(key='Cache-Control',value='no-cache, max-age=0, must-revalidate')]
    return dict(hosting=dict(site=config['site_id'],public='public',
        ignore=['firebase.json','**/.*','**/node_modules/**','**/*.map','**/*.log'],
        headers=[dict(source='**',headers=security),dict(source='/assets/**',
            headers=[dict(key='Cache-Control',value='public, max-age=31536000, immutable')])],
        rewrites=[dict(source='**',destination='/index.html')]))


def bundle(config,dist,output,asset_root=ROOT/'assets'):
    hosting=firebase_config(config)
    expected=dict(mode='live',api_origin=_https_origin(config['api_origin']),
                  app_origin=_https_origin(config['app_origin']),deployment_site=config['deployment_site'])
    if json.loads((dist/'deployment-config.json').read_text())!=expected:
        raise ValueError('Frontend build origin metadata does not match target configuration')
    if not (dist/'index.html').is_file():raise ValueError('Built frontend index is missing')
    files=[]
    for path in [dist,*dist.rglob('*')]:
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):raise ValueError('Static source links are forbidden')
        if not path.is_file():continue
        if path.name.startswith('.') or path.name=='verification.json' or path.suffix in {'.map','.log'}:raise ValueError('Private/debug build file is not publishable')
        files.append((path,Path('public')/path.relative_to(dist)))
    runtime=['pdf-canvas.mjs','pdf-quotes.mjs','pdfjs/pdf.mjs','pdfjs/pdf.worker.mjs','pdfjs/LICENSE','pdfjs/provenance.json']
    fonts=asset_root/'pdfjs/standard_fonts'
    if fonts.exists():runtime += [p.relative_to(asset_root).as_posix() for p in fonts.iterdir()
        if p.is_file() and (p.suffix.lower() in {'.pfb','.ttf'} or p.name in {'LICENSE_FOXIT','LICENSE_LIBERATION','provenance.json'})]
    for name in runtime:
        source=asset_root/name
        if source.is_symlink() or not source.is_file():raise ValueError('Qualified local PDF runtime is missing')
        files.append((source,Path('public/pdf-runtime')/name))
    if len(files)>1000 or sum(p.stat().st_size for p,_ in files)>128*1024**2:
        raise ValueError('Static artifact exceeds bounded bundle profile')
    output.mkdir(parents=True,exist_ok=False)
    for source,destination in files:
        target=output/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    (output/'firebase.json').write_text(json.dumps(hosting,indent=2)+'\n',encoding='utf-8')
    (output/'.firebaserc').write_text(json.dumps({'projects':{'default':config['project_id']}},indent=2)+'\n',encoding='utf-8')
    hashes={p.relative_to(output/'public').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((output/'public').rglob('*')) if p.is_file()}
    receipt=dict(status='PREPARED_NOT_DEPLOYED',release_admitted=False,cloud_resources_modified=False,
        firebase_authentication_added=False,source_maps_published=False,
        public_configuration=expected,files=hashes,
        public_artifact_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),
        pending=['Owner-approved Firebase site/domain and public publication',
                 'Real Google/GitHub OAuth and production-origin Chromium/Firefox cookie/CSRF E2E',
                 'Independent security, private-content, rights and release acceptance'])
    (output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--dist',type=Path,default=ROOT/'frontend/noetaris/dist')
    args=parser.parse_args()
    output=ROOT/'state/firebase-preparation'/uuid4().hex
    try:receipt=bundle(json.loads(args.config.read_text()),args.dist,output)
    except (OSError,ValueError,TypeError):
        print(json.dumps(dict(status='CONFIGURATION_REQUIRED',cloud_resources_modified=False,
            reason='Provide exact Firebase identifiers, owned HTTPS app/API origins and a matching live build'),indent=2));return 2
    print(json.dumps(dict(status=receipt['status'],bundle=str(output),release_admitted=False),indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
