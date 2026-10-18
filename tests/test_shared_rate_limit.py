import pytest


def test_cloud_run_cannot_start_with_process_local_limits(monkeypatch):
    from nsai.shared_rate_limit import validate_runtime
    monkeypatch.setenv('K_SERVICE','qualification')
    monkeypatch.setenv('NSAI_RATE_LIMIT_BACKEND','local')
    with pytest.raises(ValueError,match='shared rate limiting'):validate_runtime()


@pytest.mark.parametrize('url',['redis://public.example:6379','redis://user:secret@redis:6379','https://redis','redis://redis/1','redis://redis?x=1'])
def test_unsafe_redis_urls_fail_before_secret_read(monkeypatch,url):
    from nsai import shared_rate_limit as shared
    monkeypatch.setenv('NSAI_REDIS_URL',url)
    monkeypatch.setattr(shared,'_secret',lambda *_:pytest.fail('Invalid endpoint read a credential'))
    with pytest.raises(ValueError):shared.settings()


def test_unknown_actor_cannot_create_shared_keys(monkeypatch):
    from nsai import shared_rate_limit as shared
    monkeypatch.setattr(shared,'settings',lambda:pytest.fail('Unknown actor opened Redis'))
    assert shared.admit('untrusted-caller',120) is False
