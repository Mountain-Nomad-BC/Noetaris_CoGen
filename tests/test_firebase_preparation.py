import importlib.util
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from prepare_firebase import firebase_config,bundle


def config():
    return dict(project_id='owned-project',site_id='owned-site',app_origin='https://app.owned.example',
                api_origin='https://api.owned.example',deployment_site='owned.example')


def fixture(tmp_path):
    dist=tmp_path/'dist';dist.mkdir();(dist/'index.html').write_text('<html>synthetic</html>')
    (dist/'deployment-config.json').write_text(json.dumps(dict(mode='live',app_origin=config()['app_origin'],
        api_origin=config()['api_origin'],deployment_site='owned.example')))
    assets=tmp_path/'assets';(assets/'pdfjs').mkdir(parents=True)
    for name in ['pdf-canvas.mjs','pdf-quotes.mjs','pdfjs/pdf.mjs','pdfjs/pdf.worker.mjs','pdfjs/LICENSE','pdfjs/provenance.json']:
        (assets/name).write_text('synthetic public runtime')
    (assets/'verification.json').write_text('PRIVATE_SENTINEL')
    return dist,assets


def test_firebase_headers_spa_and_exact_api_origin():
    value=firebase_config(config())['hosting'];headers={h['key']:h['value'] for h in value['headers'][0]['headers']}
    assert value['rewrites']==[dict(source='**',destination='/index.html')]
    assert 'https://api.owned.example' in headers['Content-Security-Policy']
    assert "script-src 'self'" in headers['Content-Security-Policy']
    assert 'unsafe-eval' not in headers['Content-Security-Policy']
    assert 'no-cache' in headers['Cache-Control']
    assert value['headers'][1]['headers'][0]['value'].endswith('immutable')


def test_bundle_copies_only_public_pdf_runtime_and_is_not_deployment_acceptance(tmp_path):
    dist,assets=fixture(tmp_path);output=tmp_path/'bundle'
    receipt=bundle(config(),dist,output,assets)
    assert receipt['status']=='PREPARED_NOT_DEPLOYED' and receipt['release_admitted'] is False
    assert receipt['firebase_authentication_added'] is False
    assert not (output/'public/pdf-runtime/verification.json').exists()
    assert (output/'public/pdf-runtime/pdfjs/pdf.worker.mjs').is_file()
    assert 'PRIVATE_SENTINEL' not in json.dumps(receipt)
    assert len(receipt['public_artifact_sha256'])==64


@pytest.mark.parametrize('case',['map','log','env','private-proof','wrong-origin','demo'])
def test_private_debug_or_wrong_target_artifacts_cannot_be_bundled(tmp_path,case):
    dist,assets=fixture(tmp_path)
    if case in {'map','log','env','private-proof'}:
        (dist/{'map':'app.js.map','log':'build.log','env':'.env','private-proof':'verification.json'}[case]).write_text('private')
    else:
        p=dist/'deployment-config.json';d=json.loads(p.read_text());d['api_origin' if case=='wrong-origin' else 'mode']='wrong';p.write_text(json.dumps(d))
    with pytest.raises(ValueError):bundle(config(),dist,tmp_path/'bundle',assets)


@pytest.mark.parametrize('change',[{'api_origin':'http://api.owned.example'},{'api_origin':'https://user:secret@api.owned.example'},
    {'app_origin':'https://project.web.app'},{'project_id':'REPLACE_PROJECT'},{'site_id':'invalid/site'}])
def test_placeholder_credential_and_crosssite_configuration_cannot_render(change):
    with pytest.raises(ValueError):firebase_config({**config(),**change})


def test_default_firebase_site_can_prepare_same_origin_static_hosting():
    values=dict(project_id='existing-project',site_id='existing-site',app_origin='https://existing-site.web.app',api_origin='https://existing-site.web.app',deployment_site='')
    hosting=firebase_config(values)['hosting']
    assert hosting['site']=='existing-site'
    assert 'run' not in str(hosting.get('rewrites',[]))
    with pytest.raises(ValueError): firebase_config({**values,'app_origin':'https://other-site.web.app','api_origin':'https://other-site.web.app'})
