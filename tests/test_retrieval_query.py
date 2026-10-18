import pytest
from nsai.retrieval.query import build_retrieval_query

@pytest.mark.parametrize('suffix',['Answer briefly.','Please answer concisely.','Respond in one sentence.','Reply using bullet points.'])
def test_terminal_presentation_is_not_source_query(suffix):
    query=build_retrieval_query('What is the maximum temperature? '+suffix)
    assert query.exact=='What is the maximum temperature'
    assert query.alternate=='"maximum" OR "temperature"'
    assert query.presentation_removed

@pytest.mark.parametrize('question',['What does "Answer briefly" mean?','Where is the answer briefly recorded?',
    'What is "maximum temperature? Answer briefly.','Which manual says answer briefly for Pump-X?'])
def test_source_bearing_or_quoted_presentation_words_are_preserved(question):
    query=build_retrieval_query(question)
    assert not query.presentation_removed
    assert 'briefly' in query.alternate

def test_substantive_entity_negation_units_and_revisions_are_retained():
    query=build_retrieval_query('Pump-X revision 2 must not exceed -5 C maximum temperature? Answer briefly.')
    assert query.entities==('pump-x',)
    assert query.entity_gate=='"pump-x"'
    assert all('"'+word+'"' in query.alternate for word in ('revision','2','must','not','5','c','maximum','temperature'))
    assert '-5' in query.exact

def test_explicit_entity_comparison_gates_both_and_camel_identifier():
    query=build_retrieval_query('Compare Pump-X and Fan-Z operating limits.')
    assert query.entity_gate=='"pump-x" OR "fan-z"'
    assert build_retrieval_query('What is the PumpX temperature?').entities==('pumpx',)

def test_revision_and_source_locator_are_not_entity_gates():
    query=build_retrieval_query('maximum temperature revision-2 page-1 line-3')
    assert query.entity_gate is None
    assert 'revision' in query.alternate

def test_unit_ratios_and_filename_are_not_named_entity_gates():
    assert build_retrieval_query('temperature in C/F from manual.pdf?').entity_gate is None

@pytest.mark.parametrize('question',['',None,'x'*1001,'source\x00hidden'])
def test_query_bounds_fail_closed(question):
    with pytest.raises(ValueError):build_retrieval_query(question)

def test_unicode_tokens_and_operator_strings_remain_data():
    query=build_retrieval_query('Température OR pressure; DROP TABLE documents --')
    assert '"température"' in query.alternate
    assert '"drop"' in query.alternate
    assert '\\' not in query.alternate
