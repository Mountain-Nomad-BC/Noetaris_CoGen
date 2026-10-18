"""Complete currently authorized navigation of immutable governed candidates."""
from . import store
from .library_store import _scope,_position,_cursor
from .workflow_store import rows

KINDS=frozenset({'all','assembly','issues','proposal','extraction'})
STATES=frozenset({'all','candidate','reviewed','rejected'})

def page(*,limit=25,cursor=None,offset=0,kind='all',state='all'):
    identity=store.request_identity()
    if identity is None or identity.get('role') not in {'operator','viewer','reviewer','admin'} or identity.get('identity_kind')=='source-job':
        raise PermissionError('Governed inspection requires a verified reader identity')
    if type(limit) is not int or not 1<=limit<=100 or type(offset) is not int or not 0<=offset<=100000 or not isinstance(kind,str) or kind not in KINDS or not isinstance(state,str) or state not in STATES or (cursor is not None and offset):
        raise ValueError('Invalid governed navigation bounds')
    reviewer=identity['role'] in {'reviewer','admin'}
    scope=_scope('nsai.governed-page/1:'+('review' if reviewer else 'own')+':'+kind+':'+state)
    position=_position(cursor,scope) if cursor is not None else None
    conditions=[];arguments=[]
    if not reviewer:conditions.append('g.author=%s');arguments.append(identity['actor'])
    if kind!='all':conditions.append('g.kind=%s');arguments.append(kind)
    if state!='all':conditions.append("coalesce(r.decision,'candidate')=%s");arguments.append(state)
    def where():return ' WHERE '+' AND '.join(conditions) if conditions else ''
    tables=' FROM governed_records g LEFT JOIN governed_reviews r ON r.record_id=g.id'
    with store.connect() as conn:
        total=conn.execute('SELECT count(*)'+tables+where(),arguments).fetchone()[0]
        if position:
            created,identifier=position
            conditions.append('(g.created_at<%s OR (g.created_at=%s AND g.id>%s))');arguments.extend([created,created,identifier])
        observed=rows(conn.execute("SELECT g.id,g.kind,g.author,g.document_id,g.source_sha256,g.created_at,g.source_ids,g.provenance_complete,coalesce(r.decision,'candidate') AS state"+
            tables+where()+' ORDER BY g.created_at DESC,g.id ASC LIMIT %s OFFSET %s',[*arguments,limit+1,offset]))
    items=observed[:limit];more=len(observed)>limit
    return dict(items=items,total=total,limit=limit,has_more=more,next_cursor=_cursor(items[-1],scope) if more else None,
        kind_filter=kind,state_filter=state,legacy_offset=offset,ordering='created_at-desc/id-asc',snapshot=False,authority_granted=False,
        scope='review-authorized' if reviewer else 'own-authorized',
        limitation='Candidate reviews retain an independent decision; they grant no execution or canonical knowledge authority. Every page rechecks current source permissions.')
