"""Real PostgreSQL + real HTTP encoder + application lifecycle qualification.

Private route functions run under actual verified registry identities. The normal
private HTTP admission block is separately asserted; no release gate is bypassed.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from nsai import api,security,store,workflow_store as workflow,semantic_jobs as jobs,research_store
from nsai.semantic_encoder import PINNED_MODEL_SHA256
from semantic_fixture_helpers import configure_authority


def identity(name):
    return security.resolve_principal('Bearer '+Path('/tmp/fixture-user-'+name).read_text())


def source_text():
    return 'Motor-X maximum operating temperature is 85 C.\n'+'\n'.join(
        f'Section {number}: '+('insulation durability temperature safety '*16) for number in range(12))


def upload(name):
    who=identity(name)
    with store.identity_context(who):
        return api.ingest(api.DocumentInput(title=name+' owned source',version='pipeline-1',text=source_text()),who)


def main():
    configure_authority()
    phase=sys.argv[1]
    checks=[]
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    if phase=='checkpoint':
        saved=upload('alice');doc=saved['document_id']
        with store.identity_context(identity('alice')):
            check('new upload is queued and not searchable',not jobs.source_status(doc)['ready'] and not workflow.retrieve('Motor-X maximum operating temperature'))
        job=jobs.claim_next()
        save=jobs._save_checkpoints
        def checkpoint_then_crash(job,records):
            save(job,records)
            raise RuntimeError('Owned crash after durable stage commit')
        with patch('nsai.semantic_jobs._save_checkpoints',side_effect=checkpoint_then_crash):
            try:asyncio.run(jobs.process_job(job))
            except RuntimeError:checks.append('orchestrator crash retained committed checkpoint')
            else:raise AssertionError('Owned crash did not occur')
        with store.identity_context(identity('alice')):
            status=jobs.source_status(doc)
            check('partial checkpoint remains unpublished',not status['ready'] and status['passages_completed']==8)
            check('fixture requires more than one encoder batch',status['passages_total']>8)
        print(json.dumps(dict(status='PASS_SCOPED',phase=phase,checks=checks,document_id=doc,job_id=job['id'],
                             completed=status['passages_completed'],total=status['passages_total'])))
        return
    if phase!='resume':raise ValueError('Unknown qualification phase')
    job=jobs.claim_next()
    check('new process takes over the expired lease',job is not None and job['attempt']==2)
    doc=job['document_id'];encoded_count=0
    async def count_encode(texts):
        nonlocal encoded_count
        encoded_count+=len(texts)
        return await jobs.encode_texts(texts)
    result=asyncio.run(jobs.process_job(job,encode=count_encode))
    check('resumed real encoder publication succeeds',result['state']=='succeeded')
    with store.identity_context(identity('alice')):
        status=jobs.source_status(doc)
        resumed_total=status['passages_total']
        check('resume computes only missing passages',encoded_count==status['passages_total']-8)
        check('validated generation becomes searchable',status['ready'] and bool(workflow.retrieve('Motor-X maximum operating temperature')))
        query=asyncio.run(jobs.encode_texts(['What maximum operating temperature is allowed for the motor?']))
        hits=research_store.search(query['vectors'][0],PINNED_MODEL_SHA256,[doc])
        check('actual encoded query retrieves the published source',bool(hits['items']) and all(hit['document_id']==doc for hit in hits['items']))
        from nsai.retrieval.library import retrieve as library_retrieve
        ordinary=library_retrieve('What maximum operating temperature is allowed for the motor?',document_ids=[doc],revision='pipeline-1')
        check('ordinary natural-language retrieval uses real library semantic search',bool(ordinary) and ordinary.coverage['semantic_state']=='ready'
              and ordinary.coverage['method']=='authorized-lexical-semantic-rank-fusion'
              and all(hit['document_id']==doc for hit in ordinary))
    bob=upload('bob')['document_id']
    check('identical bytes remain separate private logical documents',bob!=doc)
    second=asyncio.run(jobs.process_one())
    check('ordinary orchestrator publishes second owner source',second['state']=='succeeded')
    with store.identity_context(identity('bob')):
        try:research_store.search(query['vectors'][0],PINNED_MODEL_SHA256,[doc])
        except LookupError:checks.append('semantic retrieval cannot cross private ownership')
        else:raise AssertionError('Private semantic source leaked')
    with store.identity_context(identity('alice')):
        api.source_share(doc,api.SourceShare(expected_epoch=1,subject_kind='user',subject_id='local-user-bob'),identity('alice'))
    question=api.Question(question='Motor-X maximum operating temperature',request_id='e'*32)
    with store.identity_context(identity('bob')):
        answer=api.chat(question,identity('bob'))
        check('authorized comparison dependencies include both owners',{doc,bob}.issubset(answer['source_dependencies']))
    with store.identity_context(identity('alice')):
        api.source_share(doc,api.SourceShare(expected_epoch=2,subject_kind='user',subject_id='local-user-bob',revoke=True),identity('alice'))
    with store.identity_context(identity('bob')):
        try:workflow.invocation_status('local-user-bob','e'*32)
        except LookupError:checks.append('revocation removes a previously cached multi-source answer')
        else:raise AssertionError('Revoked cache leaked')
    with TestClient(api.app) as client:
        response=client.get('/v1/documents',headers={'Authorization':'Bearer '+Path('/tmp/fixture-user-alice').read_text()})
        check('production private HTTP admission remains closed pending full acceptance',response.status_code==503)
    os.environ['NSAI_INDEX_WORKER_ENABLED']='true'
    with TestClient(api.app) as client:
        headers={'Authorization':'Bearer '+Path(os.environ['NSAI_API_TOKEN_FILE']).read_text()}
        response=client.post('/v1/documents',headers=headers,json=dict(title='Owned HTTP lifecycle fixture',version='http-pipeline',text='Motor-Y maximum operating temperature is 90 C.'))
        check('real application HTTP upload enqueues durably',response.status_code==200 and bool(response.json()['index_job']))
        legacy=response.json()['document_id']
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            status=client.get('/v1/sources/'+legacy+'/index',headers=headers)
            if status.status_code==200 and status.json()['ready']:break
            time.sleep(.25)
        else:raise AssertionError('Automatic background indexing did not publish')
        check('lifespan worker automatically publishes without manual indexing',status.json()['state']=='ready')
        response=client.get('/v1/knowledge/'+legacy,headers=headers)
        check('published knowledge is available through actual HTTP application',response.status_code==200)
        response=client.get('/v1/documents',headers=headers)
        check('legacy HTTP identity never lists either private owner source',response.status_code==200 and {row['id'] for row in response.json()['items']}=={legacy})
    os.environ['NSAI_INDEX_WORKER_ENABLED']='false'
    concurrent=[]
    with TestClient(api.app) as client:
        for number in range(2):
            response=client.post('/v1/documents',headers=headers,json=dict(title='Concurrent owned source',version='concurrent-'+str(number),text=source_text()))
            check('concurrent source is durably queued before worker startup',response.status_code==200 and response.json()['indexing']['state']=='queued')
            concurrent.append(response.json()['document_id'])
    os.environ['NSAI_INDEX_WORKER_ENABLED']='true';os.environ['NSAI_INDEX_CONCURRENCY']='2'
    with TestClient(api.app) as client:
        encoded=asyncio.run(jobs.encode_texts(['What is the permitted operating temperature?']))
        check('interactive encoder query succeeds while two background workers are configured',encoded['model_identity']['sha256']==PINNED_MODEL_SHA256)
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            states=[client.get('/v1/sources/'+source+'/index',headers=headers).json() for source in concurrent]
            if all(state['ready'] for state in states):break
            time.sleep(.1)
        else:raise AssertionError('Two-worker queue did not publish both sources')
        check('both prequeued sources publish through the actual two-worker lifecycle',all(state['state']=='ready' for state in states))
        response=client.get('/v1/documents',headers=headers)
        check('two-worker lifecycle retains private source isolation',{row['id'] for row in response.json()['items']}=={legacy,*concurrent})
    print(json.dumps(dict(status='PASS_SCOPED',phase=phase,checks=checks,encoded_on_resume=encoded_count,
        total_passages=resumed_total,
        concurrent_documents=concurrent,
        private_http_admitted=False,model_inference='Actual pinned CPU encoder over HTTP; no language-model generation')))


if __name__=='__main__':main()
