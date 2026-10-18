"""Fixed, read-only runtime assurance checks inside the actual API container."""
import json
import os
from pathlib import Path
from . import store

results = dict(uid=os.getuid(),docker_socket_present=Path('/var/run/docker.sock').exists())
assert results['uid']==10001 and not results['docker_socket_present']
status=Path('/proc/self/status').read_text()
assert 'NoNewPrivs:\t1' in status
assert 'CapEff:\t0000000000000000' in status
assert 'Seccomp:\t2' in status
results.update(no_new_privileges=True,effective_capabilities='none',seccomp_filter=True)
try:
    Path('/app/forbidden-write').write_text('probe')
    raise AssertionError('Root filesystem writable')
except (OSError,PermissionError): results['readonly_root_enforced']=True
with store.connect() as conn:
    role=conn.execute('SELECT current_user,rolsuper FROM pg_roles WHERE rolname=current_user').fetchone()
    assert role[0]=='nsai_app' and role[1] is False
    privileges={name:conn.execute("SELECT has_table_privilege(current_user,%s,'UPDATE'),has_table_privilege(current_user,%s,'DELETE')", (name,name)).fetchone() for name in ['documents','source_spans','chunks','audit_events']}
    assert all(not update and not delete for update,delete in privileges.values())
    assert not conn.execute("SELECT has_schema_privilege(current_user,'public','CREATE')").fetchone()[0]
    results.update(database_role=role[0],database_superuser=False,immutable_table_privileges=privileges,ddl_denied=True)
print(json.dumps(results,indent=2))
