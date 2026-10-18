"""Known defective generated corpora stay retained but outside trusted inputs."""
import importlib.util
from pathlib import Path
import pytest
from nsai.source_admission import admit_source_path,admit_filesystem_source,read_source_bytes
from nsai.ingestion import parse_source


@pytest.mark.parametrize('path',[
    'NSAI_MASTER_CORPUS/data.json','NSAI_MASTER_CORPUS_REBUILD/a.jsonl',
    'NSAI_MASTER_CORPUS_REBUILD_V2/graph.json',r'C:\data\nsai_master_corpus\a.pdf',
    '/data/NSAI_MASTER_CORPUS. /a.json','/data/ＮＳＡＩ_MASTER_CORPUS/a.json',
    'NSAI_MASTER_CORPUS.json','nsai_master_corpus_rebuild_v3/a.json',
])
def test_known_excluded_names_cannot_enter_trusted_admission(path):
    with pytest.raises(ValueError,match='excluded'):admit_source_path(path)


def test_exclusion_is_not_deletion_or_rewriting(tmp_path):
    folder=tmp_path/'NSAI_MASTER_CORPUS_REBUILD_V2';folder.mkdir();source=folder/'source.json'
    original=b'{"failure":"retain this exact regression artifact"}';source.write_bytes(original)
    with pytest.raises(ValueError):admit_source_path(source)
    assert source.read_bytes()==original


def test_aliasing_the_selected_base_cannot_admit_a_linked_tree(tmp_path,monkeypatch):
    folder=tmp_path/'NSAI_MASTER_CORPUS';folder.mkdir();(folder/'source.json').write_bytes(b'{}')
    link=tmp_path/'ordinary-alias'
    try:link.symlink_to(folder,target_is_directory=True)
    except OSError:pytest.skip('Host cannot create test symlink')
    with pytest.raises(ValueError,match='links and reparse'):admit_filesystem_source(link/'source.json')
    module=load_script('ingest_arxiv_corpus.py',monkeypatch)
    with pytest.raises(ValueError,match='links and reparse'):module.private_file(link,'source.json')
    assert (folder/'source.json').read_bytes()==b'{}'


def test_bounded_original_read_does_not_truncate_or_accept_directories(tmp_path):
    source=tmp_path/'original.json';source.write_bytes(b'{"exact":0}')
    assert read_source_bytes(source,100)==b'{"exact":0}'
    with pytest.raises(ValueError,match='bounded read'):read_source_bytes(source,5)
    with pytest.raises(ValueError,match='bounded read'):read_source_bytes(tmp_path,100)
    assert source.read_bytes()==b'{"exact":0}'


def test_independent_original_path_is_not_blanket_rejected(tmp_path):
    assert admit_source_path(tmp_path/'validated-original-snapshot'/'paper.pdf') is None
    assert parse_source(b'{"x":1}','ordinary.json')['media_type']=='application/json'
    with pytest.raises(ValueError,match='excluded'):parse_source(b'{"x":1}','NSAI_MASTER_CORPUS.json')


def load_script(name,monkeypatch):
    root=Path(__file__).resolve().parents[1];monkeypatch.syspath_prepend(str(root/'scripts'))
    spec=importlib.util.spec_from_file_location('quarantine_'+name,root/'scripts'/name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_import_query_and_enrichment_refuse_before_read_or_encoder(tmp_path,monkeypatch):
    blocked=tmp_path/'NSAI_MASTER_CORPUS_REBUILD'/'manifest.json'
    importer=load_script('ingest_arxiv_corpus.py',monkeypatch)
    with pytest.raises(ValueError,match='excluded'):importer.private_file(blocked.parent,'a.pdf')
    with pytest.raises(ValueError,match='excluded'):importer.private_file(tmp_path,'NSAI_MASTER_CORPUS_REBUILD/a.pdf')
    with pytest.raises(ValueError,match='excluded'):importer.run(blocked,'unused')
    query=load_script('query_arxiv_corpus.py',monkeypatch)
    with pytest.raises(ValueError,match='excluded'):query.query(blocked,'question')
    with pytest.raises(ValueError,match='excluded'):query.query(tmp_path/'missing.json','question',enrichment_manifest=blocked)
    enrichment=load_script('enrich_arxiv_corpus.py',monkeypatch)
    with pytest.raises(ValueError,match='excluded'):enrichment.enrich(blocked)
    with pytest.raises(ValueError,match='excluded'):enrichment.enrich(tmp_path/'missing.json',author_manifest=blocked)


def test_duplicate_manifest_keys_are_rejected_before_indexing(tmp_path,monkeypatch):
    path=tmp_path/'manifest.json';path.write_bytes(b'{"papers":[],"papers":[{}]}')
    importer=load_script('ingest_arxiv_corpus.py',monkeypatch)
    with pytest.raises(ValueError,match='Duplicate JSON key'):importer.run(path,'unused')
    query=load_script('query_arxiv_corpus.py',monkeypatch)
    with pytest.raises(ValueError,match='Duplicate JSON key'):query.query(path,'question')
    assert path.read_bytes()==b'{"papers":[],"papers":[{}]}'
