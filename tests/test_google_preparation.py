import copy
import importlib.util
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_google_deployment import render


def fixture():
    source=dict(name='noetaris-integration',services={name:dict(image='local',ports=[],volumes=[]) for name in ['api','ui','db','parser','encoder','llama-cpp']},
        secrets={'operator':{'file':'C:/private/key'},'partner_evolus':{'file':'C:/private/evolus'}},volumes={'integration_data':{}},networks={})
    source['services']['llama-cpp']['volumes']=[{'source':'C:/private/model','target':'/models/model.gguf'}]
    source['services']['encoder']['volumes']=[{'source':'C:/private/encoder','target':'/models'}]
    config=dict(project_id='owned-project',zone='us-central1-a',
        images={key:'us-central1-docker.pkg.dev/owned-project/repository/'+key+'@sha256:'+'a'*64 for key in ['api','ui','db','encoder','model']},
        model_file='/srv/noetaris/models/gemma/model.gguf',encoder_directory='/srv/noetaris/models/minilm')
    return source,config


def test_portable_private_bundle_has_no_windows_secrets_and_never_mutates_template():
    source,config=fixture();before=copy.deepcopy(source);out=render(source,config)
    assert source==before and out['name']=='noetaris-cloud'
    assert all(v['file'].startswith('/etc/noetaris/secrets/') for v in out['secrets'].values())
    assert out['services']['ui']['ports']==['127.0.0.1:8790:8080']
    assert out['services']['parser']['image']==config['images']['api']
    assert 'C:/' not in str(out)


@pytest.mark.parametrize('case',['mutable','wrong-project','missing-image','relative-model','escape-model','wrong-template'])
def test_unpinned_foreign_or_nonportable_inputs_fail(case):
    source,config=fixture()
    if case=='mutable':config['images']['api']='api:latest'
    elif case=='wrong-project':config['images']['api']=config['images']['api'].replace('/owned-project/','/foreign-project/')
    elif case=='missing-image':config['images'].pop('ui')
    elif case=='relative-model':config['model_file']='models/gemma.gguf'
    elif case=='escape-model':config['model_file']='/srv/noetaris/models/../../private'
    elif case=='wrong-template':source['name']='original-stack'
    with pytest.raises(ValueError):render(source,config)
