import hashlib
import pytest
from nsai.citation_anchors import quote_anchor


def hit(**updates):
    return dict(document_id='a'*32,original_sha256='b'*64,revision='1',
                text='The equation α² + β² = γ² is stated here.',locator='page:3:line:7',**updates)


def test_anchor_preserves_exact_unicode_and_source_binding_without_visual_claim():
    source=hit();anchor=quote_anchor(source)
    assert anchor['selector']['exact']==source['text']
    assert anchor['quote_sha256']==hashlib.sha256(source['text'].encode()).hexdigest()
    assert anchor['page']==3 and anchor['revision']=='1'
    assert anchor['original_sha256']=='b'*64
    assert anchor['status']=='page-only' and not anchor['visual_match_verified']
    assert 'start' not in anchor and 'pdf_box' not in anchor


@pytest.mark.parametrize('locator',['line:1','author-tex:page:3:line:7','ocr:page:3:line:7','page:3','page:0:line:1'])
def test_unaligned_namespaces_never_invent_pdf_page(locator):
    source=hit();source['locator']=locator;anchor=quote_anchor(source)
    assert anchor['page'] is None and anchor['status']=='unavailable'


@pytest.mark.parametrize('key,value',[
    ('document_id','foreign'),('original_sha256',''),('revision',1),
    ('text',''),('text','α'*32001),('locator',None),
], ids=['document-id','source-digest','revision-type','empty-quote','oversized-unicode','missing-locator'])
def test_invalid_or_oversized_binding_does_not_emit_a_selector(key,value):
    source=hit();source[key]=value
    assert quote_anchor(source) is None
