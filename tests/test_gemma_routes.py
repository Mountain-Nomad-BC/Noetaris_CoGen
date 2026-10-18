import pytest
from nsai.integrations.gemma_routes import candidates,free_catalog_route


def test_amd_does_real_elevation_first_and_cpu_is_local_continuity():
    routes=candidates('elevation',export_authorized=True,available=['cpu','amd','fallback'])
    assert [r.id for r in routes]==['amd','cpu','fallback']


def test_private_material_cannot_automatically_leave_local_boundary():
    assert [r.id for r in candidates('research',available=['amd','cpu','research','fallback'])]==['cpu']
    assert candidates('elevation',available=['amd','fallback'])==[]


def test_cooldown_skips_rate_limited_route_without_retry_storm():
    args=dict(export_authorized=True,available=['amd','research','fallback','cpu'],cooldowns={'research':60,'amd':30})
    assert [r.id for r in candidates('research',now=10,**args)]==['fallback','cpu']
    assert [r.id for r in candidates('research',now=60,**args)]==['amd','research','fallback','cpu']


@pytest.mark.parametrize('price',['0.01','NaN','Infinity','-1',None])
def test_free_route_refuses_priced_or_unknown_catalog(price):
    with pytest.raises(ValueError):free_catalog_route('research',[dict(id='google/gemma-4-31b-it:free',pricing=dict(prompt=price,completion='0'))])


def test_free_alias_must_be_exact_and_all_fees_zero():
    with pytest.raises(ValueError):free_catalog_route('research',[dict(id='google/gemma-4-31b-it',pricing=dict(prompt='0',completion='0'))])
    with pytest.raises(ValueError):free_catalog_route('research',[dict(id='google/gemma-4-31b-it:free',pricing=dict(prompt='0',completion='0',request='1'))])
    assert free_catalog_route('research',[dict(id='google/gemma-4-31b-it:free',pricing=dict(prompt='0',completion='0'))]).funding=='free'


def test_default_hosted_route_uses_amd_then_both_free_gemmas_then_cpu():
    assert [r.id for r in candidates('default',export_authorized=True,available=['cpu','amd','research','fallback'])] == ['amd','research','fallback','cpu']
    assert [r.id for r in candidates('default',available=['cpu','amd','research','fallback'])] == ['cpu']


def test_exact_amd_hosted_endpoint_configuration(monkeypatch):
    from nsai.inference import model_settings
    monkeypatch.setenv('NSAI_MODEL_URL','https://developer.amd.com.cn/radeon/api/v1')
    monkeypatch.setenv('NSAI_MODEL_NAME','Gemma-4-31B-IT')
    monkeypatch.setenv('NSAI_MODEL_FUNDING','free')
    monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)
    assert model_settings()[:2] == ('https://developer.amd.com.cn/radeon/api/v1','Gemma-4-31B-IT')
    monkeypatch.setenv('NSAI_MODEL_URL','https://untrusted.example/radeon/api/v1')
    with pytest.raises(RuntimeError): model_settings()
