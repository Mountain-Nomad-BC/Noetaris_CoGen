"""NSAI projection adapter for PX scope, quarantine and bounded-context contracts.

Persistent records are never changed by materialization; new contradictions quarantine context.
"""
import json
import re
from .contracts.evidence import canonical_hash

def materialize_projection(working,canon,reflection,hypotheses,*,max_bytes=16384):
    if type(max_bytes) is not int or not 1024<=max_bytes<=16384:
        raise ValueError('Memory byte budget must be between 1024 and 16384')
    conflicts={(g['subject'],g['predicate']) for g in hypotheses}
    quarantined=[]
    reviewed=[]
    for record in canon[:12]:
        if (record['subject'],record['predicate']) in conflicts:
            reason='unresolved_source_conflict'
        elif not record.get('reviewed_by') or not record.get('locator') or not re.fullmatch(r'[a-f0-9]{64}',record.get('original_sha256') or ''):
            reason='missing_review_or_provenance'
        else:
            reviewed.append(record);continue
        quarantined.append(dict(claim_id=record['id'],reason=reason))
    content=dict(working=[],canon=[],reflection=[],hypotheses=[])
    omitted=dict(working=max(0,len(working)-8),canon=max(0,len(canon)-12),
        reflection=max(0,len(reflection)-8),hypotheses=max(0,len(hypotheses)-12))
    candidates=dict(canon=reviewed,hypotheses=hypotheses[:12],working=list(reversed(working[-8:])),
        reflection=[r for r in reflection[:8] if r['state']!='rejected'])
    omitted['reflection']+=sum(r['state']=='rejected' for r in reflection[:8])
    def envelope():
        return dict(**content,quarantined=quarantined,omitted=omitted,serialized_bytes=0,
            max_bytes=max_bytes,eligible=not quarantined,writeback_policy='proposal_only',receipt_sha256='0'*64)
    def size():
        value=envelope()
        measured=0
        # Include the decimal length field itself and the fixed-width receipt.
        for _ in range(8):
            value['serialized_bytes']=measured
            actual=len(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())
            if actual==measured:return actual
            measured=actual
        raise ValueError('Memory byte accounting did not converge')
    # Preserve authoritative provenance first; add whole records/messages within the shared bound.
    for name,records in candidates.items():
        for record in records:
            content[name].append(record)
            if size()>max_bytes:
                content[name].pop();omitted[name]+=1
    content['working'].reverse()
    # Metadata is part of the same transport budget, including quarantine and receipt.
    if size()>max_bytes:
        raise ValueError('Memory metadata exceeds byte budget')
    body=dict(**content,quarantined=quarantined,omitted=omitted,serialized_bytes=size(),
        max_bytes=max_bytes,eligible=not quarantined,writeback_policy='proposal_only')
    return dict(**body,receipt_sha256=canonical_hash(body))
