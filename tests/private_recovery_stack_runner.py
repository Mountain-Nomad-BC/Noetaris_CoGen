"""Extend owned upgrade/three-container recovery with populated private state."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'src'))
from qualify_upgrade_recovery import Rehearsal


class PrivateRehearsal(Rehearsal):
    def __init__(self):
        super().__init__(ROOT/'evidence/implementation/private-upgrade-recovery')
        self.fixture_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self.helper_sha=hashlib.sha256((ROOT/'tests/semantic_fixture_helpers.py').read_bytes()).hexdigest()
        self.receipt.update(additional_scope=__doc__,private_fixture_sha256=self.fixture_sha,
            semantic_helper_sha256=self.helper_sha,encoder_scope='Synthetic unit vectors; recovery behavior only, not semantic quality')
        self.save()

    def current_client(self,token,phase,program):
        name=self.tag+'-'+phase;self.containers.append(name)
        result=self.command(phase,['docker','run','--name',name,'--label','nsai.owner='+self.tag,
            '--network',self.network,'--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--user','10001:10001','--pids-limit','64','--cpus','.25','--memory','256m',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777',
            '--env','NSAI_DB_HOST=db','--env','NSAI_DB_NAME=nsai','--env','NSAI_DB_USER=nsai_app',
            '--env','NSAI_DB_PASSWORD_FILE=/run/token','--mount',f'type=bind,source={token},target=/run/token,readonly',
            '--mount',f'type=bind,source={ROOT / "tests/semantic_fixture_helpers.py"},target=/semantic_fixture_helpers.py,readonly',
            '--entrypoint','python',self.current_image,'-c',program],timeout=90)
        output=json.loads(result.stdout.strip().splitlines()[-1])
        (self.output/(phase+'-output.json')).write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
        self.remove(name)
        return output

    def old_image_probe(self,db,token):
        super().old_image_probe(db,token)
        self.token=token
        self.current_image=self.command('pin-current-private-fixture-image',['docker','image','inspect',
            'nsai-implementation-candidate:local','--format','{{.Id}}']).stdout.decode().strip()
        self.receipt['private_application_image']=self.current_image
        program="""import asyncio,json,sys
sys.path.insert(0,'/')
from pathlib import Path
from unittest.mock import patch
from nsai import api,store,security,semantic_jobs as jobs,workflow_store
from semantic_fixture_helpers import configure_authority,synthetic_encode,mixed_extraction_fixture
configure_authority()
alice=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
with store.identity_context(alice):
    published=api.ingest(api.DocumentInput(title='Private restored published',version='1',text='Motor-R maximum operating temperature is 70 C.'),alice)['document_id']
job=jobs.claim_next();assert job is not None
assert asyncio.run(jobs.process_job(job,encode=synthetic_encode))['state']=='succeeded'
with store.identity_context(alice):
    for epoch,target,revoke in [(1,'local-user-bob',False),(2,'local-user-admin',False),(3,'local-user-admin',True)]:
        api.source_share(published,api.SourceShare(expected_epoch=epoch,subject_kind='user',subject_id=target,revoke=revoke),alice)
    mixed_bytes,native,mixed_parsed=mixed_extraction_fixture()
    mixed=workflow_store.persist_source('Preserved native and OCR','1',mixed_bytes,mixed_parsed,alice['actor'])['document_id']
mixed_job=jobs.claim_next();assert mixed_job is not None and mixed_job['document_id']==mixed
assert asyncio.run(jobs.process_job(mixed_job,encode=synthetic_encode))['state']=='succeeded'
with store.identity_context(alice):
    retained=workflow_store.source(mixed)['manifest']['documents'][0]['metadata']['extraction_history'][0]
    assert retained==mixed_parsed['extraction_history'][0] and retained['payload']==native
    pending=api.ingest(api.DocumentInput(title='Private restored checkpoint',version='1',text='Motor-S maximum operating temperature is 71 C.'),alice)['document_id']
job=jobs.claim_next();assert job is not None and job['document_id']==pending
save=jobs._save_checkpoints
class OwnedCheckpointCrash(RuntimeError):pass
def save_then_crash(job,records):
    save(job,records);raise OwnedCheckpointCrash()
with patch('nsai.semantic_jobs._save_checkpoints',side_effect=save_then_crash):
    try:asyncio.run(jobs.process_job(job,encode=synthetic_encode))
    except OwnedCheckpointCrash:pass
    else:raise AssertionError('Owned checkpoint crash did not occur')
