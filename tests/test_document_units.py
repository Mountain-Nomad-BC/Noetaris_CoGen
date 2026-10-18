"""Original multilingual and positional fixtures; no private reference content."""
import pytest
from nsai.document_units import assemble_document_units


def assemble(spans):
    return assemble_document_units('a'*32,'r1','b'*64,spans)


def test_unicode_math_and_blank_spans_are_retained_exactly():
    spans=[dict(locator='p1',page=1,text='α + β = ∫ γ dx'),dict(locator='p2',page=1,text='温度の測定'),dict(locator='p3',text='')]
    result=assemble(spans)
    assert [u['text'] for u in result['units']]==[s['text'] for s in spans]
    assert all(not u['quality_verified'] and not u['authority_granted'] for u in result['units'])
    assert result['units'][0]['quality_signals']==['math-like-wording']
    assert result['units'][2]['kind']=='unknown'


def test_section_hierarchy_and_exact_offsets():
    spans=[dict(locator=str(i),text=t) for i,t in enumerate(['1. Method','A source passage.','1.1 Limits','A second passage.','2. Results'])]
    u=assemble(spans)['units']
    assert u[1]['section_candidate_id']==u[0]['id']
    assert u[2]['section_candidate_id']==u[0]['id']
    assert u[3]['section_candidate_id']==u[2]['id']
    assert u[4]['section_candidate_id'] is None
    assert all(x['text']==s['text'][x['char_start']:x['char_end']] for x,s in zip(u,spans))


def test_inserting_unrelated_span_does_not_renumber_unit_ids():
    spans=[dict(locator='line-a',text='One source observation.'),dict(locator='line-b',text='Another source observation.')]
    original=assemble(spans)['units']
    modified=assemble([dict(locator='new',text='Unrelated added passage.'),*spans])['units']
    assert [u['id'] for u in original]==[u['id'] for u in modified[1:]]


def test_quality_signals_do_not_discard_text_or_use_ascii_ratio():
    text='Δοκιμή 温度 \ufffd\x01'
    unit=assemble([dict(locator='x',text=text)])['units'][0]
    assert unit['text']==text
    assert set(unit['quality_signals'])=={'replacement-character-present','control-character-present'}
    assert unit['confidence_probability'] is None


def test_delimiter_table_is_explicitly_only_a_candidate():
    units=assemble([dict(locator='table',text='name\tvalue\tunit'),dict(locator='list',text='• Inspect the source')])['units']
    assert units[0]['kind']=='table_candidate'
    assert units[0]['quality_signals']==['delimiter-layout-only']
    assert units[1]['kind']=='list_item_candidate'


def test_duplicate_locators_and_invalid_pages_are_refused():
    with pytest.raises(ValueError,match='duplicate'):
        assemble([dict(locator='x',text='A'),dict(locator='x',text='B')])
    with pytest.raises(ValueError,match='page'):
        assemble([dict(locator='x',page=True,text='A')])


def test_source_budget_is_bounded_before_output():
    with pytest.raises(ValueError,match='budget'):
        assemble([dict(locator=str(i),text='x'*32768) for i in range(129)])
