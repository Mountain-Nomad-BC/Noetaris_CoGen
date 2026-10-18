import copy
import hashlib
from io import BytesIO
import json
import subprocess
import sys
import base64
import os
import random
from pathlib import Path
import pytest
from pypdf.generic import ArrayObject,BooleanObject,DictionaryObject,NameObject
from nsai.ingestion import parse_source,validate_parsed_source,MAX_PARSER_OUTPUT_BYTES
from nsai.ocr_quality import error_rates,AffineTransform,box_iou
from nsai.formulas import evaluate_formula

def pdf(contents=b'BT /F1 12 Tf 72 720 Td (Native text) Tj ET', *, compress=False, raster=False, array=False):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject,ArrayObject,NumberObject
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject();stream.set_data(contents)
    reference=writer._add_object(stream.flate_encode() if compress else stream)
    page[NameObject('/Contents')]=ArrayObject([reference,reference]) if array else reference
    if raster:
        image=DecodedStreamObject();image.set_data(b'\x00')
        image.update({NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(1),NameObject('/Height'):NumberObject(1)})
        blank=writer.add_blank_page(width=612,height=792)
        blank[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im1'):writer._add_object(image)})})
    result=BytesIO();writer.write(result);return result.getvalue()


def pdf_with_filter(filter_name, *, decode_params=None):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject,NumberObject
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    stream=DecodedStreamObject();stream.set_data(b'BT (Native text) Tj ET')
    stream[NameObject('/Filter')]=NameObject(filter_name)
    if decode_params is not None:
        stream[NameObject('/DecodeParms')]=DictionaryObject({
            NameObject('/Predictor'):NumberObject(decode_params)})
    page[NameObject('/Contents')]=writer._add_object(stream)
    result=BytesIO();writer.write(result);return result.getvalue()


def pdf_with_invalid_decode_params(value):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject,NameObject
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    stream=DecodedStreamObject();stream.set_data(b'BT (Native text) Tj ET')
    stream[NameObject('/Filter')]=NameObject('/FlateDecode')
    stream[NameObject('/DecodeParms')]=value
    page[NameObject('/Contents')]=writer._add_object(stream)
    result=BytesIO();writer.write(result);return result.getvalue()


def pdf_with_invalid_resources(resources):
    from pypdf import PdfWriter
    from pypdf.generic import NameObject
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    page[NameObject('/Resources')]=resources
    result=BytesIO();writer.write(result);return result.getvalue()


def pdf_with_false_contents():
    from pypdf import PdfWriter
    from pypdf.generic import BooleanObject,NameObject
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    page[NameObject('/Contents')]=BooleanObject(False)
    result=BytesIO();writer.write(result);return result.getvalue()


def deterministic_pdf_mutations(count):
    from pypdf import PdfWriter
    writer=PdfWriter();writer.add_blank_page(width=612,height=792)
    result=BytesIO();writer.write(result);seed=result.getvalue()
    randomizer=random.Random(20261017)
    for case in range(count):
        data=bytearray(seed);operation=case%4
        if operation==0 and data:
            data[randomizer.randrange(len(data))]^=1<<randomizer.randrange(8)
        elif operation==1 and data:
            position=randomizer.randrange(len(data))
            del data[position:position+randomizer.randrange(1,min(32,len(data)-position)+1)]
        elif operation==2:
            position=randomizer.randrange(len(data)+1)
            data[position:position]=bytes(randomizer.randrange(256) for _ in range(randomizer.randrange(1,24)))
        else:
            data=data[:randomizer.randrange(0,len(data)+1)]
        if case in {37,81}:
            yield case,bytes(data)


def pdf_with_compressed_object_stream(padding=b''):
    import struct
    import zlib
    bodies=[
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
        b'/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 '
        b'/BaseFont /Helvetica >> >> >> /Contents 6 0 R >>',
    ]
    offsets_in_stream=[0]
    for body in bodies[:-1]:
        offsets_in_stream.append(offsets_in_stream[-1]+len(body)+1)
    header=b'1 0 2 '+str(offsets_in_stream[1]).encode()+b' 3 '+str(offsets_in_stream[2]).encode()+b' '
    decoded=header+b' '.join(bodies)+b' '+padding
    encoded=zlib.compress(decoded)
    object_stream=(
        b'<< /Type /ObjStm /N 3 /First '+str(len(header)).encode()
        +b' /Length '+str(len(encoded)).encode()+b' /Filter /FlateDecode >>\nstream\n'
        +encoded+b'\nendstream'
    )
    content=b'BT /F1 12 Tf 72 720 Td (Object stream OK) Tj ET'
    content_stream=b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream'
    def indirect(number,body):
        return str(number).encode()+b' 0 obj\n'+body+b'\nendobj\n'
    data=b'%PDF-1.5\n'
    offsets={}
    offsets[4]=len(data);data+=indirect(4,object_stream)
    offsets[6]=len(data);data+=indirect(6,content_stream)
    offsets[5]=len(data)
    entries=[(0,0,65535),(2,4,0),(2,4,1),(2,4,2),(1,offsets[4],0),(1,offsets[5],0),(1,offsets[6],0)]
    xref=b''.join(struct.pack('>BIH',*entry) for entry in entries)
    xref_stream=(
        b'<< /Type /XRef /Size 7 /Root 1 0 R /W [1 4 2] /Index [0 7] '
        +b'/Length '+str(len(xref)).encode()+b' >>\nstream\n'+xref+b'\nendstream'
    )
    data+=indirect(5,xref_stream)
    return data+b'startxref\n'+str(offsets[5]).encode()+b'\n%%EOF\n'


def test_flate_bomb_rejected_and_decoder_restored():
    from pypdf import filters
    before=filters.decode_stream_data
    data=pdf(b' '*(9*1024*1024),compress=True)
    assert len(data)<2*1024*1024
    with pytest.raises(ValueError,match='budget'):parse_source(data,'bomb.pdf')
    assert filters.decode_stream_data is before
    assert parse_source(pdf(compress=True),'safe.pdf')['complete']


@pytest.mark.parametrize('case,data',list(deterministic_pdf_mutations(82)),ids=['xref-trailer-type','xref-entry-type'])
def test_malformed_pdf_xref_is_a_controlled_rejection(case,data,capsys):
    with pytest.raises(ValueError,match='Malformed or unsupported PDF structure'):
        parse_source(data,'mutated-xref.pdf')
    if case==81:
        assert 'Logging error' not in capsys.readouterr().err


def test_compressed_object_stream_is_extracted_and_expansion_is_bounded():
    import gc
    import tracemalloc
    from pypdf import filters
    original=filters.decode_stream_data
    valid=pdf_with_compressed_object_stream()
    result=parse_source(valid,'object-stream.pdf')
    assert result['complete'] and 'Object stream OK' in result['raw_text']
    bomb=pdf_with_compressed_object_stream(b' '*(9*1024*1024))
    assert len(bomb)<16*1024
    gc.collect()
    tracemalloc.start()
    with pytest.raises(ValueError,match='PDF stream exceeds extraction budget'):
        parse_source(bomb,'object-stream-bomb.pdf')
    _,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak<24*1024*1024
    assert filters.decode_stream_data is original
    assert parse_source(valid,'object-stream-recovered.pdf')['complete']


@pytest.mark.parametrize('data,match',[
    (pdf_with_filter('/ASCII85Decode'),'codec unsupported'),
    (pdf_with_filter('/FlateDecode',decode_params=2),'predictor unsupported'),
],ids=['unsupported-codec','unsupported-predictor'])
def test_unsupported_pdf_decode_rejects_and_next_parse_recovers(data,match):
    from pypdf import filters
    original=filters.decode_stream_data
    with pytest.raises(ValueError,match=match):
        parse_source(data,'unsupported.pdf')
    assert filters.decode_stream_data is original
    assert parse_source(pdf(compress=True),'recovered.pdf')['complete']


@pytest.mark.parametrize('value',[
    pytest.param(BooleanObject(True),id='boolean'),
    pytest.param(NameObject('/Unexpected'),id='name'),
    pytest.param(ArrayObject(),id='array'),
])
def test_malformed_pdf_decode_parameters_are_rejected_and_next_parse_recovers(value):
    from pypdf import filters
    original=filters.decode_stream_data
    with pytest.raises(ValueError,match='Malformed PDF decode parameters'):
        parse_source(pdf_with_invalid_decode_params(value),'malformed-decode-params.pdf')
    assert filters.decode_stream_data is original
    assert parse_source(pdf(compress=True),'recovered-after-decode-params.pdf')['complete']


@pytest.mark.parametrize('resources',[
    pytest.param(BooleanObject(True),id='boolean-resource-dictionary'),
    pytest.param(NameObject('/Unexpected'),id='name-resource-dictionary'),
    pytest.param(DictionaryObject({NameObject('/XObject'):BooleanObject(True)}),id='boolean-xobject-dictionary'),
    pytest.param(DictionaryObject({NameObject('/XObject'):ArrayObject()}),id='array-xobject-dictionary'),
    pytest.param(DictionaryObject({NameObject('/XObject'):DictionaryObject({
        NameObject('/Im1'):BooleanObject(True)})}),id='boolean-xobject-entry'),
])
def test_malformed_pdf_resource_objects_are_rejected_and_next_parse_recovers(resources):
    from pypdf import filters
    original=filters.decode_stream_data
    with pytest.raises(ValueError,match='Malformed PDF'):
        parse_source(pdf_with_invalid_resources(resources),'malformed-resources.pdf')
    assert filters.decode_stream_data is original
    assert parse_source(pdf(compress=True),'recovered-after-resources.pdf')['complete']


def test_false_valued_pdf_content_stream_is_rejected_and_next_parse_recovers():
    with pytest.raises(ValueError,match='Malformed PDF page content stream'):
        parse_source(pdf_with_false_contents(),'false-content.pdf')
    assert parse_source(pdf(compress=True),'recovered-after-malformed.pdf')['complete']


def test_parser_service_recovers_after_malformed_pdf_job(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from nsai.parser import app
    token=tmp_path/'parser-token';token.write_text('synthetic-parser-token-0123456789')
    monkeypatch.setenv('NSAI_PARSER_TOKEN_FILE',str(token))
    monkeypatch.setenv('PYTHONPATH',str(Path(__file__).resolve().parents[1]/'src'))
    headers={'Authorization':'Bearer synthetic-parser-token-0123456789'}
    with TestClient(app) as client:
        malformed=dict(filename='malformed.pdf',
            data=base64.b64encode(pdf_with_false_contents()).decode())
        rejected=client.post('/parse',json=malformed,headers=headers)
        assert rejected.status_code==422
        malformed_resources=dict(filename='malformed-resources.pdf',
            data=base64.b64encode(pdf_with_invalid_resources(BooleanObject(True))).decode())
        rejected_resources=client.post('/parse',json=malformed_resources,headers=headers)
        assert rejected_resources.status_code==422
        for case,data in deterministic_pdf_mutations(82):
            malformed_xref=dict(filename=f'malformed-xref-{case}.pdf',
                data=base64.b64encode(data).decode())
            rejected_xref=client.post('/parse',json=malformed_xref,headers=headers)
            assert rejected_xref.status_code==422
        valid=dict(filename='valid.pdf',data=base64.b64encode(pdf(compress=True)).decode())
        accepted=client.post('/parse',json=valid,headers=headers)
        assert accepted.status_code==200,accepted.text[:200]
        assert accepted.json()['complete'] is True


def test_content_array_aggregate_is_bounded():
    with pytest.raises(Exception,match='output bytes|budget'):
        parse_source(pdf(b' '*(5*1024*1024),compress=True,array=True),'array.pdf')

def test_mixed_pdf_keeps_native_and_reports_raster_gap():
    result=parse_source(pdf(raster=True),'mixed.pdf')
    assert [page['status'] for page in result['pages']]==['native','ocr_required']
    assert result['spans'][0]['page']==1
    assert not result['complete']
    assert any('INCOMPLETE' in warning for warning in result['warnings'])

def test_scanned_pdf_is_explicit_empty_ocr_required_receipt():
    result=parse_source(pdf(contents=b'',raster=True),'scan.pdf')
    assert result['spans']==[] and result['chunks']==[]
    assert result['pages'][1]['status']=='ocr_required'
    assert not result['complete']

def test_ocr_tsv_geometry_and_non_probability_contract(tmp_path):
    from nsai.ocr_worker import _read_tsv
    path=tmp_path/'page.tsv'
    header='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
    path.write_text(header+'5\t1\t1\t1\t1\t1\t10\t20\t30\t40\t90\tPrinted\n')
    text,words=_read_tsv(path,1,100,100)
    assert text=='Printed' and not words[0]['engine_score_is_probability']
    path.write_text(header+'5\t1\t1\t1\t1\t1\t10\t20\t300\t40\t90\tPrinted\n')
    with pytest.raises(ValueError):_read_tsv(path,1,100,100)

def test_unicode_child_utf8_envelope_succeeds():
    data=('\U0001f600'*150000).encode()
    payload=json.dumps(dict(filename='unicode.txt',data=base64.b64encode(data).decode())).encode()
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
    child=subprocess.run([sys.executable,'-m','nsai.parser_child'],input=payload,capture_output=True,timeout=20,env=env)
    assert child.returncode==0,child.stderr.decode()
    assert len(child.stdout)<MAX_PARSER_OUTPUT_BYTES
    assert json.loads(child.stdout)['raw_text']=='\U0001f600'*150000

@pytest.mark.parametrize('mutation',['original','chunkhash','offset','end_offset','offset_map','text','pages'])
def test_untrusted_worker_custody_rejected(mutation):
    data=b'original text';result=parse_source(data,'file.txt')
    if mutation=='original':result['original_sha256']='a'*64
    if mutation=='chunkhash':result['chunks'][0]['sha256']='a'*64
    if mutation=='offset':result['chunks'][0]['offset']=1
    if mutation=='end_offset':result['chunks'][0]['end_offset']+=1
    if mutation=='offset_map':result['normalization_map'][0]['offset_map'][0]['raw'][0]+=1
    if mutation=='text':result['chunks'][0]['text']='forged'
    if mutation=='pages':result['pages']=[]
    with pytest.raises(ValueError):validate_parsed_source(data,result)

def test_normalization_preserves_lineage_and_chunk_interval():
    result=parse_source('  e\u0301\t  original  \r\nnext'.encode(),'normal.txt')
    entry=result['normalization_map'][0]
    assert entry['raw_text']=='  e\u0301\t  original  \r\n'
    assert result['spans'][0]['text']=='\u00e9 original'
    assert entry['offset_map']==[
        dict(normalized=[0,1],raw=[2,4],mode='partition'),
        dict(normalized=[1,2],raw=[4,7],mode='partition'),
        dict(normalized=[2,10],raw=[7,15],mode='linear')]
    chunk=result['chunks'][0]
    assert result['spans'][0]['text'][chunk['offset']:chunk['end_offset']]==chunk['text']

def test_normalization_offset_map_handles_hangul_composition_and_whitespace_roundtrip():
    from nsai.normalization import line_offset_map,validate_line_offset_map
    raw='\u1100\u1161\u11a8\t value  \r\n'
    normalized,offset_map=line_offset_map(raw)
    assert normalized=='\uac01 value'
    assert offset_map[0]==dict(normalized=[0,1],raw=[0,3],mode='partition')
    assert offset_map[1]==dict(normalized=[1,2],raw=[3,5],mode='partition')
    assert offset_map[2]==dict(normalized=[2,7],raw=[5,10],mode='linear')
    assert validate_line_offset_map(raw,normalized,offset_map)

def test_normalization_offset_map_compresses_repeated_combining_sequences():
    from nsai.normalization import line_offset_map
    raw='e\u0301'*10000
    normalized,offset_map=line_offset_map(raw)
    assert normalized=='\u00e9'*10000
    assert offset_map==[dict(normalized=[0,10000],raw=[0,20000],mode='partition')]

def test_normalization_maps_whitespace_before_combining_marks():
    from nsai.normalization import line_offset_map
    normalized,offset_map=line_offset_map('a\t\u0327b')
    assert normalized=='a \u0327b'
    assert offset_map==[dict(normalized=[0,4],raw=[0,4],mode='linear')]

def test_normalized_selection_maps_back_to_exact_or_covering_raw_ranges():
    from nsai.normalization import line_offset_map,raw_ranges_for_normalized_range
    normalized,offset_map=line_offset_map('  e\u0301\t  original  ')
    assert raw_ranges_for_normalized_range(offset_map,0,1)==[(2,4)]
    assert raw_ranges_for_normalized_range(offset_map,1,2)==[(4,7)]
    assert raw_ranges_for_normalized_range(offset_map,2,len(normalized))==[(7,15)]
    with pytest.raises(ValueError):raw_ranges_for_normalized_range(offset_map,0,len(normalized)+1)
    with pytest.raises(ValueError):raw_ranges_for_normalized_range([offset_map[0],offset_map[2]],0,len(normalized))

def test_normalization_offset_maps_match_canonical_cleaner_for_unicode_cases():
    from nsai.ingestion import clean_text
    from nsai.normalization import line_offset_map,validate_line_offset_map
    randomizer=random.Random(42017)
    alphabet=['a','e',' ','\t','\u0301','\u0327','\u1100','\u1161','\u11a8','\u00e9','\u212b','\u0344']
    for _ in range(1000):
        raw=''.join(randomizer.choice(alphabet) for _ in range(randomizer.randrange(80)))
        raw+=randomizer.choice(['','\r','\n','\r\n'])
        normalized,offset_map=line_offset_map(raw)
        assert normalized==clean_text(raw.rstrip('\r\n'))
        assert validate_line_offset_map(raw,normalized,offset_map)

def test_long_chunks_prefer_word_boundaries_and_preserve_contiguous_offsets():
    from nsai.text_chunks import iter_text_chunks
    text='a'*1198+' '+('word '*300)
    chunks=list(iter_text_chunks(text))
    assert chunks[0][0]==0 and chunks[0][1].endswith(' ')
    assert all(len(part)<=1200 for _,part in chunks)
    assert ''.join(part for _,part in chunks)==text
    assert [offset for offset,_ in chunks]==[sum(len(part) for _,part in chunks[:index]) for index in range(len(chunks))]
    assert all(offset==0 or text[offset-1].isspace() or text[offset].isspace() for offset,_ in chunks)

def test_long_unbroken_token_uses_bounded_codepoint_safe_chunks():
    from nsai.text_chunks import iter_text_chunks
    text='x'*2501
    chunks=list(iter_text_chunks(text))
    assert [offset for offset,_ in chunks]==[0,1200,2400]
    assert ''.join(part for _,part in chunks)==text

def test_metrics_empty_and_over_one_are_honest():
    assert error_rates('a','xyz')['cer']==3
    assert error_rates('','unwanted')['cer'] is None
    assert error_rates('','unwanted')['empty_reference_false_positive']
    assert error_rates('e\u0301','\u00e9',normalized=True)['cer']==0

def test_affine_roundtrip_and_iou():
    transform=AffineTransform(0,4,-4,0,100,200)
    assert transform.inverse().point(*transform.point(12,24))==pytest.approx((12,24),abs=0.0001)
    assert box_iou((0,0,10,10),(0,0,10,10))==1
    with pytest.raises(ValueError):AffineTransform(1,1,1,1,0,0)

def test_formula_decimal_precision_and_provenance():
    result=evaluate_formula('0.1 + 0.2',source_sha256='a'*64,locator='page:1:line:1')
    assert result['value']=='0.3'
    assert result['status']=='unverified_formula_proposal'
    assert not result['generated_execution']

@pytest.mark.parametrize('expression',['__import__("os")','1/0','2**10000','1e999','True','x+1','[1]'])
def test_formula_unsafe_or_unsupported_rejected(expression):
    with pytest.raises(ValueError):evaluate_formula(expression,source_sha256='a'*64,locator='line:1')

def test_parser_service_auth_and_real_unicode_child(monkeypatch,tmp_path):
    from fastapi.testclient import TestClient
    from nsai.parser import app
    token=tmp_path/'parser-token';token.write_text('synthetic-test-token-0123456789abcdef')
    monkeypatch.setenv('NSAI_PARSER_TOKEN_FILE',str(token))
    monkeypatch.setenv('PYTHONPATH',str(Path(__file__).resolve().parents[1]/'src'))
    with TestClient(app) as client:
        payload=dict(filename='unicode.txt',data=base64.b64encode(('\U0001f600'*150000).encode()).decode())
        # HTTPX deliberately forbids nonASCII outbound headers; test that branch
        # through the service coroutine directly in the separate test below.
        assert client.post('/parse',json=payload).status_code==401
        response=client.post('/parse',json=payload,headers={'Authorization':'Bearer synthetic-test-token-0123456789abcdef'})
        assert response.status_code==200,response.text[:200]
        assert len(response.json()['raw_text'])==150000

def test_parser_non_ascii_authorization_returns_401(monkeypatch,tmp_path):
    import asyncio
    from fastapi import HTTPException
    from nsai.parser import parse,Source
    token=tmp_path/'token';token.write_text('synthetic-test-token-0123456789abcdef')
    monkeypatch.setenv('NSAI_PARSER_TOKEN_FILE',str(token))
    with pytest.raises(HTTPException) as error:
        asyncio.run(parse(Source(filename='x.txt',data='eA=='),authorization='Bearer \u00e9'))
    assert error.value.status_code==401

def test_pipe_budget_rejected_without_unbounded_capture():
    import asyncio
    from nsai.parser import _bounded_read
    async def run():
        reader=asyncio.StreamReader();reader.feed_data(b'x'*101);reader.feed_eof()
        with pytest.raises(ValueError):await _bounded_read(reader,100)
    asyncio.run(run())
