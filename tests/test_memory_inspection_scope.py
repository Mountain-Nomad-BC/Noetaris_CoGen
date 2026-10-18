import pytest
from fastapi import HTTPException
from nsai import api


def prepare(monkeypatch):
    calls=[]
    monkeypatch.setattr(api.workflows,'source',lambda document:dict(revision='1',manifest=dict(documents=[dict(metadata=dict(pages=[dict(page=1)]))])))
    monkeypatch.setattr(api.workflows,'memory_context',lambda *args,**scope:calls.append((args,scope)) or scope)
    return calls


def test_memory_inspection_forwards_explicit_source_revision_and_pages(monkeypatch):
    calls=prepare(monkeypatch)
    scope=dict(document_ids=['a'*32,'b'*32],revision='1',pages=[1])
    assert api.memory('c'*32,identity=dict(actor='local-user-alice'),**scope)==scope
    assert calls==[(('local-user-alice','c'*32),scope)]


@pytest.mark.parametrize('scope',[dict(document_ids=[],revision='1'),
    dict(document_ids=['a'*32],revision='2'),dict(document_ids=['a'*32],pages=[2]),
    dict(document_ids=['a'*32,'a'*32])])
def test_invalid_or_stale_memory_scope_never_builds_memory(monkeypatch,scope):
    calls=prepare(monkeypatch)
    with pytest.raises(HTTPException) as caught:
        api.memory('c'*32,identity=dict(actor='local-user-alice'),**scope)
    assert caught.value.status_code==409 and calls==[]
