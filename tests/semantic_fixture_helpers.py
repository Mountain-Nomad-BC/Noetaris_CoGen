"""Synthetic encoder for database lifecycle tests; never semantic-quality evidence."""
import asyncio
import json
import os
from pathlib import Path


def configure_authority():
    entries=[]
    for name,role in [('alice','operator'),('bob','operator'),('admin','admin')]:
        path=Path('/tmp/fixture-user-'+name)
        path.write_text(('owned-fixture-credential-'+name).ljust(48,'x'))
        entries.append(dict(actor='local-user-'+name,role=role,token_file=str(path)))
    registry=Path('/tmp/fixture-identities.json')
    registry.write_text(json.dumps(dict(schema_version='nsai.local-identities/1',identities=entries)))
    os.environ['NSAI_LOCAL_IDENTITIES_FILE']=str(registry)


def mixed_extraction_fixture():
    """Known native text plus a differing synthetic OCR candidate; not OCR quality."""
    from io import BytesIO
    from unittest.mock import patch
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject,NumberObject
    from nsai import ocr_worker
    from nsai.ingestion import parse_source
    writer=PdfWriter();page=writer.add_blank_page(width=100,height=100)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    image=DecodedStreamObject();image.set_data(b'\x00');image.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(1),NameObject('/Height'):NumberObject(1),NameObject('/BitsPerComponent'):NumberObject(8),NameObject('/ColorSpace'):NameObject('/DeviceGray')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)}),NameObject('/XObject'):DictionaryObject({NameObject('/Im1'):writer._add_object(image)})})
    content=DecodedStreamObject();content.set_data(b'BT /F1 10 Tf 10 70 Td (Native text) Tj ET q 1 0 0 1 0 0 cm /Im1 Do Q')
    page[NameObject('/Contents')]=writer._add_object(content);output=BytesIO();writer.write(output);data=output.getvalue()
    native=parse_source(data,'mixed.pdf')
    def command(arguments,deadline):
        if arguments[0].endswith('pdftoppm'):Path(arguments[-1]+'.pgm').write_bytes(b'owned synthetic raster')
        else:Path(arguments[2]+'.tsv').write_text('level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n5\t1\t1\t1\t1\t1\t10\t20\t80\t30\t90\tChanged\n',encoding='utf-8')
    with patch('nsai.ocr_worker._command',side_effect=command):parsed=ocr_worker.extract_ocr(data,'mixed.pdf')
    # Parser releases may retain a trailing PDF text newline. Preserve the exact
    # native payload for custody comparisons rather than normalizing it here.
    assert native['raw_text'] in {'Native text','Native text\n'} and parsed['raw_text']=='Changed'
    return data,native,parsed


async def synthetic_encode(texts):
    from nsai.semantic_encoder import PINNED_MODEL_SHA256
    model=dict(name='sentence-transformers/all-MiniLM-L6-v2',sha256=PINNED_MODEL_SHA256,
               revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41',dimension=384,
               pooling='token-mean-overlap-compensated-special-mean')
    return dict(model_identity=model,vectors=[[1.0]+[0.0]*383 for _ in texts],
        coverage=[dict(input_tokens=1,covered_tokens=1,complete=True,max_sequence_length=256,
                       pooling=model['pooling']) for _ in texts])


def publish_pending():
    from nsai import semantic_jobs
    for _ in range(20):
        job=semantic_jobs.claim_next()
        if job is None:return
        result=asyncio.run(semantic_jobs.process_job(job,encode=synthetic_encode))
        if result['state']!='succeeded':raise AssertionError('Fixture publication did not succeed')
    raise AssertionError('Unexpected fixture queue size')
