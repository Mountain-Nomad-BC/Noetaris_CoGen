from datetime import datetime,timedelta,timezone
import os
import pytest
from nsai.api import SourceShare
from test_private_access_database import database


@pytest.mark.parametrize('change',[
    dict(actor='local-user-alice'),dict(expected_epoch=True),
    dict(subject_kind='admin'),dict(subject_id='local-admin'),
    dict(subject_id='../../private'),dict(subject_kind='group',subject_id='Bad Group'),
    dict(expires_at='2030-01-01T00:00:00'),
    dict(expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)),
    dict(revoke='yes'),
])
def test_share_request_cannot_select_actor_or_bypass_shape_and_expiry(change):
    payload=dict(expected_epoch=1,subject_kind='user',subject_id='local-user-bob')
    payload.update(change)
    with pytest.raises(ValueError):SourceShare(**payload)


def test_share_expiry_retains_explicit_timezone():
    expiry=datetime.now(timezone.utc)+timedelta(days=1)
    request=SourceShare(expected_epoch=1,subject_kind='user',subject_id='local-user-bob',expires_at=expiry)
    assert request.expires_at==expiry


@pytest.mark.parametrize('known_provider,revoke,allowed',[(True,False,True),(False,False,False),(False,True,True)])
def test_share_handler_validates_provider_target_only_after_owner_check(monkeypatch,known_provider,revoke,allowed):
    from fastapi import HTTPException
    from nsai import api,private_access_store,security
    calls=[]
    monkeypatch.setattr(private_access_store,'source_access',lambda doc:calls.append('owner') or {})
    monkeypatch.setattr(security,'_local_identities',lambda:[])
    def provider(doc,target):
        assert calls==['owner'];calls.append('target');return known_provider
    monkeypatch.setattr(private_access_store,'provider_sharing_target',provider)
    monkeypatch.setattr(private_access_store,'change_share',lambda doc,**kw:calls.append('share') or {'state':'revoked' if kw['revoke'] else 'shared'})
    payload=SourceShare(expected_epoch=1,subject_kind='user',subject_id='local-user-oauth-'+'a'*32,revoke=revoke)
    if allowed:
        result=api.source_share('a'*32,payload,identity={})
        assert result['state']==('revoked' if revoke else 'shared') and calls[-1]=='share'
        if revoke:assert calls==['owner','share']
    else:
        with pytest.raises(HTTPException) as error:api.source_share('a'*32,payload,identity={})
        assert error.value.status_code==409 and 'share' not in calls


@pytest.mark.skipif(os.getenv('NSAI_TEST_PRIVATE_DATABASE')!='1',reason='explicit owned PostgreSQL qualification')
def test_owner_adapter_binds_current_actor_and_denies_resharing(database):
    import json
    policy=json.loads(database("SELECT nsai_current_source_access('private');",app=True,actor='local-user-alice'))
    assert policy['owner']=='local-user-alice' and policy['epoch']==1 and policy['grants']==[]
    assert database("SELECT nsai_current_source_share('private',1,'user','local-user-bob',NULL,false);",app=True,actor='local-user-alice')=='2'
    assert database("SELECT id FROM documents;",app=True,actor='local-user-bob')=='private'
    for actor,role in [('local-user-bob','operator'),('local-user-admin','admin')]:
        database("SELECT nsai_current_source_access('private');",app=True,actor=actor,role=role,ok=False)
        database("SELECT nsai_current_source_share('private',2,'user','local-user-carol',NULL,false);",app=True,actor=actor,role=role,ok=False)
    database("SELECT nsai_current_source_share('private',1,'user','local-user-carol',NULL,false);",app=True,actor='local-user-alice',ok=False)
    assert database("SELECT nsai_current_source_share('private',2,'user','local-user-bob',NULL,true);",app=True,actor='local-user-alice')=='3'
    assert database("SELECT count(*) FROM documents;",app=True,actor='local-user-bob')=='0'
