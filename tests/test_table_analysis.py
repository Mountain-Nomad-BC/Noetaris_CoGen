"""Independent decimal answers and explicit exclusion/authority contracts."""
import pytest
from nsai.ingestion import parse_source
from nsai.table_analysis import TableAnalysisInput,calculate


def table(text):return parse_source(text.encode('utf-8'),'sample.csv')['structured_data']


def test_group_sum_is_decimal_exact_and_accounts_for_every_record():
    result=calculate(table('Group,Amount\nA,0.1\nA,0.2\nB,-2.5\nB,\n\n'),
        TableAnalysisInput(value_column=2,group_column=1,skip_rows=1,unit='USD'))
    assert result['groups']==[dict(label='A',value='0.3',included_records=2),dict(label='B',value='-2.5',included_records=1)]
    assert result['coverage']==dict(total_records=6,skipped_records=1,selected_records=5,included_records=3,excluded_records=2,
        exclusions=[dict(locator='table:1:row:5',reason='empty-cell'),dict(locator='table:1:row:6',reason='missing-column')])
    assert result['included_cell_locators']==['table:1:row:2:column:2','table:1:row:3:column:2','table:1:row:4:column:2']
    assert result['unit']['authority'].startswith('user-declared') and result['authority_granted'] is False


@pytest.mark.parametrize('operation,expected',[('sum','6'),('mean','2'),('min','-1'),('max','5'),('count','3')])
def test_aggregates_match_independently_calculated_answers(operation,expected):
    result=calculate(table('-1\n2\n5\n'),TableAnalysisInput(value_column=1,operation=operation))
    assert result['groups'][0]['value']==expected
    if operation=='count':assert result['unit']['label']=='records'


def test_mean_declares_rounding_instead_of_claiming_exact_repeating_decimal():
    result=calculate(table('0\n0\n1\n'),TableAnalysisInput(value_column=1,operation='mean'))
    assert result['groups'][0]['value']=='0.'+'3'*34
    assert result['arithmetic']['mean_significant_digits']==34


@pytest.mark.parametrize('value',[' 1','1 ','1,234','$1','1e3','=SUM(A1:A2)','NaN','Infinity','2026-01-01'])
def test_nonnumeric_values_stop_numeric_calculation_without_silent_omission(value):
    import json
    data=table('2\n'+json.dumps(value)+'\n')
    with pytest.raises(ValueError,match='Expected an explicit decimal'):calculate(data,TableAnalysisInput(value_column=1))


def test_count_does_not_parse_text_as_numbers_and_empty_is_not_zero():
    result=calculate(table('x\n0\n""\n'),TableAnalysisInput(value_column=1,operation='count'))
    assert result['groups'][0]['value']=='2' and result['coverage']['excluded_records']==1


@pytest.mark.parametrize('extra',[dict(value_column=True),dict(skip_rows=-1),dict(operation='DROP TABLE documents'),dict(sql='select 1'),dict(group_column=101)])
def test_request_is_typed_and_contains_no_arbitrary_execution(extra):
    payload=dict(value_column=1);payload.update(extra)
    with pytest.raises(ValueError):TableAnalysisInput(**payload)


def test_group_and_empty_selection_bounds_fail_whole_analysis():
    data=table('\n'.join(f'g{i},1' for i in range(101)))
    with pytest.raises(ValueError,match='100 groups'):calculate(data,TableAnalysisInput(value_column=2,group_column=1))
    with pytest.raises(ValueError,match='No records'):calculate(table('a\n'),TableAnalysisInput(value_column=1,skip_rows=1))
    with pytest.raises(ValueError,match='Grouping column'):calculate(table('1\n'),TableAnalysisInput(value_column=1,group_column=2))
