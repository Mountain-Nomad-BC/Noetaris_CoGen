"""A new named subject must not silently inherit the previous question's evidence."""
from nsai import api


def prepare(monkeypatch):
    old=dict(id='a'*32,document_id='b'*32,locator='line:1',text='Motor-X maximum operating temperature is 75 C.',
             title='Old subject',revision='1',original_sha256='c'*64)
    calls=[]
    def retrieve(question,**scope):
        calls.append((question,scope))
        return [dict(old)] if 'Motor-X' in question else []
    monkeypatch.setattr(api,'library_retrieve',retrieve)
    monkeypatch.setattr(api.workflows,'claim_context',lambda *a,**kw:[])
    return calls,dict(working=[dict(role='user',text='Motor-X maximum operating temperature')])


def test_new_named_subject_with_pronoun_does_not_fall_back_to_old_subject(monkeypatch):
    calls,memory=prepare(monkeypatch)
    question='Does Motor-Z have an operating limit, and is it safe?'
    hits,matched,conflicts,citations=api.evidence(question,memory)
    assert hits==[] and citations==[]
    assert [question for question,_ in calls]==[question]


def test_plain_pronoun_can_use_previous_question_without_broadening_scope(monkeypatch):
    calls,memory=prepare(monkeypatch)
    monkeypatch.setattr(api.workflows,'source',lambda *a:dict(revision='1'))
    hits,*_=api.evidence('What is it?',memory,document_ids=['b'*32],revision='1')
    assert hits and len(calls)==2
    assert all(scope==dict(document_ids=['b'*32],revision='1',pages=None) for _,scope in calls)
