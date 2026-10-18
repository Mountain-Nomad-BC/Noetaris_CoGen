from nsai import api,inference


class Hits(list):
    coverage=dict(method='lexical',returned_chunks=12,limit=12,additional_matches_exist=True,
        matching_chunks_lower_bound=13,omitted_chunks_at_least=1,total_matching_chunks=None)


def test_truncated_retrieval_is_visible_in_answer_and_machine_receipt():
    result=api.attach_retrieval_coverage(dict(answer='source-supported answer',answer_verified=False),Hits([{}]*12))
    assert result['answer'].startswith('RETRIEVAL LIMIT:')
    assert result['retrieval_coverage']['total_matching_chunks'] is None
    assert result['retrieval_coverage']['omitted_chunks_at_least']==1
    assert result['answer_verified'] is False


def test_unknown_coverage_never_claims_no_omissions():
    result=api.attach_retrieval_coverage(dict(answer='source answer'),[{}])
    assert result['answer']=='source answer'
    assert result['retrieval_coverage']==dict(method='unknown',returned_chunks=1,total_matching_chunks=None)


def test_search_exposes_same_truncation_receipt(monkeypatch):
    hits=Hits([{}]*12)
    monkeypatch.setattr(api,'library_retrieve',lambda q:hits)
    result=api.search('Pump-X',identity={'role':'viewer'})
    assert result['items'] is hits
    assert result['retrieval_coverage']==hits.coverage


def test_prompt_carries_omission_metadata_before_actual_token_admission(monkeypatch):
    monkeypatch.setenv('NSAI_MODEL_URL','http://llama-cpp:8080/v1')
    monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)
    hits=Hits([dict(id='a'*32,revision='1',locator='line:1',text='Pump-X operating limit is 75 C')])
    body=inference.prepare_source_request('Pump-X?',hits)
    prompt=body['messages'][1]['content']
    assert '"additional_matches_exist": true' in prompt
    assert '"total_matching_chunks": null' in prompt
    assert 'not semantic completeness' in prompt
