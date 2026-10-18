import gzip
import hashlib
from io import BytesIO
import importlib.util
from pathlib import Path
import tarfile
import pytest

spec=importlib.util.spec_from_file_location('source_acquisition',Path(__file__).resolve().parents[1]/'scripts/acquire_arxiv_sources.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def bundle(members):
    output=BytesIO()
    with tarfile.open(fileobj=output,mode='w') as archive:
        for name,data in members:
            info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,BytesIO(data))
    return output.getvalue()

def artifact(raw):return module.build_supplement(raw,pdf_sha256='a'*64,document_id='b'*32,revision='v1')

def test_tar_gzip_reads_only_tex_bytes_without_filesystem_extraction(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Archive filesystem extraction attempted')
    monkeypatch.setattr(tarfile.TarFile,'extract',forbidden);monkeypatch.setattr(tarfile.TarFile,'extractall',forbidden)
    result=module.inspect_bundle(gzip.compress(bundle([('paper/main.tex',b'$x=1$'),('figure.png',b'original synthetic raster placeholder')])))
    assert result['format']=='tar_gzip' and result['member_count']==2 and result['ignored_extensions']=={'.png':1}
    assert result['files'][0]['data']==b'$x=1$' and result['files'][0]['member_path']=='paper/main.tex'

@pytest.mark.parametrize('name',['../escape.tex','/absolute.tex','C:/source.tex','dir\\escape.tex','a/../../b.tex','bad\nname.tex'])
def test_traversal_and_ambiguous_archive_paths_rejected(name):
    with pytest.raises(ValueError,match='Unsafe'):module.inspect_bundle(bundle([(name,b'$x$')]))

@pytest.mark.parametrize('kind',[tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.CHRTYPE,tarfile.BLKTYPE,tarfile.FIFOTYPE])
def test_links_devices_and_nonregular_archive_objects_rejected(kind):
    stream=BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as archive:
        info=tarfile.TarInfo('source.tex');info.type=kind;info.linkname='outside';archive.addfile(info)
    with pytest.raises(ValueError,match='links/devices'):module.inspect_bundle(stream.getvalue())

def test_duplicate_normalized_members_are_refused():
    with pytest.raises(ValueError,match='Duplicate'):module.inspect_bundle(bundle([('./a.tex',b'$a$'),('a.tex',b'$b$')]))

def test_member_count_and_declared_total_limits_fail_before_unbounded_reads():
    with pytest.raises(ValueError,match='128'):module.inspect_bundle(bundle([(f'{i}.bin',b'') for i in range(129)]))
    info=tarfile.TarInfo('oversize.bin');info.size=module.MAX_ARCHIVE_BYTES+1
    with pytest.raises(ValueError,match='total member'):module.inspect_bundle(info.tobuf()+b'\0'*1024)

def test_gzip_expansion_cap_and_tex_member_cap_are_independent():
    with pytest.raises(ValueError,match='Expanded'):module.inspect_bundle(gzip.compress(b'x'*(module.MAX_ARCHIVE_BYTES+1)))
    with pytest.raises(ValueError,match='TeX member'):module.inspect_bundle(bundle([('large.tex',b'x'*(module.MAX_MEMBER_BYTES+1))]))

def test_plain_gzip_tex_and_pdf_sources_have_explicit_coverage():
    assert artifact(gzip.compress(b'$x=1$'))['records'][0]['latex']=='$x=1$'
    pdf=artifact(b'%PDF-original synthetic placeholder')
    assert pdf['records']==[] and not pdf['processing_complete'] and pdf['coverage']['unsupported']

def test_non_utf8_member_remains_partial_without_guessed_decoding():
    result=artifact(bundle([('good.tex',b'$x=1$'),('unknown.tex',b'\xff\xfeinvalid')]))
    assert len(result['records'])==1 and result['coverage']['refused_tex_members']==1 and not result['processing_complete']

def test_separate_members_with_identical_basename_and_bytes_keep_distinct_ids():
    result=artifact(bundle([('a/main.tex',b'$x=1$'),('b/main.tex',b'$x=1$')]))
    assert len({r['id'] for r in result['records']})==2
    assert {r['source']['archive_member_path'] for r in result['records']}=={'a/main.tex','b/main.tex'}
    assert all(r['pdf_alignment']=='not_verified' and r['source']['page'] is None for r in result['records'])

def test_html_and_empty_bodies_are_not_author_source():
    for raw in (b'',b'<html>error</html>',b' <!DOCTYPE HTML>'):
        with pytest.raises(ValueError):module.inspect_bundle(raw)

def test_directory_entries_are_skipped_without_creating_directories():
    stream=BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as archive:
        info=tarfile.TarInfo('original/');info.type=tarfile.DIRTYPE;archive.addfile(info)
        info=tarfile.TarInfo('original/main.tex');info.size=3;archive.addfile(info,BytesIO(b'$x$'))
    assert module.inspect_bundle(stream.getvalue())['files'][0]['basename']=='main.tex'

def test_source_identity_matches_pdf_persistence_versioned_revision():
    paper=dict(id='2501.00655v1',version=1,pdf_sha256='a'*64)
    identifier,revision=module.source_identity(paper)
    assert revision=='2501.00655v1'
    assert identifier==hashlib.sha256(b'2501.00655v1:'+b'a'*64).hexdigest()[:32]
    assert identifier!=hashlib.sha256(b'1:'+b'a'*64).hexdigest()[:32]
