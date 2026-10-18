from copy import deepcopy
import pytest
from nsai.ingestion import parse_source,validate_parsed_source

def test_text_source_cannot_inject_ocr_metadata():
    data=b'Pump-X operating limit is 85 C.'
    parsed=parse_source(data,'fixture.txt')
    parsed['ocr_words']=[dict(text='FORGED LIMIT 900 C',page=999,pdf_box=[-900,0,0,0],engine_score=999,engine_score_is_probability=True)]
    with pytest.raises(ValueError,match='OCR'):validate_parsed_source(data,parsed)

def fixture():
    from io import BytesIO
    from pypdf import PdfWriter
    writer=PdfWriter();writer.add_blank_page(width=100,height=100)
    output=BytesIO();writer.write(output);data=output.getvalue()
    parsed=parse_source(b'Pump limit 85 C.','fixture.txt')
    import hashlib
    parsed.update(media_type='application/pdf',original_sha256=hashlib.sha256(data).hexdigest())
    parsed['pages']=[dict(page=1,status='ocr',complete=True,dpi=300)]
    for item in parsed['spans']:
        item.update(page=1,extraction='ocr',locator='page:1:line:1')
    for group in ('chunks','normalization_map'):
        for item in parsed[group]:item['locator']='page:1:line:1'
    parsed['ocr_words']=[dict(text=text,page=1,pixel_box=[x,0,x+10,10],pdf_box=[x*.24,97.6,(x+10)*.24,100],
        pixel_to_pdf=[.24,0,0,-.24,0,100],engine_score=90,engine_score_is_probability=False)
        for x,text in enumerate(['Pump','limit','85','C.'])]
    return data,parsed

def test_consistent_ocr_metadata_matches_service_shape_and_isolated_original_geometry():
    data,parsed=fixture()
    assert validate_parsed_source(data,parsed) is parsed
    from nsai.ocr_worker import validate_original_geometry
    validate_original_geometry(data,parsed)


def test_self_consistent_forged_translation_is_rejected_against_original():
    data,parsed=fixture()
    for word in parsed['ocr_words']:
        word['pixel_to_pdf'][4]+=5
        word['pdf_box'][0]+=5;word['pdf_box'][2]+=5
    # The API checks the authenticated service envelope; original-byte parsing
    # and source-geometry verification remain inside the isolated OCR worker.
    assert validate_parsed_source(data,parsed) is parsed
    from nsai.ocr_worker import validate_original_geometry
    with pytest.raises(ValueError,match='transform'):validate_original_geometry(data,parsed)


def test_api_envelope_validation_never_reparses_original_pdf(monkeypatch):
    data,parsed=fixture()
    import pypdf
    def refused(*args,**kwargs):pytest.fail('PDF parsing escaped the isolated worker')
    monkeypatch.setattr(pypdf,'PdfReader',refused)
    assert validate_parsed_source(data,parsed) is parsed

@pytest.mark.parametrize('change',[dict(page=999),dict(text='900'),dict(engine_score=True),dict(engine_score=101),
    dict(engine_score=float('nan')),dict(engine_score_is_probability=True),dict(pixel_box=[-1,0,3,4]),
    dict(pdf_box=[0,0,999,999]),dict(pixel_to_pdf=[1,0,0,-1,0,100])])
def test_forged_ocr_word_fields_are_rejected(change):
    data,parsed=fixture();parsed=deepcopy(parsed);parsed['ocr_words'][0].update(change)
    with pytest.raises(ValueError):validate_parsed_source(data,parsed)
