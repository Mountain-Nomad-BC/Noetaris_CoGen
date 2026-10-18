import pytest
from library_corpus_runtime_fixture import ranking_metrics


def test_duplicate_chunks_do_not_inflate_document_recall_or_precision():
    result=ranking_metrics(['a','a','x','b'],{'a','b'})
    assert result['recall_at_k']==1 and result['precision_at_k']==.4 and result['reciprocal_rank']==1


def test_first_relevant_document_determines_reciprocal_rank():
    result=ranking_metrics(['x','b','a'],{'a','b'})
    assert result['reciprocal_rank']==.5


def test_missing_results_are_not_removed_from_metric_denominators():
    result=ranking_metrics([],{'a','b'})
    assert result['recall_at_k']==result['precision_at_k']==result['reciprocal_rank']==0


def test_undefined_relevance_set_is_not_reported_as_perfect_recall():
    with pytest.raises(ValueError):ranking_metrics(['a'],set())
