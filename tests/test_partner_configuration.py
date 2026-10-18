import json
import pytest
from fastapi.testclient import TestClient
from nsai.integrations.configuration import evolus_configuration,evolus_setup,integration_setup


def binding():
    return dict(api_base='https://evolus.example.invalid/api/v1',application_id='application',workflow_id='workflow',agent_id='agent',extractor_id='extractor',payload_schema_sha256='a'*64)


def test_complete_local_configuration_is_never_claimed_commissioned(tmp_path):
    config=tmp_path/'bindings.json';config.write_text(json.dumps(binding()))
    key=tmp_path/'credential';key.write_text('synthetic-'+('x'*40))
    assert evolus_configuration(config)==binding()
    result=evolus_setup(str(config),str(key))
    assert result['configuration_ready'] is True
    assert result['commissioned'] is False and result['dispatch_enabled'] is False
    assert 'synthetic' not in json.dumps(result) and str(tmp_path) not in json.dumps(result)


@pytest.mark.parametrize('change',[
    {'workflow_id':'../path'},{'application_id':True},{'agent_id':''},
    {'extractor_id':'x'*129},{'payload_schema_sha256':'not-a-digest'},{'credential':'FORBIDDEN'},
    {'api_base':'http://unverified.example'},{'api_base':'https://user:secret@unverified.example'},
])
def test_bad_bindings_fail_closed_and_are_redacted(tmp_path,change):
    config=tmp_path/'bindings.json';config.write_text(json.dumps({**binding(),**change}))
    with pytest.raises(ValueError):evolus_configuration(config)
    report=evolus_setup(str(config),'')
    assert report['configuration_ready'] is False and report['bindings_configured'] is False
    assert '../path' not in json.dumps(report) and 'FORBIDDEN' not in json.dumps(report)


def test_duplicate_oversize_and_missing_configs_do_not_pass(tmp_path):
    for raw in ['{"application_id":"a","application_id":"b"}','x'*16385,'[]']:
        p=tmp_path/'bad.json';p.write_text(raw)
        assert evolus_setup(str(p),'')['configuration_ready'] is False
    assert evolus_setup(str(tmp_path/'absent'),'')['configuration_ready'] is False


def test_integration_status_requires_identity_and_never_calls_partner(monkeypatch,tmp_path):
    import httpx
    from nsai.api import app
    key=tmp_path/'operator';key.write_text('x'*64)
    monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(key))
    for name in ['NSAI_EVOLUS_CONFIG_FILE','NSAI_EVOLUS_API_KEY_FILE','NSAI_AMD_API_KEY_FILE','NSAI_OPENROUTER_API_KEY_FILE']:
        monkeypatch.delenv(name,raising=False)
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:pytest.fail('Setup status contacted a partner'))
    with TestClient(app) as client:
        assert client.get('/v1/integrations/status').status_code==401
        response=client.get('/v1/integrations/status',headers={'Authorization':'Bearer '+('x'*64)})
    assert response.status_code==200
    data=response.json();assert len(data['partners'])==3
    assert all(p['dispatch_enabled'] is False for p in data['partners'])
