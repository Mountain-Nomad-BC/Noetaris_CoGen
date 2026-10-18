import asyncio
import httpx
import pytest
from nsai import inference


def configure(monkeypatch):
    monkeypatch.setenv('NSAI_MODEL_URL','http://llama-cpp:8080/v1')
    monkeypatch.setenv('NSAI_MODEL_NAME','nsai-local-gemma')
    monkeypatch.setenv('NSAI_MODEL_ANSWER_STRATEGY','source-selection')
    monkeypatch.delenv('NSAI_MODEL_API_KEY_FILE',raising=False)


def hit(text='Pump-X operating limit is 85 C.'):
    return dict(id='a'*32,document_id='b'*32,text=text,revision='1',locator='line:1',title='Synthetic',original_sha256='c'*64)


def test_cpu_selection_contains_complete_units_and_omits_truncated_line(monkeypatch):
    configure(monkeypatch)
    first=hit('Pump-X operating limit is 85 C.\n'+'x'*2000)
    body=inference.prepare_source_request('Pump-X',[first,hit()],max_tokens=128)
    schema=body['response_format']['json_schema']['schema']
    # The support contract splits a temperature sentence at a following newline;
    # its complete unit can therefore omit the separator's terminal period.
    assert {choice.rstrip('.') for choice in schema['properties']['answer']['enum']}=={'Pump-X operating limit is 85 C'}
    assert schema['properties']['citation_ids']['items']['enum']==['a'*32]


def test_cpu_selection_refuses_when_only_truncated_unit_fits(monkeypatch):
    configure(monkeypatch)
    with pytest.raises(ValueError,match='No complete source units'):
        inference.prepare_source_request('Question',[hit('x'*2000)])


def test_complete_unit_and_choice_limits_are_disclosed_in_answer(monkeypatch):
    from nsai import api
    configure(monkeypatch)
    text='\n'.join('Complete source observation '+str(i)+'.' for i in range(15))
    choices,coverage=inference.source_selection([hit(text),hit(text)])
    assert len(choices)==12
    assert coverage['distinct_retrieved_units']==15 and coverage['omitted_units']==3
    result=api.attach_retrieval_coverage(dict(answer='Candidate quote',source_selection=coverage),[hit(text)])
    assert result['answer'].startswith('CPU SOURCE SELECTION LIMIT: 3 distinct text units')
    assert 'not exhaustive' in result['answer']


def test_provider_ignoring_cpu_schema_still_cannot_fabricate_value(monkeypatch):
    configure(monkeypatch)
    original=httpx.AsyncClient
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kwargs:original(
        transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'choices':[{'message':{'content':'{"answer":"Pump-X operating limit is 75 C.","citation_ids":["'+('a'*32)+'"]}'}}]})),**kwargs))
    result=asyncio.run(inference.generate_from_sources('What is Pump-X operating limit?',[hit()]))
    assert result['mode']=='source_support_guard_fallback'
    assert result['answer_strategy']=='source-selection'
    assert result['answer_verified'] is False


def test_default_grounded_profile_is_preserved(monkeypatch):
    configure(monkeypatch);monkeypatch.delenv('NSAI_MODEL_ANSWER_STRATEGY')
    body=inference.prepare_source_request('Question',[hit()])
    assert 'enum' not in body['response_format']['json_schema']['schema']['properties']['answer']


def test_question_relevance_excludes_uuid_and_unrelated_source_heading(monkeypatch):
    configure(monkeypatch)
    fact='The Aurora laboratory replaces the ceramic membrane every 47 days.'
    text='Aurora laboratory maintenance guide\n'+fact+'\nA technician isolates the water supply.\n4228d40f-8a0c-4832-a909-55907551fc4d'
    choices,coverage=inference.source_selection([hit(text)],'How often does the Aurora laboratory replace the ceramic membrane?')
    assert choices==[fact]
    assert coverage['omitted_units']==3
    assert coverage['relevance_selection'].startswith('maximum-query-token-overlap')


def test_relevance_keeps_negated_and_competing_complete_quotes(monkeypatch):
    configure(monkeypatch)
    positive='Aurora ceramic membrane replacement interval is 47 days.'
    negative='Aurora ceramic membrane replacement interval is not 47 days.'
    choices,_=inference.source_selection([hit(positive+'\n'+negative)],'What is Aurora ceramic membrane replacement interval?')
    assert choices==[positive,negative]


def test_provider_cannot_ignore_relevant_selection_for_an_irrelevant_supported_quote(monkeypatch):
    configure(monkeypatch)
    original=httpx.AsyncClient
    monkeypatch.setattr(inference.httpx,'AsyncClient',lambda **kwargs:original(
        transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'choices':[{'message':{'content':'{"answer":"Unrelated source identifier","citation_ids":["'+('a'*32)+'"]}'}}]})),**kwargs))
    source=hit('The Aurora ceramic membrane replacement interval is 47 days.\nUnrelated source identifier')
    result=asyncio.run(inference.generate_from_sources('What is Aurora ceramic membrane replacement interval?',[source]))
    assert result['mode']=='source_support_guard_fallback'
    assert '47 days' in result['answer']
    assert result['answer_verified'] is False
