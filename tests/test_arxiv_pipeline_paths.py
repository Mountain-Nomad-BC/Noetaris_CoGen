import importlib.util
from pathlib import Path
import pytest

@pytest.fixture
def module():
    source=Path(__file__).resolve().parents[1]/'scripts/ingest_arxiv_corpus.py'
    spec=importlib.util.spec_from_file_location('arxiv_pipeline',source);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

@pytest.mark.parametrize('value',['../secrets/token.txt','/etc/passwd','C:/secret','a\\b','x/../../y',''])
def test_untrusted_manifest_path_escape_rejected(module,tmp_path,value):
    with pytest.raises(ValueError):module.private_file(tmp_path,value)

def test_regular_corpus_file_admitted_and_link_refused(module,tmp_path):
    paper=tmp_path/'paper.pdf';paper.write_bytes(b'%PDF-')
    assert module.private_file(tmp_path,'paper.pdf')==paper
    link=tmp_path/'link.pdf'
    try:link.symlink_to(paper)
    except OSError:pytest.skip('Host cannot create test symlink')
    with pytest.raises(ValueError):module.private_file(tmp_path,'link.pdf')

def test_parser_image_alias_refused_before_docker(module):
    with pytest.raises(ValueError):module.parse_isolated(b'%PDF-','paper.pdf','latest')
