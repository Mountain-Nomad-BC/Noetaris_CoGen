"""Authorized keyset library pages; cursors carry no authority."""
import base64
from datetime import datetime
import hashlib
import json
from . import store


def _scope(query):
    identity=store.request_identity() or dict(actor='legacy-service',role='service')
    return hashlib.sha256(json.dumps(dict(actor=identity['actor'],role=identity['role'],query=query),
        sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _cursor(row,scope):
    return base64.urlsafe_b64encode(json.dumps(dict(version=1,scope=scope,
        created_at=row['created_at'].isoformat(),id=row['id']),separators=(',',':')).encode()).decode().rstrip('=')


def _position(cursor,scope):
    try:
        if not isinstance(cursor,str) or not 1<=len(cursor)<=512:raise ValueError()
        value=json.loads(base64.b64decode(cursor+'='*((-len(cursor))%4),altchars=b'-_',validate=True))
        if set(value)!={'version','scope','created_at','id'} or type(value['version']) is not int or value['version']!=1 or value['scope']!=scope:
            raise ValueError()
        created=datetime.fromisoformat(value['created_at'])
        if created.tzinfo is None or not isinstance(value['id'],str) or not 1<=len(value['id'])<=200 or '\x00' in value['id']:
            raise ValueError()
        return created,value['id']
    except (ValueError,TypeError,KeyError,UnicodeError):
        raise ValueError('Library cursor is invalid for this identity/filter; refresh the library') from None


def page(*,limit=25,cursor=None,query=None):
    if type(limit) is not int or not 1<=limit<=100:raise ValueError('Invalid library page size')
    if query is not None and (not isinstance(query,str) or len(query)>200 or '\x00' in query):
        raise ValueError('Invalid library filter')
    query=query.strip() if query else None
    query=query or None
    scope=_scope(query);position=_position(cursor,scope) if cursor is not None else None
    conditions=[];arguments=[]
    if query:
        conditions.append('strpos(lower(title),lower(%s))>0');arguments.append(query)
    predicate=' WHERE '+' AND '.join(conditions) if conditions else ''
    from .workflow_store import rows
    with store.connect() as conn:
        total=conn.execute('SELECT count(*) FROM documents'+predicate,arguments).fetchone()[0]
        if position:
            created,identity=position
            conditions.append('(created_at,id)<(%s,%s)');arguments.extend([created,identity])
        predicate=' WHERE '+' AND '.join(conditions) if conditions else ''
        observed=rows(conn.execute('SELECT id,title,source_version AS version,coalesce(original_sha256,sha256) AS sha256,'
            'created_at,nsai_source_is_owner(id) AS can_manage_access,nsai_source_index_status(id) AS indexing '
            'FROM documents'+predicate+' ORDER BY created_at DESC,id DESC LIMIT %s',[*arguments,limit+1]))
    items=observed[:limit];more=len(observed)>limit
    return dict(items=items,total=total,has_more=more,next_cursor=_cursor(items[-1],scope) if more else None,
                limit=limit,filter=query,ordering='created_at-desc/id-desc',snapshot=False)
