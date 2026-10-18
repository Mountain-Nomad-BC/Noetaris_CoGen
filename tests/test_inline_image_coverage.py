"""Inline and resource-backed raster content require the same honest coverage."""
from io import BytesIO
from pathlib import Path
import hashlib
import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from nsai.ingestion import parse_source,validate_parsed_source,extraction_snapshot


def inline_pdf(native=True,indirect=False,compressed=False,literal_only=False):
    writer=PdfWriter();page=writer.add_blank_page(width=100,height=100)
    resources=DictionaryObject()
    if native:
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        resources[NameObject('/Font')]=DictionaryObject({NameObject('/F1'):writer._add_object(font)})
    page[NameObject('/Resources')]=writer._add_object(resources) if indirect else resources
    stream=DecodedStreamObject()
    image=b'' if literal_only else b'q 100 0 0 100 0 0 cm BI /W 1 /H 1 /CS /G /BPC 8 ID \x00 EI Q '
    text=b'Literal BI ID EI text' if literal_only else b'Native text'
    stream.set_data(image+(b'BT /F1 10 Tf 1 g 10 70 Td ('+text+b') Tj ET' if native else b''))
    page[NameObject('/Contents')]=writer._add_object(stream.flate_encode() if compressed else stream)
    output=BytesIO();writer.write(output);return output.getvalue()


@pytest.mark.parametrize('native',[False,True])
@pytest.mark.parametrize('indirect',[False,True])
@pytest.mark.parametrize('compressed',[False,True])
def test_inline_raster_is_never_reported_as_complete_native_or_blank(native,indirect,compressed):
    original=inline_pdf(native,indirect,compressed);parsed=parse_source(original,'inline.pdf')
    assert parsed['pages']==[dict(page=1,status='ocr_required',native_text_present=native,complete=False)]
    assert parsed['complete'] is False and parsed['original_sha256']==hashlib.sha256(original).hexdigest()
    assert parsed['parser_version']=='nsai-bounded/3'
    assert validate_parsed_source(original,parsed) is parsed


def test_inline_image_markers_inside_text_do_not_trigger_ocr():
    parsed=parse_source(inline_pdf(literal_only=True),'literal.pdf')
    assert parsed['pages'][0]['status']=='native' and parsed['complete'] is True
    assert 'Literal BI ID EI text' in parsed['raw_text']


def test_inline_ocr_selection_keeps_exact_native_extraction(monkeypatch):
    from nsai import ocr_worker
    original=inline_pdf();native=parse_source(original,'inline.pdf')
    def command(arguments,deadline):
        if arguments[0].endswith('pdftoppm'):Path(arguments[-1]+'.pgm').write_bytes(b'owned synthetic raster')
        else:Path(arguments[2]+'.tsv').write_text('level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n5\t1\t1\t1\t1\t1\t10\t20\t80\t30\t90\tChanged\n',encoding='utf-8')
    monkeypatch.setattr(ocr_worker,'_command',command)
    parsed=ocr_worker.extract_ocr(original,'inline.pdf')
    assert parsed['raw_text']=='Changed' and parsed['extraction_history']==[extraction_snapshot(native)]
    assert validate_parsed_source(original,parsed) is parsed


@pytest.mark.parametrize('native',[False,True])
def test_inline_detection_does_not_parse_the_page_content_twice(monkeypatch,native):
    from pypdf.generic import ContentStream
    calls=[];original=ContentStream._parse_content_stream
    def count(self,*args,**kwargs):calls.append(1);return original(self,*args,**kwargs)
    monkeypatch.setattr(ContentStream,'_parse_content_stream',count)
    parse_source(inline_pdf(native),'inline.pdf')
    assert len(calls)==1
