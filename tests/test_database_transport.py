import pytest
from nsai.store import database_transport


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for name in ['NSAI_DB_HOST','NSAI_DB_PORT','NSAI_DB_SSLMODE','NSAI_DB_SSLROOTCERT_FILE']:
        monkeypatch.delenv(name,raising=False)


def test_local_database_preserves_default_transport():
    assert database_transport()==dict(port=5432,sslmode='prefer')


def test_managed_database_uses_explicit_port_ca_and_hostname_verification(monkeypatch,tmp_path):
    ca=tmp_path/'ca.pem';ca.write_text('-----BEGIN CERTIFICATE-----\nfixture\n-----END CERTIFICATE-----')
    monkeypatch.setenv('NSAI_DB_HOST','primary.database.example')
    monkeypatch.setenv('NSAI_DB_PORT','6543')
    monkeypatch.setenv('NSAI_DB_SSLROOTCERT_FILE',str(ca))
    assert database_transport()==dict(port=6543,sslmode='verify-full',sslrootcert=str(ca))


@pytest.mark.parametrize('mode',['disable','allow','prefer','require','verify-ca'])
def test_remote_database_cannot_downgrade_tls(monkeypatch,mode):
    monkeypatch.setenv('NSAI_DB_HOST','primary.example');monkeypatch.setenv('NSAI_DB_SSLMODE',mode)
    with pytest.raises(RuntimeError,match='verified TLS'):database_transport()


@pytest.mark.parametrize('port',['0','65536','-1','many','5432,5433','1'*20])
def test_invalid_port_rejected(monkeypatch,port):
    monkeypatch.setenv('NSAI_DB_PORT',port)
    with pytest.raises(RuntimeError,match='port'):database_transport()


@pytest.mark.parametrize('host',['','db other','postgres://server','host/user','server\nnext'])
def test_host_is_a_single_endpoint(monkeypatch,host):
    monkeypatch.setenv('NSAI_DB_HOST',host)
    with pytest.raises(RuntimeError,match='host'):database_transport()


def test_remote_database_needs_real_readable_ca_configuration(monkeypatch,tmp_path):
    monkeypatch.setenv('NSAI_DB_HOST','primary.example')
    with pytest.raises(RuntimeError,match='CA certificate file'):database_transport()
    ca=tmp_path/'ca';monkeypatch.setenv('NSAI_DB_SSLROOTCERT_FILE',str(ca))
    with pytest.raises(RuntimeError,match='unavailable'):database_transport()
    ca.write_bytes(b'x'*131073)
    with pytest.raises(RuntimeError,match='oversized'):database_transport()
