"""Source-owned lock integrity; actual solver/build/runtime evidence is separate."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def test_package_lock_is_complete_unique_exact_data_without_shell_flags():
    data=(ROOT/'deploy/db/apk-package-closure.lock').read_bytes()
    assert b'\r' not in data
    rows=data.decode('ascii').splitlines()
    assert rows==sorted(rows) and len(rows)==len(set(rows))==46
    assert all(re.fullmatch(r'\.?[a-z0-9][a-z0-9+_.-]*=[0-9][A-Za-z0-9._+~-]*',row) for row in rows)
    packages=dict(row.split('=',1) for row in rows)
    assert packages['libcrypto3']=='3.5.9-r0'
    assert packages['libssl3']=='3.5.9-r0'
    assert packages['su-exec']=='0.3-r0'
    assert packages['.postgresql-rundeps']=='20260917.213122'
