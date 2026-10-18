from contextlib import contextmanager
import json
from types import SimpleNamespace
from nsai import workflow_store as workflow,store,provenance_manifests


def test_thousand_source_lineage_keeps_exact_complete_memory_transport_bound(monkeypatch):
    sources=[f'{number:032x}' for number in range(1000)];registered=[]
    monkeypatch.setattr(workflow,'session',lambda *a:None)
    monkeypatch.setattr(workflow,'memory_claims',lambda *a,**kw:[])
    monkeypatch.setattr(store,'request_source_dependencies',lambda:sources)
    class Connection:
        def execute(self,*a):return SimpleNamespace(description=[],fetchall=lambda:[])
    @contextmanager
    def connect():yield Connection()
    monkeypatch.setattr(store,'connect',connect)
    monkeypatch.setattr(provenance_manifests,'register',lambda value:registered.append(value) or 'a'*32)
    result=workflow.memory_context('local-operator','session')
    assert registered==[sources] and result['source_dependency_count']==1000
    assert result['source_manifest_id']=='a'*32 and 'source_dependencies' not in result
    assert result['provenance_complete'] is True
    assert result['envelope_bytes']==len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode())
    assert result['envelope_bytes']<=result['envelope_max_bytes']==16384
