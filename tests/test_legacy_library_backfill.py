"""Historical projections preserve original custody and never assert new coverage."""
import copy
import hashlib
import pytest
from nsai import store


def retained_source():
    text='Greek α and combining e\u0301\nPump maximum temperature is 72 C.\nP = V * I'
    data=text.encode();digest=hashlib.sha256(data).hexdigest();document='a'*32
    spans=[dict(locator='line:'+str(index),text=line) for index,line in enumerate(text.splitlines(),1)]
    manifest=dict(index_name='historical',documents=[dict(source_id=document,title='Historical source',text=text,
        metadata=dict(revision='1',original_sha256=digest,parser_version='nsai-bounded/1',spans=spans,warnings=[]))])
    return dict(id=document,source_version='1',original_sha256=digest,source_bytes=data,raw_text=text,
        manifest=manifest,owner_scope='legacy-shared',media_type='text/plain'),[(s['locator'],s['text']) for s in spans]


def test_legacy_projection_keeps_exact_retained_text_locators_and_unknown_coverage():
    from nsai.legacy_library_backfill import prepare_legacy_projection
    record,spans=retained_source();before=copy.deepcopy(record)
    artifacts=prepare_legacy_projection(record,spans)
    coverage=artifacts['knowledge']['extraction_coverage']
    assert coverage['complete'] is False and coverage['pages']==[] and coverage['quality_verified'] is False
    assert coverage['input_kind']=='legacy-retained-spans' and coverage['legacy_parser_version']=='nsai-bounded/1'
    nodes=[node for node in artifacts['knowledge']['nodes'] if node['kind']=='source_span']
    assert {(node['locator'],node['text']) for node in nodes}==set(spans)
    assert record==before and record['source_bytes']==record['raw_text'].encode()


@pytest.mark.parametrize('fault',['original','digest','source-id','revision','text','span','duplicate','parser'])
def test_legacy_projection_refuses_changed_custody_or_unsupported_history(fault):
    from nsai.legacy_library_backfill import prepare_legacy_projection
    record,spans=retained_source();document=record['manifest']['documents'][0];metadata=document['metadata']
    if fault=='original':record['source_bytes']+=b'changed'
    elif fault=='digest':record['original_sha256']='f'*64
    elif fault=='source-id':document['source_id']='b'*32
    elif fault=='revision':metadata['revision']='changed'
    elif fault=='text':document['text']+='changed'
    elif fault=='span':metadata['spans'][0]['text']='foreign replacement'
    elif fault=='duplicate':metadata['spans'].append(copy.deepcopy(metadata['spans'][0]))
    else:metadata['parser_version']='unsupported'
    with pytest.raises(ValueError):prepare_legacy_projection(record,spans)


def test_private_source_cannot_use_legacy_projection():
    from nsai.legacy_library_backfill import prepare_legacy_projection
    record,spans=retained_source();record['owner_scope']='local-user-alice'
    with pytest.raises(PermissionError):prepare_legacy_projection(record,spans)


@pytest.mark.parametrize('role',['operator','viewer','reviewer','admin'])
def test_request_identity_cannot_run_legacy_maintenance(monkeypatch,role):
    from nsai import legacy_library_backfill as module
    monkeypatch.setattr(module.store,'connect',lambda:pytest.fail('Maintenance opened a request database connection'))
    with store.identity_context(dict(actor='local-user-alice',role=role,identity_kind='local-user')):
        with pytest.raises(PermissionError):module.commission_batch()


@pytest.mark.parametrize('limit',[True,0,1001])
def test_backfill_limits_cannot_disable_bounds(monkeypatch,limit):
    from nsai import legacy_library_backfill as module
    monkeypatch.setattr(module.store,'connect',lambda:pytest.fail('Invalid maintenance limit opened database'))
    with pytest.raises(ValueError):module.commission_batch(limit=limit)


@pytest.mark.parametrize('operation',['batch','source'])
def test_disabled_semantic_worker_preserves_legacy_readability(monkeypatch,operation):
    from nsai import legacy_library_backfill as module
    monkeypatch.setenv('NSAI_INDEX_WORKER_ENABLED','false')
    monkeypatch.setattr(module.store,'connect',lambda:pytest.fail('Disabled worker opened database'))
    with pytest.raises(RuntimeError,match='Commission the semantic worker'):
        if operation=='batch':module.commission_batch()
        else:module.commission_source('a'*32)
