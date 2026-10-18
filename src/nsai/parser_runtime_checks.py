"""Fixed parser containment probes; not an arbitrary-code executor certification."""
import json
import os
from pathlib import Path
import socket
import subprocess

assert os.getuid()==10001
assert set(p.name for p in Path('/run/secrets').iterdir())=={'parser_token'}
assert not Path('/var/run/docker.sock').exists()
status=Path('/proc/self/status').read_text()
assert 'NoNewPrivs:\t1' in status and 'CapEff:\t0000000000000000' in status and 'Seccomp:\t2' in status
try:
    connection=socket.create_connection(('1.1.1.1',80),timeout=2)
    connection.close();raise AssertionError('Parser unexpectedly has external egress')
except OSError:pass
try:
    socket.getaddrinfo('db',5432);raise AssertionError('Parser unexpectedly resolves database network')
except socket.gaierror:pass
path=Path('/tmp/nsai-fixed-noexec-probe.sh')
path.write_text('#!/bin/sh\nexit 0\n');path.chmod(0o700)
try:
    subprocess.run([str(path)],check=True);raise AssertionError('Parser tmpfs allows native executable launch')
except PermissionError:pass
finally:path.unlink()
report=dict(status='PASS',uid=10001,secret_mounts=['parser_token'],no_database_network=True,
    external_egress_denied=True,tmpfs_noexec_enforced=True,no_new_privileges=True,seccomp_filter=True,
    scope='fixed parser service only; does not certify an arbitrary-code sandbox')
print(json.dumps(report,indent=2))
