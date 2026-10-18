import pytest
from nsai import inference


SOURCE='Motor-X maximum operating temperature is 75 C.'


@pytest.mark.parametrize('answer',[
    'Motor-X maximum operating temperature is not 75 C.',
    'Motor-X minimum operating temperature is 75 C.',
    'Motor-X maximum operating temperature is 75 C because of poor lubrication.',
    'Motor-X is certified for unattended operation.',
    'Motor-X was formerly limited to 75 C.',
])
def test_numbers_and_entity_do_not_establish_assertion_support(answer):
    assert not inference.factual_support(answer,[dict(text=SOURCE)])


@pytest.mark.parametrize('source',[
    'If pressure is stable, Motor-X maximum operating temperature is 75 C.',
    'Motor-X maximum operating temperature is not 75 C.',
    'Previously Motor-X maximum operating temperature is 75 C.',
    'Perhaps Motor-X maximum operating temperature is 75 C.',
])
def test_bare_quantity_cannot_drop_source_qualifiers(source):
    assert not inference.factual_support('75 C',[dict(text=source)])


def test_supported_exact_unit_conversion_remains_available():
    assert inference.factual_support('167 F',[dict(text=SOURCE)])
    assert inference.factual_support('Motor-X maximum operating temperature is 167 F.',[dict(text=SOURCE)])


def test_question_entity_binds_a_bare_quantity_to_its_source_fact():
    from nsai.answer_support import assess
    hits=[dict(id='a'*64,text=SOURCE+'\nMotor-Y maximum operating temperature is 85 C.')]
    assert not assess('85 C',hits,question='What is the maximum operating temperature of Motor-X?')['valid']
    assert assess('75 C',hits,question='What is the maximum operating temperature of Motor-X?')['valid']


def test_exact_general_source_text_remains_an_attributed_quotation():
    from nsai.answer_support import assess
    text='The red indicator identifies the bypass valve.'
    result=assess(text,[dict(id='a'*64,text=text)])
    assert result['valid'] and result['claims'][0]['method']=='source-quotation'
    assert result['claims'][0]['citation_ids']==['a'*64]
    assert result['rendered_answer'].startswith('The cited excerpt states:')


@pytest.mark.parametrize('question',[
    'What is the minimum operating temperature of Motor-X?',
    'What was the maximum operating temperature of Motor-X previously?',
    'Is Motor-X certified for unattended operation at 75 C?',
])
def test_bare_value_cannot_invent_the_question_predicate(question):
    from nsai.answer_support import assess
    assert not assess('75 C',[dict(id='a'*64,text=SOURCE)],question=question)['valid']
