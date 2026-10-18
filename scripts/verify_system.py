"""Observational local liveness/readiness only; owned runners provide stateful acceptance."""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import json
import os
import time
from urllib.parse import urlsplit
import httpx

ROOT=Path(__file__).resolve().parents[1]

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readiness-only',action='store_true')
    args=parser.parse_args(argv)
    if not args.readiness_only:
        parser.error('Use --readiness-only for observational checks. Stateful acceptance is owned by scripts/qualify_local_stack.py.')
    base=os.getenv('NSAI_BASE_URL','http://127.0.0.1:8787').rstrip('/')
    try:
        parsed=urlsplit(base)
        port=parsed.port
        valid=(parsed.scheme=='http' and parsed.hostname=='127.0.0.1' and not parsed.username and not parsed.password
               and not parsed.path and not parsed.query and not parsed.fragment and port is not None and 1<=port<=65535)
    except ValueError:
        valid=False
    if not valid:
        parser.error('Readiness accepts an explicit local loopback HTTP service only.')
    checks=[]
    with httpx.Client(timeout=3,trust_env=False,follow_redirects=False) as client:
        for path,status in [('/healthz','alive'),('/readyz','ready')]:
            started=time.monotonic()
            try:
                body=bytearray()
                with client.stream('GET',base+path) as response:
                    response.raise_for_status()
                    for chunk in response.iter_bytes():
                        if len(body)+len(chunk)>8192 or time.monotonic()-started>5:raise ValueError('Readiness response budget exceeded')
                        body.extend(chunk)
                value=json.loads(body)
                if not isinstance(value,dict) or value.get('status')!=status:raise ValueError('Unexpected readiness verdict')
                checks.append(dict(endpoint=path,status='PASS',elapsed_ms=round((time.monotonic()-started)*1000)))
            except (httpx.HTTPError,ValueError,TypeError):
                checks.append(dict(endpoint=path,status='FAIL',reason='Local readiness unavailable or invalid'))
    report=dict(status='PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL',captured_at=datetime.now(timezone.utc).isoformat(),
        checks=checks,scope='Observational local health/schema readiness; no fixture, credential, policy, model or source writes',certification=False)
    destination=ROOT/'evidence/implementation/readiness-current.json'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
