import pytest
from nsai.inference import context_budget, prepare_source_request

@pytest.mark.parametrize('configured,actual,expected',[
    ('8192',8192,8192),('16384',8192,8192),('32768',16384,16384),('2048',8192,2048)])
def test_actual_capacity_always_limits_configured_budget(monkeypatch,configured,actual,expected):
    monkeypatch.setenv('NSAI_MODEL_CONTEXT_TOKENS',configured)
    assert context_budget(actual)==expected

@pytest.mark.parametrize('configured',['0','-1','511','32769','1000000','8192.0',' 8192','nan',''])
def test_invalid_context_configuration_fails_closed(monkeypatch,configured):
    monkeypatch.setenv('NSAI_MODEL_CONTEXT_TOKENS',configured)
    with pytest.raises(ValueError):context_budget(8192)

@pytest.mark.parametrize('output',[True,0,-1,4097,256.0])
def test_invalid_output_budget_precedes_provider_configuration(output):
    with pytest.raises(ValueError,match='output token'):prepare_source_request('question',[],max_tokens=output)
