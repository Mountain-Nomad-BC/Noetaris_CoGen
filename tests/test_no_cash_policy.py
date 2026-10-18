import pytest


@pytest.mark.parametrize('account',['cash-api','cash-cloud','cash-contingency','cash-total'])
def test_cash_denied_before_storage_or_provider(monkeypatch,account):
    from nsai import cost_store
    monkeypatch.setattr(cost_store.store,'connect',lambda:pytest.fail('Cash request reached database'))
    with pytest.raises(PermissionError,match='Cash dispatch is prohibited'):
        cost_store.reserve(request_id='a'*32,provider='test',account=account,estimated_units=0)


def test_admin_example_is_explicitly_nonbinding_without_storage(monkeypatch):
    from nsai import cost_store
    monkeypatch.setattr(cost_store.store,'connect',lambda:pytest.fail('Demonstration accessed money ledger'))
    result=cost_store.demonstration()
    assert result['mode']=='demonstration-only' and result['cash_dispatch_enabled'] is False
    assert result['example']['maximum']=='20.00'


@pytest.mark.parametrize('funding',['cash','paid','credit-card'])
def test_cash_funded_model_is_rejected_before_transport(monkeypatch,funding):
    from nsai.inference import model_settings
    monkeypatch.setenv('NSAI_MODEL_URL','https://example.invalid/v1')
    monkeypatch.setenv('NSAI_MODEL_FUNDING',funding)
    with pytest.raises(RuntimeError,match='Cash-funded'):model_settings()


def test_unclassified_remote_model_cannot_dispatch(monkeypatch):
    from nsai.inference import model_settings
    monkeypatch.setenv('NSAI_MODEL_URL','https://example.invalid/v1')
    monkeypatch.delenv('NSAI_MODEL_FUNDING',raising=False)
    with pytest.raises(RuntimeError,match='explicitly approved'):model_settings()
