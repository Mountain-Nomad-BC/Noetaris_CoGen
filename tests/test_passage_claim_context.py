from nsai import api


def test_later_passage_segment_participates_in_conflict_analysis(monkeypatch):
    hit=dict(id='passage',document_id='one',locator='line:1',text='Context\nRated 75 C',
             source_segments=[dict(locator='line:1'),dict(locator='line:2')])
    claims=[dict(id='a',document_id='one',locator='line:2',subject='motor',predicate='temperature',value='75 C',status='candidate'),
            dict(id='b',document_id='two',locator='line:1',subject='motor',predicate='temperature',value='90 C',status='candidate')]
    monkeypatch.setattr(api,'library_retrieve',lambda *a,**k:[hit])
    monkeypatch.setattr(api.workflows,'claim_context',lambda *a,**k:claims)
    monkeypatch.setattr(api,'citation_from_hit',lambda hit:dict(id=hit['id']))
    hits,matched,conflicts,_=api.evidence('Motor temperature?')
    assert {claim['id'] for claim in matched}=={'a','b'}
    assert conflicts and hits[0]['projection_status']=='candidate'
