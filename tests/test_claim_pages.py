from datetime import datetime,timezone
import pytest
from nsai import claim_pages,library_store,store


@pytest.mark.parametrize('arguments',[dict(limit=True),dict(limit=0),dict(limit=101),dict(cursor='bad')])
def test_invalid_review_page_rejected_before_database(monkeypatch,arguments):
    def forbidden():raise AssertionError('Invalid review page reached database')
    monkeypatch.setattr(store,'connect',forbidden)
    with pytest.raises(ValueError):claim_pages.page(**arguments)


def test_review_cursor_cannot_reuse_library_or_another_identity_cursor(monkeypatch):
    def forbidden():raise AssertionError('Cross-scope cursor reached database')
    monkeypatch.setattr(store,'connect',forbidden)
    row=dict(id='a'*32,created_at=datetime.now(timezone.utc))
    with store.identity_context(dict(actor='local-user-alice',role='operator')):
        cursor=library_store._cursor(row,claim_pages.cursor_scope())
        library_cursor=library_store._cursor(row,library_store._scope(None))
        with pytest.raises(ValueError):claim_pages.page(cursor=library_cursor)
    with store.identity_context(dict(actor='local-user-bob',role='operator')):
        with pytest.raises(ValueError):claim_pages.page(cursor=cursor)
