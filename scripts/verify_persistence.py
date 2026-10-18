"""Project-scoped service restart proof; never removes volumes."""
from pathlib import Path
from datetime import datetime,timezone
import httpx
import json
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restart-project',action='store_true',help='Explicitly restart the configured project API and database; requires a quiet maintenance window')
    args=parser.parse_args()
    if not args.restart_project:
        parser.error('This check restarts services. Use the isolated stack qualification for routine validation, or explicitly select --restart-project during maintenance.')
    token=(ROOT/'secrets/api_token.txt').read_text().strip()
    headers={'Authorization':'Bearer '+token}
    client=httpx.Client(base_url='http://127.0.0.1:8787',timeout=10,trust_env=False)
    before=client.get('/v1/documents',headers=headers);before.raise_for_status()
    documents=before.json()['items'];assert documents
    claims_before=client.get('/v1/claims',headers=headers);claims_before.raise_for_status()
    claim_projection={(c['id'],c['status'],c['revision']) for c in claims_before.json()['items']}
    sessions=ROOT/'evidence/raw/live-system-current.json'
    session_id=None
    if sessions.exists():
        live=json.loads(sessions.read_text())
        chat=next((r.get('details',{}) for r in live.get('results',[]) if r['name']=='retrieval-to-cited-answer with conflict warning'),{})
        session_id=chat.get('session_id')
        if session_id:
            memory_before=client.get('/v1/memory/'+session_id,headers=headers);memory_before.raise_for_status()
            working_before=memory_before.json()['working']
    cmd=['docker','compose','-f','compose.yaml','-f','deploy/local/compose.cpu.yaml','restart','db','api']
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=120)
    assert result.returncode==0,'Service restart failed'
    for _ in range(30):
        try:
            if client.get('/readyz').status_code==200:break
        except httpx.HTTPError:pass
        time.sleep(1)
    else:raise RuntimeError('Readiness did not recover')
    after=client.get('/v1/documents',headers=headers);after.raise_for_status()
    assert {(d['id'],d['sha256']) for d in documents}=={(d['id'],d['sha256']) for d in after.json()['items']}
    claims_after=client.get('/v1/claims',headers=headers);claims_after.raise_for_status()
    assert claim_projection=={(c['id'],c['status'],c['revision']) for c in claims_after.json()['items']}
    if session_id:
        memory_after=client.get('/v1/memory/'+session_id,headers=headers);memory_after.raise_for_status()
        assert memory_after.json()['working']==working_before
    report=dict(status='PASS',captured_at=datetime.now(timezone.utc).isoformat(),documents_preserved=len(documents),
        claims_and_reviews_preserved=len(claim_projection),session_messages_preserved=bool(session_id),
        authenticated_api_recovered=True,volume_deletion=False,command=cmd)
    (ROOT/'evidence/raw/persistence.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
