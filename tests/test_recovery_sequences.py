"""Recovery inventory must fail closed before interpolating a sequence name."""
import pytest
from test_ops_implementation import load


@pytest.mark.parametrize('inventory',[
    'unsafe; DROP TABLE documents;', 'public.sequence', 'quoted-name', 'a'*64,
    'same\nsame', '\n', '\n'.join('seq_'+str(i) for i in range(1025)),
])
def test_sequence_inventory_rejects_unsafe_ambiguous_or_excessive_names(inventory):
    calls=[]
    def query(sql):
        calls.append(sql)
        assert len(calls)==1, 'Unsafe sequence relation was queried'
        return inventory
    with pytest.raises(ValueError,match='Unexpected recovery sequence'):
        load('recovery_sequences').sequence_state(query)
    assert len(calls)==1


def test_database_with_no_sequences_has_empty_state():
    assert load('recovery_sequences').sequence_state(lambda sql:'')=={}
