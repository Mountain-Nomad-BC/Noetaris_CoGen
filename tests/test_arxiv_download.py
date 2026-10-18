import importlib.util
from pathlib import Path
import pytest

path=Path(__file__).resolve().parents[1]/'scripts/download_arxiv_corpus.py'
spec=importlib.util.spec_from_file_location('arxiv_download',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

@pytest.mark.parametrize('url',['http://arxiv.org/pdf/1412.6980v9','https://arxiv.org.evil.invalid/pdf/a','https://evil.arxiv.org/a','https://user:secret@arxiv.org/a','https://arxiv.org:444/a','https://example.com/a'])
def test_only_exact_official_https_hosts_admitted(url):
    with pytest.raises(ValueError):module.official_url(url)

def test_seeded_order_is_repeatable_complete_and_not_input_order_dependent():
    records=[{'id':str(i)}for i in range(20)]
    first=module.sample_order(records,20261014,'physics')
    assert first==module.sample_order(list(reversed(records)),20261014,'physics')
    assert {r['id']for r in first}=={r['id']for r in records}
    assert first!=module.sample_order(records,20261014,'biology')

@pytest.mark.parametrize('value',['1412.6980','../1412.6980v9','1412.6980v0','https://evil.invalid/1412.6980v9'])
def test_unversioned_or_ambiguous_paper_identity_refused(value):
    with pytest.raises(ValueError):module.paper_id(value)

def fixture():
    record={'base_id':'1412.6980','version':9,'title':'Adam: A Method for Stochastic Optimization','primary_category':'cs.LG'}
    html=b'<meta name="citation_title" content="Adam: A Method for Stochastic Optimization"><meta name="citation_arxiv_id" content="1412.6980"><div>(cs.LG)</div><strong>[v9]</strong><a href="http://arxiv.org/licenses/nonexclusive-distrib/1.0/">Rights</a>'
    return record,html

def test_license_title_category_and_requested_version_bind_actual_abs_metadata():
    record,html=fixture();assert module.validate_abs(html,record)['license_url']=='http://arxiv.org/licenses/nonexclusive-distrib/1.0/'

@pytest.mark.parametrize('old,new',[(b'[v9]',b'[v8]'),(b'(cs.LG)',b'(cs.CL)'),(b'1412.6980',b'1412.6981'),(b'Adam:',b'Forged:')])
def test_changed_metadata_is_refused(old,new):
    record,html=fixture()
    with pytest.raises(ValueError):module.validate_abs(html.replace(old,new),record)

def test_no_parser_or_docker_launch_for_html_or_oversized_original(monkeypatch):
    def forbidden(*a,**k):raise AssertionError('Unadmitted original reached Docker')
    monkeypatch.setattr(module.subprocess,'run',forbidden)
    for data in [b'<html>notPDF',b'%PDF-'+b'x'*module.MAX_BYTES]:
        with pytest.raises(ValueError):module.preflight_pdf(data,'1412.6980v9')

def test_polite_spacing_cannot_be_disabled():
    with pytest.raises(ValueError):module.Fetcher([],delay=2.99)

def test_metadata_dtd_rejected_before_xml_expansion():
    with pytest.raises(ValueError):module.parse_pool(b'<!DOCTYPE feed [<!ENTITY x "expanded">]><feed>&x;</feed>','ai')

def test_cached_official_original_requires_exact_hash_and_budget(tmp_path):
    path=tmp_path/'original';path.write_bytes(b'original official bytes')
    url='https://arxiv.org/pdf/1412.6980v9'
    fetcher=module.Fetcher([],cache={url:dict(path=str(path),sha256=module.sha(path.read_bytes()),run_id='original-capture')})
    assert fetcher.fetch(url,100)[0]==b'original official bytes'
    with pytest.raises(ValueError,match='digest/budget'):fetcher.fetch(url,2)
    path.write_bytes(b'altered official bytes')
    with pytest.raises(ValueError,match='digest/budget'):fetcher.fetch(url,100)

def test_native_visual_gap_is_not_misrepresented_as_complete_acquisition(monkeypatch):
    data=b'%PDF-original-fixture'
    def fake(args,**kwargs):
        if args[1]=='inspect':return module.subprocess.CompletedProcess(args,1,b'',b'')
        parsed=dict(original_sha256=module.sha(data),page_count=1,raw_text='Native text beside an unextracted figure.',complete=False,pages=[dict(page=1,complete=False)],warnings=['visual gap'])
        return module.subprocess.CompletedProcess(args,0,module.json.dumps(parsed).encode(),b'')
    monkeypatch.setattr(module.subprocess,'run',fake)
    result=module.preflight_pdf(data,'1412.6980v9')
    assert result['status']=='PASS_CAPS_ONLY'and result['complete']is False and result['native_gap_pages']==[1]

def test_missing_or_ambiguous_license_is_refused():
    record,html=fixture()
    with pytest.raises(ValueError):module.validate_abs(html.replace(b'/licenses/',b'/help/'),record)
    with pytest.raises(ValueError):module.validate_abs(html+b'<a href="https://creativecommons.org/licenses/by/4.0/">Other license</a>',record)

def test_oversized_cache_refused_before_open(tmp_path,monkeypatch):
    path=tmp_path/'large-cache';path.write_bytes(b'x'*101)
    def forbidden(*args,**kwargs):raise AssertionError('Oversized cache was opened')
    monkeypatch.setattr(Path,'open',forbidden)
    with pytest.raises(ValueError,match='digest/budget'):module.bounded_cached_bytes(path,100)
