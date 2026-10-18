"""Explicit local migration, separate owner credentials and least-privilege app role."""
from pathlib import Path
import subprocess
import sys
from datetime import datetime,timezone
import hashlib
import json
import os
import time
import queue
import threading
from uuid import uuid4
ROOT = Path(__file__).resolve().parents[1]

def stream_backup(args, target, max_bytes=64*1024*1024, timeout=120):
    """Pipe into an exclusive private file; enforce bytes before writing and a wall deadline."""
    target=Path(target)
    partial=target.with_suffix(target.suffix+'.partial')
    manifest=target.with_suffix(target.suffix+'.manifest.json')
    manifest_partial=manifest.with_suffix(manifest.suffix+'.partial')
    owns_manifest_partial=False
    # Never replace another capture's manifest, including a dangling link.
    if os.path.lexists(target) or os.path.lexists(manifest):
        raise FileExistsError('Backup or manifest already exists')
    fd=os.open(partial,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    process=None; reader=None; cancelled=threading.Event()
    blocks=queue.Queue(maxsize=2)
    def offer(value):
        while not cancelled.is_set():
            try: blocks.put(value,timeout=.05); return
            except queue.Full: pass
    def read_pipe():
        try:
            while not cancelled.is_set():
                block=process.stdout.read(65536)
                if not block: break
                offer(block)
            offer(None)
        except Exception as error: offer(error)
    try:
        with os.fdopen(fd,'wb') as stream:
            # Child owns only the pipe: never inherits an open backup file handle.
            process=subprocess.Popen(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            reader=threading.Thread(target=read_pipe,daemon=True);reader.start()
            deadline=time.monotonic()+timeout; size=0
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0: raise RuntimeError('Backup exceeded configured time budget')
                try: block=blocks.get(timeout=min(remaining,.1))
                except queue.Empty: continue
                if isinstance(block,Exception): raise RuntimeError('Backup pipe failed') from block
                if block is None: break
                if size+len(block)>max_bytes: raise RuntimeError('Backup exceeded configured size budget')
                stream.write(block);size+=len(block)
            remaining=deadline-time.monotonic()
            if remaining<=0: raise RuntimeError('Backup exceeded configured time budget')
            try: result=process.wait(timeout=remaining)
            except subprocess.TimeoutExpired as error: raise RuntimeError('Backup exceeded configured time budget') from error
            if result: raise RuntimeError('Backup command failed')
            stream.flush();os.fsync(stream.fileno())
        os.link(partial,target)  # atomic create-if-absent; no check/rename overwrite race
        partial.unlink()
        digest=hashlib.sha256()
        with target.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
        # Exclusive creation avoids overwriting a manifest introduced during capture.
        # A write failure is a failed capture; the SQL is retained for inspection,
        # and consumers must require a valid complete manifest before recovery.
        manifest_fd=os.open(manifest_partial,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        owns_manifest_partial=True
        with os.fdopen(manifest_fd,'w',encoding='utf-8') as stream:
            json.dump(dict(captured_at=datetime.now(timezone.utc).isoformat(),sha256=digest.hexdigest(),size_bytes=target.stat().st_size,restore_verified=False),stream)
            stream.flush();os.fsync(stream.fileno())
        os.link(manifest_partial,manifest)
        manifest_partial.unlink();owns_manifest_partial=False
        return target
    finally:
        cancelled.set()
        if process is not None:
            if process.poll() is None: process.kill()
            process.wait(timeout=10)
            if reader is not None: reader.join(timeout=10)
            if process.stdout is not None: process.stdout.close()
        if partial.exists(): partial.unlink()
        if owns_manifest_partial and manifest_partial.exists():manifest_partial.unlink()


def migration_sql(root):
    """Ordered immutable journal, serialized and transactional; unknown/edited history is denied."""
    root=Path(root)
    paths=[root/'deploy/init.sql']+sorted((root/'database/migrations').glob('*.sql'))
    entries=[(path.relative_to(root).as_posix(),hashlib.sha256(path.read_bytes()).hexdigest(),path.read_text(encoding='utf-8')) for path in paths]
    names=','.join("'"+name.replace("'","''")+"'" for name,_,_ in entries)
    sql="BEGIN; SELECT pg_advisory_xact_lock(873211004); SET LOCAL statement_timeout='120s';\n"
    sql+="CREATE TABLE IF NOT EXISTS nsai_schema_migrations(name text PRIMARY KEY, sha256 text NOT NULL CHECK(length(sha256)=64), applied_at timestamptz NOT NULL DEFAULT now());\n"
    sql+=f"DO $$ BEGIN IF EXISTS(SELECT 1 FROM nsai_schema_migrations WHERE name NOT IN ({names})) THEN RAISE EXCEPTION 'Migration history contains unknown entries'; END IF; END $$;\n"
    for name,digest,body in entries:
        # psql conditionals let arbitrary SQL run outside PL/pgSQL, while keeping one transaction.
        escaped=name.replace("'","''")
        sql+=f"DO $$ BEGIN IF EXISTS(SELECT 1 FROM nsai_schema_migrations WHERE name='{escaped}' AND sha256<>'{digest}') THEN RAISE EXCEPTION 'Applied migration hash mismatch'; END IF; END $$;\n"
        sql+=f"SELECT NOT EXISTS(SELECT 1 FROM nsai_schema_migrations WHERE name='{escaped}') AS migration_needed \\gset\n\\if :migration_needed\n"
        sql+=body+f"\nINSERT INTO nsai_schema_migrations(name,sha256) VALUES ('{escaped}','{digest}');\n\\endif\n"
    return sql


def role_sql(password, include_commit=True):
    """One privilege contract for deployment and owned qualification; never prints credentials."""
    if (not isinstance(password,str) or not password.isascii() or not 32<=len(password)<=1024
        or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-' for c in password)):
        raise ValueError('Invalid bounded ASCII database credential')
    if type(include_commit) is not bool: raise ValueError('Commit option must be boolean')
    sql=''
    sql += "\nDO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='nsai_app') THEN CREATE ROLE nsai_app LOGIN PASSWORD '" + password + "'; END IF; END; $$;\n"
    sql += '''
    ALTER ROLE nsai_app NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
    DO $$ DECLARE membership RECORD; BEGIN
    FOR membership IN SELECT r.rolname FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid JOIN pg_roles member ON member.oid=m.member WHERE member.rolname='nsai_app'
    LOOP EXECUTE format('REVOKE %I FROM nsai_app',membership.rolname); END LOOP;
    END $$;
    REVOKE ALL ON DATABASE nsai FROM nsai_app;
    GRANT CONNECT ON DATABASE nsai TO nsai_app;
    REVOKE ALL ON SCHEMA public FROM nsai_app;
    REVOKE ALL ON ALL TABLES IN SCHEMA public FROM nsai_app;
    REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM nsai_app;
    REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM nsai_app;
    REVOKE ALL ON SCHEMA public FROM PUBLIC;
    GRANT USAGE ON SCHEMA public TO nsai_app;
    GRANT SELECT,INSERT ON documents,claims,claim_events,source_spans,chunks,audit_events,sessions,session_messages,learning_proposals,inference_runs TO nsai_app;
    GRANT SELECT,INSERT ON governed_records,governed_reviews,policy_actions,invocation_receipts TO nsai_app;
    GRANT SELECT,INSERT ON document_knowledge,knowledge_embeddings,research_supplements TO nsai_app;
    GRANT UPDATE(state,approved_by,receipt_sha256) ON policy_actions TO nsai_app;
    GRANT UPDATE(state,response) ON invocation_receipts TO nsai_app;
    GRANT UPDATE(source_ids,provenance_complete) ON invocation_receipts TO nsai_app;
    GRANT UPDATE(status,revision,reviewed_by) ON claims TO nsai_app;
    GRANT UPDATE(source_ids,provenance_complete) ON claims TO nsai_app;
    GRANT UPDATE(state,revision) ON learning_proposals TO nsai_app;
    GRANT UPDATE(state,details) ON inference_runs TO nsai_app;
    GRANT UPDATE(source_ids,provenance_complete) ON inference_runs TO nsai_app;
    GRANT SELECT ON local_policy TO nsai_app;
    GRANT SELECT ON nsai_schema_migrations TO nsai_app;
    GRANT UPDATE(revision,inference_enabled,daily_call_limit,max_output_tokens,central_config) ON local_policy TO nsai_app;
    GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO nsai_app;
    -- Sequence values would reveal private policy/access-event activity.
    REVOKE ALL ON SEQUENCE private_access_events_id_seq FROM nsai_app;
    REVOKE ALL ON SEQUENCE semantic_job_events_id_seq FROM nsai_app;
    REVOKE ALL ON SEQUENCE cost_events_id_seq FROM nsai_app;
    REVOKE ALL ON SEQUENCE oauth_identity_events_id_seq FROM nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_reserve_cost(text,text,text,bigint,bigint,bigint),
      nsai_settle_cost(text,bigint,bigint,bigint),nsai_active_inference_count(),nsai_cost_status() TO nsai_app;
    -- Private policy tables are never directly available to the application.
    GRANT EXECUTE ON FUNCTION nsai_operation_begin(text,text,integer,integer,integer,integer),
      nsai_operation_claim(text,integer),nsai_operation_finish(text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_oauth_state_put(text,text,text),nsai_oauth_state_take(text,text),
      nsai_oauth_state_clear(text,text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_oauth_bind(text,text,text,text),
      nsai_oauth_session_create(text,text,text,integer),nsai_oauth_session_resolve(text),
      nsai_oauth_session_revoke(text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_oauth_browser_epoch(text),nsai_oauth_browser_assert(text,bigint),
      nsai_oauth_session_create(text,text,text,integer,text,bigint),nsai_oauth_browser_cancel(text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_current_oauth_sharing_target(text,text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_private_share(text,text,bigint,text,text,timestamptz,boolean),
      nsai_private_can_read(text,text),
      nsai_private_authorize_read(text,text,text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_document_visible(text),nsai_audit_head(),
      nsai_actor(),nsai_actor_role(),nsai_legacy_context(),nsai_pending_source_insert(text,text,text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_sources_visible(text[],boolean),
      nsai_artifact_visible(text,text[],boolean,boolean),nsai_daily_inference_count(),
      nsai_current_source_dependencies() TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_current_source_access(text),
      nsai_current_source_share(text,bigint,text,text,timestamptz,boolean) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_enqueue_semantic_job(text,text,text,text),
      nsai_claim_semantic_job(text,text[],integer,integer),nsai_job_source_allowed(text),
      nsai_publish_semantic_job(text,uuid,text,text[]),nsai_fail_semantic_job(text,uuid,text),
      nsai_source_index_status(text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_put_semantic_checkpoints(text,uuid,jsonb),
      nsai_get_semantic_checkpoints(text,uuid),nsai_retry_semantic_job(text,bigint) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_source_is_owner(text),nsai_index_source_readable(text) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_cancel_semantic_job(text,bigint),
      nsai_set_semantic_job_priority(text,bigint,integer) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_library_lexical_search(text,text,text,text[],text,integer[],integer) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_claim_context(jsonb,text[],text,integer[]),
      nsai_memory_claim_seeds(text,text[],text,integer[]),
      nsai_claim_review_page(integer,timestamptz,text),nsai_reflection_claims() TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_source_capacity_available(integer) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_library_semantic_search(double precision[],text[],text,integer[],text,integer) TO nsai_app;
    GRANT EXECUTE ON FUNCTION nsai_register_source_manifest(text[]),nsai_source_manifest_sources(text) TO nsai_app;
    '''
    return sql+('COMMIT;\n' if include_commit else '')


def main():
    # Direct CLI invocation must obey the same admission as the deployment launcher.
    # Imported pure SQL/backup helpers remain available to owned test fixtures.
    admission=subprocess.run([sys.executable,str(ROOT/'scripts/check_release_readiness.py')],
        cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
    if admission.returncode:
        raise SystemExit('Migration denied: independent foundation release admission is incomplete. No credentials, backup or database changes were made.')
    password = (ROOT/'secrets/app_db_password.txt').read_text().strip()
    privileges = role_sql(password)
    backup_root=ROOT/'state/backups'; backup_root.mkdir(parents=True,exist_ok=True)
    backup_file=backup_root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex+'.sql')
    stream_backup(['docker','compose','exec','-T','db','pg_dump','-U','nsai','-d','nsai'], backup_file)
    sql = migration_sql(ROOT)+privileges
    result = subprocess.run(['docker','compose','exec','-T','db','psql','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],
        cwd=ROOT,input=sql.encode('utf-8'),capture_output=True,timeout=120)
    if result.returncode:
        # Do not print SQL or credential-containing driver errors.
        raise SystemExit('Migration failed; inspect DB locally. No credential output retained.')
    print('Ordered migrations journaled atomically; nsai_app privileges converged.')

if __name__ == "__main__":
    main()
