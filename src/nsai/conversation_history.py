"""Owner-bound durable history; source authorization precedes content release."""
import base64
from datetime import datetime
import hashlib
import json
import re
from . import store
from .source_dependencies import collect_sources,validate_sources


def _actor():
    identity=store.request_identity()
    if identity is None:raise PermissionError('Conversation history requires a verified identity')
    return identity['actor']


def _id(value):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{32}',value):raise ValueError('Invalid conversation identifier')
    return value


def _number(value):
    if not isinstance(value,str) or not re.fullmatch('[1-9][0-9]{0,18}',value) or int(value)>9223372036854775807:
        raise ValueError('Invalid message position')
    return int(value)


def _limit(value):
    if type(value) is not int or not 1<=value<=50:raise ValueError('Invalid history page size')
    return value


def _scope(actor):return hashlib.sha256(('nsai.history/1:'+actor).encode()).hexdigest()


def sessions(*,limit=25,cursor=None):
    actor=_actor();_limit(limit);arguments=[actor];position=''
    if cursor is not None:
        try:
            if not isinstance(cursor,str) or not 1<=len(cursor)<=512:raise ValueError()
            value=json.loads(base64.b64decode(cursor+'='*((-len(cursor))%4),altchars=b'-_',validate=True))
            if set(value)!={'scope','created_at','id'} or value['scope']!=_scope(actor):raise ValueError()
            created=datetime.fromisoformat(value['created_at'])
            if created.tzinfo is None:raise ValueError()
            _id(value['id']);arguments.extend([created,value['id']]);position=' AND (created_at,id)<(%s,%s)'
        except (ValueError,TypeError,KeyError,UnicodeError):raise ValueError('History cursor is invalid for this identity') from None
    from .workflow_store import rows
    with store.connect() as conn:
        observed=rows(conn.execute('SELECT id,created_at FROM sessions WHERE owner=%s'+position+' ORDER BY created_at DESC,id DESC LIMIT %s',[*arguments,limit+1]))
    items=observed[:limit];more=len(observed)>limit
    next_cursor=None
    if more:
        row=items[-1]
        next_cursor=base64.urlsafe_b64encode(json.dumps(dict(scope=_scope(actor),created_at=row['created_at'].isoformat(),id=row['id']),separators=(',',':')).encode()).decode().rstrip('=')
    return dict(items=items,has_more=more,next_cursor=next_cursor,limit=limit,snapshot=False,
                content_policy='Session identifiers contain no conversation text; messages require current complete source authorization.')


def _owner(conn,session_id,actor):
    if conn.execute('SELECT id FROM sessions WHERE id=%s AND owner=%s',(session_id,actor)).fetchone() is None:
        raise LookupError('Conversation unavailable')


def messages(session_id,*,limit=25,before_id=None):
    actor=_actor();_id(session_id);_limit(limit)
    arguments=[session_id];position=''
    if before_id is not None:position=' AND id<%s';arguments.append(_number(before_id))
    from .workflow_store import rows
    with store.connect() as conn:
        _owner(conn,session_id,actor)
        observed=rows(conn.execute('SELECT id::text AS id,role,created_at FROM session_messages '
            'WHERE session_id=%s AND provenance_complete AND nsai_sources_visible(source_ids,provenance_complete)'+position+
            ' ORDER BY session_messages.id DESC LIMIT %s',[*arguments,limit+1]))
    items=observed[:limit];more=len(observed)>limit
    return dict(session_id=session_id,items=items,has_more=more,next_before_id=items[-1]['id'] if more else None,
        ordering='message-id-desc',limit=limit,snapshot=False,
        content_policy='Only currently readable, provenance-complete records are listed. Other records are retained, not deleted; full content is fetched separately.')


def message(session_id,message_id):
    actor=_actor();_id(session_id);message_id=_number(message_id)
    with store.connect() as conn:
        _owner(conn,session_id,actor)
        metadata=conn.execute('SELECT octet_length(receipt::text),source_ids,provenance_complete FROM session_messages '
            'WHERE session_id=%s AND id=%s AND provenance_complete AND nsai_sources_visible(source_ids,provenance_complete)',(session_id,message_id)).fetchone()
        if metadata is None:raise LookupError('Message unavailable')
        if metadata[0]>16*1024*1024:raise ValueError('Retained message exceeds the qualified response bound; no stored content was changed')
        validate_sources(conn,metadata[1],complete=metadata[2])
        row=conn.execute('SELECT role,text,receipt,created_at FROM session_messages WHERE session_id=%s AND id=%s',(session_id,message_id)).fetchone()
        if row is None:raise LookupError('Message unavailable')
        role,preview,receipt,created=row
        if role=='assistant':
            if not isinstance(receipt,dict) or receipt.get('provenance_complete') is not True or not isinstance(receipt.get('answer'),str):
                raise ValueError('Retained assistant receipt lacks complete content provenance')
            dependencies=collect_sources(receipt,conn=conn)
            if set(dependencies)!=set(metadata[1]):raise ValueError('Retained history provenance does not match its source envelope')
            validate_sources(conn,dependencies)
        return dict(session_id=session_id,id=str(message_id),role=role,created_at=created,
                    text_preview=preview,receipt=receipt,full_text_field='receipt.answer' if role=='assistant' else 'text_preview',
                    source_dependencies=metadata[1],provenance_complete=True,
                    content_policy='Assistant receipt.answer retains the complete response; text_preview may be shorter. No stored records were truncated or rewritten by this read.')
