from collections import deque
from concurrent.futures import ThreadPoolExecutor
from nsai.rate_limit import admit, ACTORS

def test_one_principal_cannot_exhaust_another():
    events=deque()
    for actor in sorted(ACTORS):
        assert all(admit(events,actor,1) for _ in range(120))
        assert not admit(events,actor,1)
    assert len(events)==480
    assert admit(events,'local-operator',61)
    assert len(events)==1

def test_unknown_principal_cannot_grow_limiter_state():
    events=deque()
    assert not admit(events,'untrusted-identity',1)
    assert not events


def test_distinct_authenticated_users_have_separate_bounded_allowances():
    events=deque()
    for actor in ['local-user-alice','local-user-bob','local-operator']:
        assert all(admit(events,actor,1) for _ in range(120))
        assert not admit(events,actor,1)
    assert len(events)==360
    assert admit(events,'local-user-alice',61) and len(events)==1


def test_malformed_local_user_ids_cannot_grow_state():
    events=deque()
    for actor in ['local-user-','local-user-Alice','local-user-'+('a'*65),'local-user-a/other',None]:
        assert not admit(events,actor,1)
    assert not events

def test_concurrent_admission_preserves_exact_bound():
    events=deque()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:admit(events,'local-operator',1),range(200)))
    assert sum(results)==120 and len(events)==120
