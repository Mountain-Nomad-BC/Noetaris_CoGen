from decimal import Decimal
import pytest


def test_event_defaults_and_separate_cash_credit_ledgers():
    from nsai.operational_policy import operational_policy
    p=operational_policy({})
    assert (p.concurrent_users,p.requests_per_minute,p.generations_per_day)==(5,120,20)
    assert (p.generations_per_user,p.ingestions_per_user,p.gpu_jobs,p.gpu_queue)==(1,1,1,10)
    assert (p.cash_microusd,p.cloud_microusd,p.api_microusd,p.contingency_microusd)==(20000000,5000000,10000000,5000000)
    assert p.local_token_ceiling is None and p.amd_credit_limit==0 and p.evolus_credit_limit==0


@pytest.mark.parametrize('value',['-1','0','true','1.5',' 5','1000000000000'])
def test_invalid_concurrency_cannot_disable_limits(value):
    from nsai.operational_policy import operational_policy
    with pytest.raises(ValueError):operational_policy({'NSAI_CONCURRENT_USERS':value})


def test_overallocated_cash_is_rejected():
    from nsai.operational_policy import operational_policy
    with pytest.raises(ValueError):operational_policy({'NSAI_CASH_BUDGET_USD':'19.99'})


@pytest.mark.parametrize('value',['NaN','Infinity','-1','0.0000001','1e5',' 20'])
def test_money_rejects_nonfinite_negative_precision_or_ambiguous_syntax(value):
    from nsai.operational_policy import microusd
    with pytest.raises(ValueError):microusd(value)


def test_cost_estimate_rounds_up_and_never_uses_binary_float():
    from nsai.operational_policy import estimate_token_cost,microusd
    assert microusd('20.00')==20000000
    assert estimate_token_cost(1,1,Decimal('0.10'),Decimal('0.20'))==1
    assert estimate_token_cost(1000000,2000000,Decimal('1.25'),Decimal('2.50'))==6250000
    with pytest.raises(ValueError):estimate_token_cost(1,1,0.1,Decimal('0.2'))


def test_only_whole_ai_requests_count_as_generations():
    from nsai.operational_policy import is_ai_generation
    assert is_ai_generation('generation')
    for kind in ['retrieval','authentication','stream.chunk','asr.partial','tts.clause','ingestion']:
        assert not is_ai_generation(kind)


def test_configured_request_limit_is_enforced_by_http(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from nsai import api
    token=tmp_path/'operator';token.write_text('x'*48)
    for setting in ['NSAI_ADMIN_TOKEN_FILE','NSAI_VIEWER_TOKEN_FILE','NSAI_REVIEWER_TOKEN_FILE','NSAI_LOCAL_IDENTITIES_FILE']:
        monkeypatch.delenv(setting,raising=False)
    monkeypatch.setenv('NSAI_API_TOKEN_FILE',str(token))
    monkeypatch.setenv('NSAI_REQUESTS_PER_MINUTE','2')
    api.rate_window.clear()
    try:
        with TestClient(api.app) as client:
            headers={'Authorization':'Bearer '+'x'*48}
            assert client.get('/v1/capabilities',headers=headers).status_code==200
            assert client.get('/v1/capabilities',headers=headers).status_code==200
            denied=client.get('/v1/capabilities',headers=headers)
            assert denied.status_code==429 and denied.headers['Retry-After']=='60'
    finally:api.rate_window.clear()
