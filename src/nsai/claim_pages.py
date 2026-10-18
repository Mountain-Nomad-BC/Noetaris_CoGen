"""Authorized review pages with summaries independent of the displayed page."""
import hashlib
from datetime import datetime
from . import store
from .library_store import _scope,_position,_cursor
from .models import conflict_groups


def cursor_scope():
    return hashlib.sha256(('nsai.claim-review-page/1:'+_scope(None)).encode()).hexdigest()


def page(*,limit=25,cursor=None):
    if type(limit) is not int or not 1<=limit<=100:raise ValueError('Invalid claim page size')
    scope=cursor_scope()
    try:position=_position(cursor,scope) if cursor is not None else None
    except ValueError:raise ValueError('Claim cursor is invalid for this identity; refresh review') from None
    with store.connect() as conn:
        result=conn.execute('SELECT nsai_claim_review_page(%s,%s,%s)',
            [limit,position[0] if position else None,position[1] if position else None]).fetchone()[0]
    total,verified=result['total'],result['verified']
    items,witnesses=result['items'],result['witnesses']
    for item in items:item['created_at']=datetime.fromisoformat(item['created_at'])
    complete=len(witnesses)<=2000
    active=conflict_groups([row for row in witnesses if row['status'] not in {'rejected','superseded'}]) if complete else []
    historical=conflict_groups(witnesses) if complete else []
    more=len(items)>limit;items=items[:limit]
    return dict(items=items,total=total,has_more=more,next_cursor=_cursor(items[-1],scope) if more else None,
        limit=limit,snapshot=False,conflicts=active[:100],historical_conflicts=historical[:100],
        summary=dict(verified_claims=verified,active_conflict_groups=len(active) if complete else None,
            historical_conflict_groups=len(historical) if complete else None,conflict_analysis_complete=complete,
            displayed_conflict_groups=min(100,len(active)),method='distinct-raw-alternative-witnesses',
            warning=None if complete else 'Conflict analysis exceeds the qualified bound; no absence of conflicts is established.'))
