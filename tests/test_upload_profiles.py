import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from nsai.upload_limits import select_profile


def test_default_and_evaluation_envelopes_keep_text_budget():
    default = select_profile()
    standard = select_profile('standard-evaluation')
    assert (default.max_bytes, default.max_pages) == (2097152, 100)
    assert (standard.max_bytes, standard.max_pages) == (26214400, 250)
    assert default.max_chars == standard.max_chars == 200000
    assert standard.base64_chars == 34952536
    with pytest.raises(AttributeError):
        standard.max_pages = 1000


@pytest.mark.parametrize('profile', ['', 'standard', 'STANDARD-EVALUATION', ' standard-evaluation', 'large'])
def test_unknown_profile_refused(profile):
    with pytest.raises(ValueError, match='upload profile'):
        select_profile(profile)


@pytest.mark.parametrize('profile,pages,accepted', [
    ('default', 100, True), ('default', 101, False),
    ('standard-evaluation', 250, True), ('standard-evaluation', 251, False),
])
def test_actual_child_page_boundaries(profile, pages, accepted):
    # A fresh process exercises startup selection and the real bounded PDF parser.
    program = '''
from io import BytesIO
import json
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from nsai.ingestion import parse_source
w=PdfWriter()
for _ in range(PAGES):w.add_blank_page(width=612,height=792)
font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
w.pages[0][NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):w._add_object(font)})})
stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 60 700 Td (Envelope check) Tj ET')
w.pages[0][NameObject('/Contents')]=w._add_object(stream)
b=BytesIO();w.write(b)
try:
 r=parse_source(b.getvalue(),'pages.pdf')
 print(json.dumps({'accepted':True,'pages':r['page_count']}))
except ValueError as e:print(json.dumps({'accepted':False,'error':str(e)}))
'''.replace('PAGES', str(pages))
    result = subprocess.run([sys.executable, '-c', program],
        env={**os.environ, 'NSAI_UPLOAD_PROFILE': profile, 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')}, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data['accepted'] is accepted, data
    if accepted:
        assert data['pages'] == pages


def test_invalid_profile_stops_service_import_before_credentials():
    result = subprocess.run([sys.executable, '-c', 'import nsai.api'],
        env={**os.environ, 'NSAI_UPLOAD_PROFILE': 'invalid', 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')}, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert 'Invalid server upload profile' in result.stderr
