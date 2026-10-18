import pytest
from nsai import workflow_store
from nsai.retrieval import library


def test_unconfigured_encoder_keeps_lexical_contract(monkeypatch):
    monkeypatch.delenv('NSAI_ENCODER_URL',raising=False)
    hits=workflow_store.RetrievalHits([dict(id='a')],12)
    monkeypatch.setattr(workflow_store,'retrieve',lambda *a,**kw:hits)
    assert library.retrieve('question') is hits
    assert hits.coverage['semantic_state']=='not-configured'


def test_semantic_only_paraphrase_enters_ordinary_retrieval_with_fixed_scope(monkeypatch):
    monkeypatch.setenv('NSAI_ENCODER_URL','http://encoder:8092')
    monkeypatch.setattr(workflow_store,'retrieve',lambda *a,**kw:workflow_store.RetrievalHits([],12))
    calls=[]
    def semantic(question,limit,**scope):
        calls.append((question,limit,scope))
        return [dict(id='passage',document_id='chosen',text='insulation degradation')]
    monkeypatch.setattr(library,'semantic_hits',semantic)
    hits=library.retrieve('Why does the coating wear out?',document_ids=['chosen'],revision='2',pages=[3])
    assert hits[0]['id']=='passage'
    assert calls==[('Why does the coating wear out?',13,dict(document_ids=['chosen'],revision='2',pages=[3]))]
    assert hits.coverage['corpus_scope']=='authorized-current-publications'
    assert hits.coverage['exhaustive_answer'] is False


def test_unavailable_encoder_is_visible_and_does_not_broaden_scope(monkeypatch):
    monkeypatch.setenv('NSAI_ENCODER_URL','http://encoder:8092')
    monkeypatch.setattr(workflow_store,'retrieve',lambda *a,**kw:workflow_store.RetrievalHits([],12))
    def failed(*a,**kw):raise ValueError('untrusted response')
    monkeypatch.setattr(library,'semantic_hits',failed)
    hits=library.retrieve('question',document_ids=['chosen'])
    assert hits==[] and hits.coverage['semantic_state']=='unavailable'


def test_database_authority_errors_are_not_hidden_as_encoder_degradation(monkeypatch):
    monkeypatch.setenv('NSAI_ENCODER_URL','http://encoder:8092')
    monkeypatch.setattr(workflow_store,'retrieve',lambda *a,**kw:workflow_store.RetrievalHits([],12))
    def failed(*a,**kw):raise RuntimeError('schema drift')
    monkeypatch.setattr(library,'semantic_hits',failed)
    with pytest.raises(RuntimeError):library.retrieve('question')
