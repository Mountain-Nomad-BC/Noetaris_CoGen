"""Matched current-code connection mechanism experiment on owned ephemeral PostgreSQL.

This compares fresh psycopg connections with the current bounded pool. Both run
the same current all_claims read, data, SQL, pinned images and resource profile.
It never reads production credentials/data, changes source, or benchmarks a
historical application. Output and raw latency samples remain private evidence.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = 100
REPEATS = 3
CONCURRENCY = 8


def command(args, *, input=None, timeout=120):
    result = subprocess.run(args, input=input, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Owned benchmark command failed; credential/driver output withheld')
    return result.stdout


def source_hashes():
    paths = list((ROOT/'src/nsai').rglob('*.py')) + list((ROOT/'database/migrations').glob('*.sql'))
    paths += [ROOT/'deploy/init.sql', ROOT/'scripts/migrate.py', Path(__file__)]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths if '__pycache__' not in p.parts}


def cgroup_snapshot():
    result = {}
    for name in ('memory.current','memory.peak','memory.max','cpu.max','pids.max','cpu.stat'):
        path = Path('/sys/fs/cgroup')/name
        if path.exists(): result[name] = path.read_text().strip()
    return result


def percentile(values, probability):
    # Independent nearest-rank estimator; report raw observations and sample size.
    ordered = sorted(values)
    return ordered[max(0, math.ceil(probability*len(ordered))-1)]


def worker():
    payload = json.load(sys.stdin)
    secret = Path('/tmp/owned-db-password')
    secret.write_text(payload['password'], encoding='ascii');secret.chmod(0o600)
    os.environ.update(NSAI_DB_HOST='owned-db', NSAI_DB_NAME='nsai', NSAI_DB_USER='nsai_app',
                      NSAI_DB_PASSWORD_FILE=str(secret))
    import psycopg
    from nsai import store
    pooled = store.connect
    original_connect = psycopg.connect
    connection_counter = 0
    lock = threading.Lock()
    def counted_connect(**kwargs):
        nonlocal connection_counter
        with lock: connection_counter += 1
        return original_connect(**kwargs)
    psycopg.connect = counted_connect
    @contextmanager
    def direct():
        settings = dict(host=os.environ['NSAI_DB_HOST'], dbname=os.environ['NSAI_DB_NAME'],
            user=os.environ['NSAI_DB_USER'], password=store._secret(str(secret)), connect_timeout=3,
            options='-c statement_timeout=10000 -c lock_timeout=5000 -c idle_in_transaction_session_timeout=15000')
        with psycopg.connect(**settings) as conn: yield conn
    def digest(rows):
        return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    # One shared warm data/cache read; separately label pool startup and block reuse.
    store.connect = direct
    expected = [dict(id=hashlib.md5(('claim-'+str(i)).encode()).hexdigest(),
        document_id=hashlib.md5(('doc-'+str((i-1)//20+1)).encode()).hexdigest(),
        subject='device-'+str(i),predicate='operating limit',value='85C',
        locator='line:'+str((i-1)%20+1),status='candidate',revision=1,reviewed_by=None)
        for i in range(1,2001)]
    expected_hash = digest(expected)
    if digest(store.all_claims()) != expected_hash:
        raise AssertionError('Synthetic rows differ from independent logical fixture oracle')
    blocks = []
    plans = []
    with direct() as conn:
        for query in ['SELECT count(*) FROM claims',
            'SELECT id,document_id,subject,predicate,value,locator,status,revision,reviewed_by FROM claims ORDER BY created_at,id LIMIT 2000']:
            plans.append(conn.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query).fetchone()[0])
    for repetition in range(REPEATS):
        for concurrency in (1, CONCURRENCY):
            order = ('direct','pool') if repetition%2 == 0 else ('pool','direct')
            for mechanism in order:
                store.connect = direct if mechanism == 'direct' else pooled
                before_connections = connection_counter
                resources_before = cgroup_snapshot()
                def read_once(index):
                    started = time.perf_counter()
                    rows = store.all_claims()
                    elapsed_ms = (time.perf_counter()-started)*1000
                    if digest(rows) != expected_hash or len(rows) != 2000:
                        raise AssertionError('Read quality differs from frozen expected output')
                    return {'index':index,'latency_ms':elapsed_ms,'rows':len(rows)}
                started = time.perf_counter()
                if concurrency == 1:
                    observations = [read_once(index) for index in range(SAMPLES)]
                else:
                    with ThreadPoolExecutor(max_workers=concurrency) as executor:
                        observations = list(executor.map(read_once, range(SAMPLES)))
                seconds = time.perf_counter()-started
                latencies = [o['latency_ms'] for o in observations]
                blocks.append({'repeat':repetition+1,'concurrency':concurrency,'mechanism':mechanism,
                    'order':list(order),'samples':SAMPLES,'seconds':seconds,
                    'p50_ms':percentile(latencies,.50),'p95_ms':percentile(latencies,.95),
                    'mean_ms':sum(latencies)/len(latencies),'connections_opened':connection_counter-before_connections,
                    'raw_observations':observations,'quality_sha256':expected_hash,'all_rows':2000,
                    'resources_before':resources_before,'resources_after':cgroup_snapshot(),
                    'phase':'shared database caches warmed; pool initializes on first pool block and stays warm thereafter'})
    store.connect = direct
    if digest(store.all_claims()) != expected_hash: raise AssertionError('Fixture mutated during reads')
    settings = dict(host='owned-db', dbname='nsai', user='nsai_app', password=store._secret(str(secret)), connect_timeout=3)
    with original_connect(**settings) as conn:
        row = conn.execute('SELECT version(),pg_database_size(current_database()),current_setting(\'max_connections\')').fetchone()
        database = dict(version=row[0],bytes=row[1],max_connections=row[2])
    # These are the only connections in this worker; release explicitly before exit.
    from queue import Empty
    while True:
        try: _, connection = store._idle.get_nowait();connection.close()
        except Empty: break
    secret.unlink()
    return {'status':'PASS_SCOPED','blocks':blocks,'query_plans':plans,'database':database,
        'read_operations':SAMPLES*REPEATS*2*2,'output_quality_identical':True,'fixture_rows':2000,
        'fixture_documents':100,'quality_sha256':expected_hash,'runtime_python':sys.version,
        'psycopg_version':psycopg.__version__,'store_file':store.__file__,
        'store_sha256':hashlib.sha256(Path(store.__file__).read_bytes()).hexdigest(),
        'connection_count_method':'successful psycopg connect invocations counted under a lock',
        'latency_scope':'all_claims SQL/materialization including connection acquisition/commit/close; output hashing excluded from per-read latency and included in block elapsed',
        'limitations':['Current mechanism comparison, not historical baseline or whole-application benchmark.',
            'Eight worker threads are compared against the configured four-connection pool; direct path may open eight connections.',
            'No cold database/server start qualification; paired order alternates over three repetitions.',
            'No read-write/event-loop workload, inference/retrieval quality, production scalability or independent operating-system noise isolation.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--candidate-image',default='nsai-implementation-candidate:local')
    parser.add_argument('--database-image',default='postgres:16-alpine')
    args = parser.parse_args()
    if args.worker:
        try: print(json.dumps(worker()))
        except Exception as error:
            print(json.dumps({'status':'FAIL','error_type':type(error).__name__,'reason':'Owned worker failed; raw credential/driver diagnostics withheld'}))
            return 1
        return 0
    output = ROOT/'evidence/implementation/database-performance'
    output.mkdir(parents=True,exist_ok=True)
    tag = uuid4().hex[:12];prefix = 'nsai-db-performance-'+tag
    network = prefix+'-net';db = prefix+'-db';client = prefix+'-worker'
    before = source_hashes()
    def image_id(name): return json.loads(command(['docker','image','inspect',name]))[0]['Id']
    api_image, db_image = image_id(args.candidate_image), image_id(args.database_image)
    declaration = {'run_id':prefix,'started_at':datetime.now(timezone.utc).isoformat(),
        'status':'RUNNING','scope':'owned internal network/tmpfs PostgreSQL; no production resources or host ports',
        'samples_per_block':SAMPLES,'repeats':REPEATS,'concurrency_profiles':[1,CONCURRENCY],
        'paired_order':[['direct','pool'],['pool','direct'],['direct','pool']],
        'corpus':{'documents':100,'claims':2000,'seed':'original deterministic generate_series fixture'},
        'images':{'candidate':api_image,'database':db_image},'sources_before':before,
        'limits':{'worker_cpu':1,'worker_memory':'768m','worker_pids':128,'db_cpu':1,'db_memory':'1g','db_tmpfs':'256m'},
        'owned_only':True,'cleanup':[]}
    (output/'predeclared-profile.json').write_text(json.dumps(declaration,indent=2),encoding='utf-8')
    owned = []
    try:
        command(['docker','network','create','--internal','--label','nsai.owner='+tag,network]);owned.append(('network',network))
        password = secrets.token_urlsafe(48)
        command(['docker','run','-d','--name',db,'--label','nsai.owner='+tag,'--network',network,'--network-alias','owned-db',
            '--read-only','--user','70:70','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--cpus','1','--memory','1g','--pids-limit','128','--tmpfs','/var/lib/postgresql/data:rw,nosuid,size=256m,mode=1777',
            '--tmpfs','/var/run/postgresql:rw,nosuid,size=8m,mode=1777','--tmpfs','/tmp:rw,nosuid,size=32m',
            '--env','PGDATA=/var/lib/postgresql/data/pgdata','--env','POSTGRES_USER=nsai','--env','POSTGRES_DB=nsai',
            '--env','POSTGRES_PASSWORD='+password,db_image]);owned.append(('container',db))
        for _ in range(80):
            ready = subprocess.run(['docker','exec',db,'pg_isready','-U','nsai','-d','nsai'],capture_output=True,timeout=5)
            if ready.returncode == 0: break
            time.sleep(.25)
        else: raise RuntimeError('Owned DB readiness deadline exceeded')
        spec = importlib.util.spec_from_file_location('owned_migrations',ROOT/'scripts/migrate.py')
        migration = importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
        sql = migration.migration_sql(ROOT)+migration.role_sql(password)
        command(['docker','exec','-i',db,'psql','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],input=sql.encode())
        seed = """BEGIN;
        INSERT INTO documents(id,title,source_version,sha256,raw_text,source_bytes,original_sha256,media_type,ingested_by)
        SELECT md5('doc-'||i),'Owned original fixture '||i,i::text,encode(sha256(convert_to(source,'UTF8')),'hex'),source,
        convert_to(source,'UTF8'),encode(sha256(convert_to(source,'UTF8')),'hex'),'text/plain','owned-benchmark'
        FROM generate_series(1,100) i CROSS JOIN LATERAL
        (SELECT string_agg('device-'||j||' operating limit is 85C',E'\n' ORDER BY j) AS source
         FROM generate_series((i-1)*20+1,i*20) j) s;
        INSERT INTO claims(id,document_id,subject,predicate,value,locator,status,created_at)
        SELECT md5('claim-'||i),md5('doc-'||((i-1)/20+1)), 'device-'||i,'operating limit','85C','line:'||((i-1)%20+1),'candidate',
        '2026-10-14T00:00:00Z'::timestamptz+i*interval '1 second' FROM generate_series(1,2000) i;
        ANALYZE claims; COMMIT;"""
        command(['docker','exec','-i',db,'psql','-v','ON_ERROR_STOP=1','-U','nsai','-d','nsai'],input=seed.encode())
        owned.append(('container',client))
        raw = command(['docker','run','--rm','-i','--name',client,'--label','nsai.owner='+tag,'--network',network,
            '--read-only','--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges:true',
            '--cpus','1','--memory','768m','--pids-limit','128','--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
            '--mount','type=bind,source='+str(ROOT/'src')+',target=/qualified-src,readonly',
            '--mount','type=bind,source='+str(Path(__file__).resolve())+',target=/benchmark.py,readonly',
            '--env','PYTHONPATH=/qualified-src','--entrypoint','python',api_image,'/benchmark.py','--worker'],
            input=json.dumps({'password':password}).encode(),timeout=300)
        results = json.loads(raw)
        if results.get('status') != 'PASS_SCOPED': raise RuntimeError('Owned mechanism benchmark failed')
        (output/(prefix+'-results.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')
        declaration.update(status='PASS_SCOPED',results_file=prefix+'-results.json',source_binding='read-only current src overrides the pinned candidate Python package',
                           sources_after=source_hashes())
        if declaration['sources_after'] != before:
            declaration.update(status='UNQUALIFIED_SOURCE_CHANGED')
    except Exception as error:
        declaration.update(status='FAIL',error_type=type(error).__name__,error='Owned benchmark failed; no production resources involved')
    finally:
        for kind,name in reversed(owned):
            inspected = subprocess.run(['docker',kind,'inspect',name],capture_output=True,timeout=15)
            if inspected.returncode:
                declaration['cleanup'].append({'resource':name,'already_absent':True});continue
            value = json.loads(inspected.stdout)[0]
            labels = value.get('Config',{}).get('Labels',{}) if kind=='container' else value.get('Labels',{})
            if labels.get('nsai.owner') != tag:
                declaration['cleanup'].append({'resource':name,'removed':False,'reason':'ownership mismatch'});continue
            command(['docker','rm','-f',name] if kind=='container' else ['docker','network','rm',name])
            declaration['cleanup'].append({'resource':name,'removed':True})
        declaration['cleanup_complete'] = all(v.get('removed') or v.get('already_absent') for v in declaration['cleanup'])
        if not declaration['cleanup_complete']: declaration['status']='FAIL_CLEANUP'
        declaration['captured_at']=datetime.now(timezone.utc).isoformat()
        (output/(prefix+'-receipt.json')).write_text(json.dumps(declaration,indent=2),encoding='utf-8')
        (output/'current.json').write_text(json.dumps(declaration,indent=2),encoding='utf-8')
    print(json.dumps({'status':declaration['status'],'receipt':str(output/'current.json')}))
    return int(declaration['status'] != 'PASS_SCOPED')


if __name__=='__main__': raise SystemExit(main())
