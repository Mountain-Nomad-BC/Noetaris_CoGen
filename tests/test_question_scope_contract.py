"""Invalid scope is rejected at the public input boundary, before persistence."""
import pytest
from nsai.api import Question


@pytest.mark.parametrize('scope', [
    {'revision': '1'}, {'pages': [1]}, {'document_ids': [], 'pages': [1]},
    {'document_ids': ['a'*32, 'a'*32]}, {'document_ids': ['a'*32], 'pages': [True]},
])
def test_invalid_question_scope_is_rejected(scope):
    with pytest.raises(ValueError):
        Question(question='What does the source say?', **scope)


@pytest.mark.parametrize('scope', [
    {}, {'document_ids': ['a'*32]},
    {'document_ids': ['a'*32], 'revision': '1'},
    {'document_ids': ['a'*32], 'revision': '1', 'pages': [1]},
])
def test_existing_library_document_and_page_requests_remain_valid(scope):
    assert Question(question='What does the source say?', **scope).question
