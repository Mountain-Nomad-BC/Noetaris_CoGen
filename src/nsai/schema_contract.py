"""Fail closed on owner credentials, missing RLS or a different migration journal."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import stat

ROOT=Path(__file__).resolve().parents[2]
RLS_TABLES=frozenset({'documents','claims','claim_events','source_spans','chunks','audit_events',
    'sessions','session_messages','learning_proposals','inference_runs','governed_records',
    'governed_reviews','invocation_receipts','document_knowledge','knowledge_embeddings','research_supplements',
    'native_semantic_passages','cost_accounts','cost_reservations','cost_events','operation_admissions',
    'oauth_pending_states','oauth_accounts','oauth_bindings','oauth_login_sessions','oauth_identity_events',
    'oauth_browser_epochs'})


@lru_cache(maxsize=1)
def expected_migrations():
    paths=[ROOT/'deploy/init.sql']+sorted((ROOT/'database/migrations').glob('*.sql'))
    if len(paths)<2:raise RuntimeError('Packaged schema contract is unavailable')
    result={}
    for path in paths:
        info=path.lstat()
        if path.is_symlink() or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            raise RuntimeError('Schema contract links are not admitted')
        result[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify_database_contract(conn):
    authority=conn.execute("""
      SELECT r.rolname='nsai_app' AND current_user=session_user
        AND r.rolcanlogin AND NOT(r.rolsuper OR r.rolbypassrls OR r.rolcreatedb OR r.rolcreaterole OR r.rolreplication)
        AND NOT EXISTS(SELECT 1 FROM pg_auth_members WHERE member=r.oid)
        AND NOT EXISTS(SELECT 1 FROM pg_database WHERE oid=(SELECT oid FROM pg_database WHERE datname=current_database()) AND datdba=r.oid)
        AND NOT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='public' AND nspowner=r.oid)
        AND NOT EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relowner=r.oid)
        AND NOT EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proowner=r.oid)
      FROM pg_roles r WHERE r.rolname=current_user
    """).fetchone()
    if not authority or authority[0] is not True:
        raise RuntimeError('Application database authority is not admitted')
    actual=dict(conn.execute('SELECT name,sha256 FROM nsai_schema_migrations').fetchall())
    if actual!=expected_migrations():raise RuntimeError('Application database schema contract does not match')
    enabled={row[0] for row in conn.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname=ANY(%s) AND c.relrowsecurity",
                                           (sorted(RLS_TABLES),)).fetchall()}
    if enabled!=RLS_TABLES:raise RuntimeError('Application source row security is incomplete')
    major=conn.execute("SELECT current_setting('server_version_num')::integer/10000").fetchone()[0]
    contract=expected_access_contract(major)
    actual_definitions=conn.execute(ACCESS_DEFINITIONS_SQL).fetchone()[0]
    if definitions_hash(actual_definitions)!=contract['definitions_sha256']:
        raise RuntimeError('Application database access definitions do not match')


ACCESS_DEFINITIONS_SQL = r"""WITH base AS (SELECT jsonb_build_object('policies',coalesce((SELECT jsonb_agg(jsonb_build_object('table',c.relname,'name',p.polname,'cmd',p.polcmd,'permissive',p.polpermissive,'roles',p.polroles::text,'using',pg_get_expr(p.polqual,p.polrelid),'check',pg_get_expr(p.polwithcheck,p.polrelid)) ORDER BY c.relname COLLATE "C",p.polname COLLATE "C") FROM pg_policy p JOIN pg_class c ON c.oid=p.polrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'),'[]'::jsonb),'functions',coalesce((SELECT jsonb_agg(pg_get_functiondef(p.oid) ORDER BY p.proname COLLATE "C",pg_get_function_identity_arguments(p.oid) COLLATE "C") FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname LIKE 'nsai\_%' ESCAPE '\'),'[]'::jsonb))) SELECT (SELECT * FROM base)||jsonb_build_object( 'triggers',coalesce((SELECT jsonb_agg(jsonb_build_array(c.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid)) ORDER BY c.relname COLLATE "C",t.tgname COLLATE "C") FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT t.tgisinternal),'[]'::jsonb),
 'constraints',coalesce((SELECT jsonb_agg(jsonb_build_array(c.relname,k.conname,k.convalidated,pg_get_constraintdef(k.oid)) ORDER BY c.relname COLLATE "C",k.conname COLLATE "C") FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'),'[]'::jsonb),
 'columns',coalesce((SELECT jsonb_agg(jsonb_build_object('table',c.relname,'name',a.attname,'position',a.attnum,'type',format_type(a.atttypid,a.atttypmod),'collation_schema',cn.nspname,'collation',co.collname,'not_null',a.attnotnull,'identity',a.attidentity,'generated',a.attgenerated,'default',pg_get_expr(d.adbin,d.adrelid)) ORDER BY c.relname COLLATE "C",a.attnum) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace LEFT JOIN pg_collation co ON co.oid=a.attcollation LEFT JOIN pg_namespace cn ON cn.oid=co.collnamespace LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f') AND a.attnum>0 AND NOT a.attisdropped),'[]'::jsonb),
 'application_acl',coalesce((SELECT jsonb_agg(jsonb_build_array(kind,object_name,column_name,CASE WHEN grantee=0 THEN 'PUBLIC' ELSE 'application' END,privilege_type,is_grantable) ORDER BY kind COLLATE "C",object_name COLLATE "C",column_name COLLATE "C",CASE WHEN grantee=0 THEN 'PUBLIC' ELSE 'application' END COLLATE "C",privilege_type COLLATE "C",is_grantable) FROM (
 SELECT 'relation'::text AS kind,c.relname::text AS object_name,NULL::text AS column_name,a.* FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault((CASE WHEN c.relkind='S' THEN 'S' ELSE 'r' END)::"char",c.relowner))) a WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','f','S')
 UNION ALL SELECT 'column',c.relname,col.attname,a.* FROM pg_attribute col JOIN pg_class c ON c.oid=col.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(col.attacl) a WHERE n.nspname='public' AND col.attnum>0 AND NOT col.attisdropped
 UNION ALL SELECT 'function',p.proname||'('||pg_get_function_identity_arguments(p.oid)||')',NULL,a.* FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE n.nspname='public'
 UNION ALL SELECT 'schema',n.nspname,NULL,a.* FROM pg_namespace n CROSS JOIN LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) a WHERE n.nspname='public'
 UNION ALL SELECT 'database','current',NULL,a.* FROM pg_database d CROSS JOIN LATERAL aclexplode(coalesce(d.datacl,acldefault('d',d.datdba))) a WHERE d.datname=current_database()
 ) permissions WHERE grantee IN (0,(SELECT oid FROM pg_roles WHERE rolname=current_user))),'[]'::jsonb)
);
"""


def definitions_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


@lru_cache(maxsize=2)
def expected_access_contract(major=16):
    if type(major) is not int or major not in {16,18}:
        raise RuntimeError('Application database version is not admitted')
    path=ROOT/('database/access-contract.json' if major==16 else 'database/access-contract-pg18.json')
    info=path.lstat()
    if (path.is_symlink() or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024)
        or info.st_size>512*1024):raise RuntimeError('Packaged database access contract is invalid')
    contract=json.loads(path.read_bytes())
    if (contract.get('postgres_major')!=major
        or contract.get('schema_version')!='nsai.database-access-contract/1'
        or contract.get('migration_sha256')!=expected_migrations()
        or contract.get('query_sha256')!=hashlib.sha256(ACCESS_DEFINITIONS_SQL.encode()).hexdigest()
        or set(contract.get('definitions',{}))!={'policies','functions','triggers','constraints','columns','application_acl'}
        or definitions_hash(contract['definitions'])!=contract.get('definitions_sha256')):
        raise RuntimeError('Packaged database access contract does not match migrations')
    return contract
