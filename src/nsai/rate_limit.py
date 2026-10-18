"""Bounded admission for authenticated roles and the bounded local registry."""
import re
from threading import Lock

_lock=Lock()
ACTORS=frozenset({'local-operator','local-viewer','local-reviewer','local-admin'})

def admit(events,actor,now,*,per_principal=120,window_seconds=60):
    if actor not in ACTORS and (not isinstance(actor,str) or re.fullmatch(r'local-user-[a-z][a-z0-9_-]{0,63}',actor) is None):
        return False
    with _lock:
        while events and events[0][0]<=now-window_seconds:
            events.popleft()
        if sum(owner==actor for _,owner in events)>=per_principal:
            return False
        # Each principal has its own allowance: one role cannot exhaust another.
        # The authenticated registry admits at most 1,000 identities. Hot reload
        # cannot grow retained state beyond that registry-sized window budget.
        if len(events)>=(len(ACTORS)+1000)*per_principal:
            return False
        events.append((now,actor))
        return True
