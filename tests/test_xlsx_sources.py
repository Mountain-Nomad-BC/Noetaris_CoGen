from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile
import pytest
from nsai.ingestion import parse_source,validate_parsed_source
from xlsx_fixture_helpers import workbook,NS


def test_raw_numbers_formulas_caches_hidden_and_late_cells_are_retained():
    data=workbook();parsed=parse_source(data,'source.xlsx');evidence=parsed['structured_data']
    first,hidden=evidence['sheets']
    assert evidence['cell_count']==8 and first['name']=='Visible' and hidden['state']=='hidden'
    a,b,c=first['rows'][0]['cells']
    assert a['raw_value']=='001.2300' and a['cell_type']=='n'
    assert b['formula']==dict(text='SUM(A1:A2)',attributes=[]) and b['raw_value']=='999.1'
    assert c['text']==' leading text' and c['raw_value']=='0' and c['shared_string']['xml']
    assert first['rows'][1]['cells'][0]['coordinate']=='Z9'
    assert first['rows'][1]['cells'][0]['locator']=='sheet:Visible:cell:Z9'
    assert [cell['raw_value'] for cell in hidden['rows'][0]['cells']]==['0','#DIV/0!',None,None]
    assert hidden['rows'][0]['cells'][2]['text'] is None and hidden['rows'][0]['cells'][3]['text']==''
    assert dict((a['name'],a['value']) for a in hidden['rows'][0]['attributes'])['hidden']=='1'
    assert any('mergeCell' in section for section in first['sections'])
    assert validate_parsed_source(data,deepcopy(parsed))==parsed


@pytest.mark.parametrize('mutate',[
    lambda p:p['structured_data']['sheets'].pop(),
    lambda p:p['structured_data']['sheets'][0]['rows'][0]['cells'][0].update(raw_value='1.23'),
    lambda p:p['structured_data']['sheets'][0]['rows'][0]['cells'][1].update(formula=None),
    lambda p:p['chunks'].pop(),lambda p:p.update(page_count=True),
])
def test_source_reconstruction_refuses_changed_or_lost_workbook_data(mutate):
    data=workbook();parsed=parse_source(data,'source.xlsx');mutate(parsed)
    with pytest.raises(ValueError,match='does not match original'):validate_parsed_source(data,parsed)


@pytest.mark.parametrize('name',['../outside.xml','/absolute.xml','xl/vbaProject.bin','xl/comments/comment1.xml','xl/drawings/drawing1.xml'])
def test_active_unsafe_or_unqualified_parts_reject_whole_workbook(name):
    with pytest.raises(ValueError):parse_source(workbook(extra={name:b'unqualified'}),'source.xlsx')


def test_duplicate_entries_and_zip_bombs_are_refused():
    data=BytesIO(workbook())
    with pytest.warns(UserWarning):
        with ZipFile(data,'a') as archive:archive.writestr('xl/workbook.xml',b'duplicate')
    with pytest.raises(ValueError,match='duplicate'):parse_source(data.getvalue(),'source.xlsx')
    with pytest.raises(ValueError,match='compression'):parse_source(workbook(extra={'xl/styles.xml':b'x'*100000}),'source.xlsx')


@pytest.mark.parametrize('encoding',['utf-8','utf-16'])
def test_xml_dtd_and_entities_are_forbidden_in_any_admitted_encoding(encoding):
    xml='<?xml version="1.0" encoding="'+encoding+'"?><!DOCTYPE workbook [<!ENTITY x SYSTEM "file:///should-never-read">]><workbook xmlns="'+NS+'">&x;</workbook>'
    with pytest.raises(ValueError,match='Unsafe or malformed'):parse_source(workbook(overrides={'xl/workbook.xml':xml.encode(encoding)}),'source.xlsx')


def test_attribute_names_never_become_source_authority_fields():
    from nsai.source_dependencies import collect_sources
    raw=f'<worksheet xmlns="{NS}"><sheetData><row r="1" document_id="foreign"><c r="A1" source_ids="secret"><v>1</v></c></row></sheetData></worksheet>'.encode()
    parsed=parse_source(workbook(overrides={'xl/worksheets/sheet1.xml':raw}),'source.xlsx')
    assert collect_sources(parsed)==[]


def test_workbook_analysis_requires_sheet_and_never_trusts_cached_formula(monkeypatch):
    from nsai import workflow_store
    from nsai.table_analysis import analyze_source,TableAnalysisInput
    data=workbook();parsed=parse_source(data,'source.xlsx')
    source=dict(media_type=parsed['media_type'],revision='1',original_sha256=parsed['original_sha256'],
        manifest=dict(documents=[dict(metadata=dict(structured_data=parsed['structured_data']))]))
    monkeypatch.setattr(workflow_store,'source',lambda _:source)
    monkeypatch.setattr(workflow_store,'original_source',lambda _:(data,parsed['media_type']))
    with pytest.raises(ValueError,match='exact worksheet'):analyze_source('a'*32,TableAnalysisInput(value_column=1))
    result=analyze_source('a'*32,TableAnalysisInput(value_column=1,sheet='Visible'))
    assert result['groups'][0]['value']=='1.2300' and result['coverage']['excluded_records']==1
    assert result['worksheet']['name']=='Visible'
    with pytest.raises(ValueError,match='Formula results'):analyze_source('a'*32,TableAnalysisInput(value_column=2,sheet='Visible'))
    with pytest.raises(ValueError,match='Boolean, date or error'):analyze_source('a'*32,TableAnalysisInput(value_column=1,sheet='Hidden'))
    result=analyze_source('a'*32,TableAnalysisInput(value_column=1,sheet='Hidden',operation='count'))
    assert result['groups'][0]['value']=='1' and result['worksheet']['state']=='hidden'
