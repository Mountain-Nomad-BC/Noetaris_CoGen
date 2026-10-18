"""Independently specified local query-plan envelope; no execution authority."""
from dataclasses import dataclass, replace
from .evidence import canonical_hash

@dataclass(frozen=True)
class LocalMemoryPlan:
    payload:dict
    def as_dict(self):return dict(self.payload)

def build_memory_query_plan(**fields):
    required={'project_id','subject_id','actor_id','agent_id','binding_ids','memory_classes','tiers',
        'max_items','max_bytes','max_tokens','trust_floor','max_age_seconds','conflict_policy',
        'provenance_required','writeback_policy','source_revision','dependency_revisions'}
    if set(fields)!=required:raise ValueError('Incomplete local memory contract')
    if fields['writeback_policy']!='proposal_only' or fields['conflict_policy']!='quarantine' or fields['provenance_required'] is not True:
        raise ValueError('Local memory cannot import authority')
    for name,limit in [('max_items',100),('max_bytes',16384),('max_tokens',4096),('max_age_seconds',86400)]:
        if type(fields[name]) is not int or not 1<=fields[name]<=limit:raise ValueError('Invalid memory bound')
    body=dict(schema_version='nsai.memory-query-plan/1',**fields)
    body['plan_sha256']=canonical_hash(body)
    body['plan_id']=body['plan_sha256'][:32]
    return LocalMemoryPlan(body)
