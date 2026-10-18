"""Native extraction survives selection of a different OCR representation."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import hashlib
import pytest
from nsai import ocr_worker
from nsai.ingestion import parse_source,validate_parsed_source,extraction_snapshot
from test_parser_implementation import pdf


def mixed_pdf(extra_native=False):
    from pypdf import PdfReader,PdfWriter
    from pypdf.generic import NameObject
    reader=PdfReader(BytesIO(pdf(raster=True)))
    reader.pages[0]['/Resources'][NameObject('/XObject')]=reader.pages[1]['/Resources']['/XObject']
    writer=PdfWriter();writer.add_page(reader.pages[0])
    if extra_native:writer.add_page(PdfReader(BytesIO(pdf())).pages[0])
    output=BytesIO();writer.write(output)
    return output.getvalue()


def ocr_alternative(monkeypatch,extra_native=False):
    data=mixed_pdf(extra_native);native=parse_source(data,'mixed.pdf')
    def command(arguments,deadline):
        if arguments[0].endswith('pdftoppm'):Path(arguments[-1]+'.pgm').write_bytes(b'owned synthetic raster')
        else:
            Path(arguments[2]+'.tsv').write_text('level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n5\t1\t1\t1\t1\t1\t10\t20\t80\t30\t90\tChanged\n',encoding='utf-8')
    monkeypatch.setattr(ocr_worker,'_command',command)
    return data,native,ocr_worker.extract_ocr(data,'mixed.pdf')


def test_ocr_selection_retains_the_entire_original_native_representation(monkeypatch):
    data,native,result=ocr_alternative(monkeypatch)
    assert result['raw_text']=='Changed' and native['raw_text']=='Native text'
    assert result['extraction_history']==[extraction_snapshot(native)]
    assert result['extraction_history'][0]['payload']['pages'][0]['status']=='ocr_required'
    assert result['pages'][0]['status']=='ocr' and result['original_sha256']==hashlib.sha256(data).hexdigest()
    assert validate_parsed_source(data,result) is result


def test_prior_native_and_ocr_snapshot_generation_remains_readable(monkeypatch):
    data,native,result=ocr_alternative(monkeypatch)
    native['parser_version']='nsai-bounded/2';result['parser_version']='nsai-bounded/2+ocr/3'
    result['extraction_history']=[extraction_snapshot(native)]
    assert validate_parsed_source(data,result) is result


def test_current_ocr_cannot_relabel_an_older_native_snapshot(monkeypatch):
    data,native,result=ocr_alternative(monkeypatch)
    native['parser_version']='nsai-bounded/2';result['extraction_history']=[extraction_snapshot(native)]
    with pytest.raises(ValueError,match='version mismatch'):validate_parsed_source(data,result)


@pytest.mark.parametrize('change',['omitted','hash','source','nested'])
def test_current_ocr_history_cannot_be_silently_dropped_or_rebound(monkeypatch,change):
    data,native,result=ocr_alternative(monkeypatch);result=deepcopy(result)
    if change=='omitted':result.pop('extraction_history')
    elif change=='hash':result['extraction_history'][0]['sha256']='0'*64
    elif change=='source':
        native['original_sha256']='0'*64;result['extraction_history']=[extraction_snapshot(native)]
    else:
        native['extraction_history']=[];result['extraction_history']=[extraction_snapshot(native)]
    with pytest.raises(ValueError):validate_parsed_source(data,result)


def test_snapshot_validation_does_not_move_pdf_parsing_into_the_api(monkeypatch):
    data,native,result=ocr_alternative(monkeypatch)
    import pypdf
    monkeypatch.setattr(pypdf,'PdfReader',lambda *args,**kw:pytest.fail('Original PDF parsing escaped the worker'))
    assert validate_parsed_source(data,result) is result


def test_ocr_on_one_page_cannot_drop_an_unchanged_native_page(monkeypatch):
    data,native,result=ocr_alternative(monkeypatch,extra_native=True)
    assert result['pages'][1]['status']=='native'
    result['spans']=[span for span in result['spans'] if span['page']==1]
    for field in ('chunks','normalization_map'):
        result[field]=[item for item in result[field] if item['locator'].startswith('page:1:')]
    result['raw_text']='Changed'
    with pytest.raises(ValueError,match='Unselected native extraction changed'):validate_parsed_source(data,result)
