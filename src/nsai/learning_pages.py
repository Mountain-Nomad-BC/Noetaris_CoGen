"""Freshly authorized keyset proposal pages; no listing cursor grants authority."""
from . import store
from .library_store import _scope,_position,_cursor
from .workflow_store import rows

STATES=frozenset({'all','candidate','reviewed','rejected'})


def page(*,own=False,limit=25,cursor=None,state='all'):
    identity=store.request_identity()
    expected={'operator'} if own else {'reviewer','admin'}
    if identity is None or identity.get('role') not in expected or identity.get('identity_kind')=='source-job':
        raise PermissionError('Proposal inspection requires the appropriate verified identity')
    if type(own) is not bool or type(limit) is not int or not 1<=limit<=100 or not isinstance(state,str) or state not in STATES:
        raise ValueError('Invalid proposal navigation bounds')
    scope=_scope('nsai.learning-page/1:'+('own' if own else 'review')+':'+state)
    position=_position(cursor,scope) if cursor is not None else None
    conditions=[];arguments=[]
    if own:conditions.append('l.author=%s');arguments.append(identity['actor'])
    if state!='all':conditions.append('l.state=%s');arguments.append(state)
    def where():return ' WHERE '+' AND '.join(conditions) if conditions else ''
    tables=' FROM learning_proposals l JOIN claims c ON c.id=l.source_claim_id JOIN documents d ON d.id=c.document_id'
    with store.connect() as conn:
        total=conn.execute('SELECT count(*)'+tables+where(),arguments).fetchone()[0]
        if position:
            conditions.append('(l.created_at,l.id)<(%s,%s)');arguments.extend(position)
        observed=rows(conn.execute("SELECT l.*,jsonb_build_object('id',c.id,'document_id',c.document_id,"
            "'subject',c.subject,'predicate',c.predicate,'value',c.value,'locator',c.locator,"
            "'status',c.status,'revision',c.revision,'original_sha256',d.original_sha256) AS source_claim"+
            tables+where()+' ORDER BY l.created_at DESC,l.id DESC LIMIT %s',[*arguments,limit+1]))
    items=observed[:limit];more=len(observed)>limit
    return dict(items=items,total=total,limit=limit,has_more=more,
        next_cursor=_cursor(items[-1],scope) if more else None,state_filter=state,
        scope='own-authorized' if own else 'review-authorized',snapshot=False,authority_granted=False,
        limitation='Proposal review records an independent decision; it does not promote a reflection into canonical knowledge.')