assert jobs.fail_job(job,'processing-failed')
print(json.dumps(dict(published=published,pending=pending,mixed=mixed,native_snapshot_sha256=retained['sha256'],native_raw_text=native['raw_text'],mixed_original_sha256=mixed_parsed['original_sha256'],job_id=job['id'],synthetic_encoder=True,synthetic_ocr=True)))
"""
        self.private_state=self.current_client(token,'populate-private-state',program)
        self.receipt['private_fixture']=self.private_state
        self.case('Actual private route functions produce grants revocation native index and durable checkpoint',
            self.sql(db,"SELECT (SELECT count(*) FROM native_semantic_passages),(SELECT count(*) FROM semantic_job_vectors);",'private-fixture-counts').strip()=='2|1')

    def remove(self,name,cleanup=False):
        if name==self.tag+'-restore' and not cleanup:
            program="""import asyncio,json,sys,time
sys.path.insert(0,'/')
from pathlib import Path
from nsai import store,security,semantic_jobs as jobs,workflow_store
from semantic_fixture_helpers import configure_authority,synthetic_encode
configure_authority()
for _ in range(40):
    job=jobs.claim_next()
    if job is not None:break
    time.sleep(.25)
else:raise AssertionError('Restored queued job was not claimable')
calls=[]
async def encode(texts):
    calls.extend(texts);return await synthetic_encode(texts)
result=asyncio.run(jobs.process_job(job,encode=encode))
assert result['state']=='succeeded' and calls==['Index generation identity check']
alice=security.resolve_principal('Bearer '+Path('/tmp/fixture-user-alice').read_text())
with store.identity_context(alice):
    assert jobs.source_status(job['document_id'])['ready']
    original,media=workflow_store.original_source(job['document_id'])
    assert original==b'Motor-S maximum operating temperature is 71 C.'
print(json.dumps(dict(resumed=True,only_model_identity_encoded=True,original_bytes_preserved=True,job_id=job['id'])))
"""
            resumed=self.current_client(self.token,'resume-after-private-restore',program)
            self.case('Fresh-container restored job resumes from valid checkpoint and publishes original source',resumed['resumed'],resumed)
        super().remove(name,cleanup=cleanup)

    def fingerprint(self,db):
        result=super().fingerprint(db)
        if db.endswith('-restore'):
            doc=self.private_state['published']
            access=self.sql(db,f"SELECT nsai_private_can_read('{doc}','local-user-alice'),"
                f"nsai_private_can_read('{doc}','local-user-bob'),"
                f"nsai_private_can_read('{doc}','local-user-admin');",'restored-private-policy').strip()
            self.case('Fresh-container restored private ownership grant and revocation work',access=='t|t|f')
            budget=self.sql(db,'SELECT canonical_bytes=(SELECT sum(octet_length(payload::text)) FROM knowledge_embeddings) FROM semantic_storage_usage;','restored-private-budget').strip()
            self.case('Fresh-container restored semantic byte accounting matches canonical artifacts',budget=='t')
            pending=self.sql(db,"SELECT count(*) FROM semantic_jobs j JOIN semantic_job_vectors v ON v.job_id=j.id WHERE j.state='queued' AND j.document_id='"+self.private_state['pending']+"';",'restored-pending-checkpoint').strip()
            self.case('Fresh-container restored pending job retains checkpoint',pending=='1')
            mixed=self.private_state['mixed']
            preserved=json.loads(self.sql(db,"SELECT json_build_object('snapshot_sha256',manifest#>>'{documents,0,metadata,extraction_history,0,sha256}',"
                "'raw_text',manifest#>>'{documents,0,metadata,extraction_history,0,payload,raw_text}',"
                "'original_sha256',encode(sha256(source_bytes),'hex')) FROM documents WHERE id='"+mixed+"';",'restored-native-and-original').strip())
            self.case('Fresh-container restore preserves original PDF bytes and pre-OCR native extraction',
                preserved==dict(snapshot_sha256=self.private_state['native_snapshot_sha256'],
                    raw_text=self.private_state['native_raw_text'],original_sha256=self.private_state['mixed_original_sha256']))
        return result

    def cleanup(self):
        self.receipt['private_fixture_after_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self.receipt['semantic_helper_after_sha256']=hashlib.sha256((ROOT/'tests/semantic_fixture_helpers.py').read_bytes()).hexdigest()
        if self.fixture_sha!=self.receipt['private_fixture_after_sha256'] or self.helper_sha!=self.receipt['semantic_helper_after_sha256']:self.receipt['status']='FAIL'
        super().cleanup()


if __name__=='__main__':
    run=PrivateRehearsal();receipt=run.execute()
    print(json.dumps(dict(status=receipt['status'],run_id=run.tag,cases=len(receipt['cases']),cleanup=receipt['cleanup_complete'])))
    raise SystemExit(0 if receipt['status']=='PASS_SCOPED' else 1)
