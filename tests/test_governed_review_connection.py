from contextlib import contextmanager
import hashlib
import pytest
from nsai import governed_store as governed

@pytest.fixture
def review_db(monkeypatch):
    original=b'Original synthetic engineering source.'
    digest=hashlib.sha256(original).hexdigest()
    state=dict(author='operator',record_digest=digest,document=(original,digest),reviewed=False,inserted=False,audited=False,connections=0,active=False)
    class Cursor:
        def __init__(self,row):self.row=row
        def fetchone(self):return self.row
    class Connection:
        def execute(self,sql,parameters=None):
            if 'SELECT author,document_id,source_sha256' in sql:return Cursor((state['author'],'doc-id',state['record_digest'],['doc-id','other-source'],True))
            if 'SELECT nsai_sources_visible' in sql:return Cursor((True,))
            if 'SELECT 1 FROM governed_reviews' in sql:return Cursor((1,) if state['reviewed'] else None)
            if 'SELECT source_bytes,original_sha256' in sql:return Cursor(state['document'])
            if sql.startswith('INSERT INTO governed_reviews'):state['inserted']=True
            return Cursor(None)
    @contextmanager
    def connect():
        assert not state['active'],'Nested pool acquisition while transaction holds a slot'
        state['active']=True;state['connections']+=1
        try:yield Connection()
        finally:state['active']=False
    monkeypatch.setattr(governed.store,'connect',connect)
    # Exercise the real original_source helper pre-fix: it must try the forbidden second slot.
    def audit(conn,*args):
        assert state['active'] and state['inserted']
        assert args[-1]['source_ids']==['doc-id','other-source']
        state['audited']=True
        return 'synthetic-audit-receipt'
    monkeypatch.setattr(governed.w,'audit',audit)
    return state

def test_review_uses_one_transaction_connection(review_db):
    result=governed.review('reviewer','record-id','reviewed','Independent review complete')
    assert result['state']=='reviewed' and result['authority_granted'] is False
    assert review_db['connections']==1 and review_db['inserted'] and review_db['audited']

@pytest.mark.parametrize('mutation,exception,message',[
    (dict(document=None),LookupError,'Original source unavailable'),
    (dict(document=(None,'0'*64)),LookupError,'Original source unavailable'),
    (dict(document=(b'tampered','0'*64)),ValueError,'Source integrity failure'),
    (dict(record_digest='0'*64),ValueError,'Stale source binding'),
    (dict(author='reviewer'),PermissionError,'Independent reviewer required'),
    (dict(reviewed=True),ValueError,'Record already reviewed')])
def test_integrity_and_authority_failure_never_writes(review_db,mutation,exception,message):
    review_db.update(mutation)
    with pytest.raises(exception,match=message):
        governed.review('reviewer','record-id','reviewed','Independent review complete')
    assert not review_db['inserted'] and not review_db['audited']
