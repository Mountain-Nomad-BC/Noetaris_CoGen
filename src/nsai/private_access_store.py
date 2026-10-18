"""Current-principal owner management; request bodies cannot select the actor."""
from . import store


def _private_owner_context():
    identity=store.request_identity()
    if identity is None or identity.get('identity_kind')!='local-user':
        raise LookupError('Source unavailable')


def _translate(error):
    if getattr(error,'sqlstate',None)=='42501':raise LookupError('Source unavailable') from None
    if getattr(error,'sqlstate',None)=='40001':raise ValueError('Sharing changed; reload before applying another change') from None
    if getattr(error,'sqlstate',None) in {'23514','23503','P0001'}:
        raise ValueError('Invalid sharing target or expiry') from None
    raise error


def source_access(document_id):
    _private_owner_context()
    try:
        with store.connect() as conn:
            result=conn.execute('SELECT nsai_current_source_access(%s)',(document_id,)).fetchone()[0]
    except Exception as error:_translate(error)
    if result is None:raise LookupError('Source unavailable')
    return result


def provider_sharing_target(document_id,subject_id):
    _private_owner_context()
    try:
        with store.connect() as conn:
            return conn.execute('SELECT nsai_current_oauth_sharing_target(%s,%s)',
                                (document_id,subject_id)).fetchone()[0] is True
    except Exception as error:_translate(error)


def change_share(document_id,*,expected_epoch,subject_kind,subject_id,expires_at=None,revoke=False):
    _private_owner_context()
    try:
        with store.connect() as conn:
            epoch=conn.execute('SELECT nsai_current_source_share(%s,%s,%s,%s,%s,%s)',
                (document_id,expected_epoch,subject_kind,subject_id,expires_at,revoke)).fetchone()[0]
    except Exception as error:_translate(error)
    return dict(document_id=document_id,epoch=epoch,state='revoked' if revoke else 'shared')
