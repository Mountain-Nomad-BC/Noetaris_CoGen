"""Source-scope input bounds fail before a database connection is attempted."""
import pytest
from nsai.workflow_store import scoped_claims

@pytest.mark.parametrize('pages',[[True],[False],[0],[1001],[1.5],['1'],(1,),1])
def test_invalid_memory_page_scope_fails_closed(pages):
    with pytest.raises(ValueError,match='page numbers'):
        scoped_claims(pages=pages)

@pytest.mark.parametrize('active_only',[None,0,1,'true'])
def test_historical_state_selector_requires_boolean(active_only):
    with pytest.raises(ValueError,match='boolean'):
        scoped_claims(active_only=active_only)
