"""Original legacy compatibility contract; no reference runtime implementation."""
from dataclasses import dataclass,asdict
import math
from ..contracts.evidence import canonical_hash

@dataclass(frozen=True)
class MemoryQueryPlan:
    project_id:str
    subject_id:str
    actor_id:str
    agent_id:str
    binding_ids:tuple
    memory_classes:tuple
    tiers:tuple
    max_items:int
    max_bytes:int
    max_tokens:int
    trust_floor:float
    max_age_seconds:int
    conflict_policy:str
    provenance_required:bool
    writeback_policy:str
    source_revision:str
    dependency_revisions:tuple
    schema_version:str='nsai.legacy-memory-interface/1'
    def as_dict(self):
        body=asdict(self)
        body['plan_sha256']=canonical_hash(body)
        body['plan_id']=body['plan_sha256'][:32]
        return body

def validate_memory_query_plan(plan,*,current_source_revision=None,**unused):
    errors=[]
    for name,maximum in [('max_items',100),('max_bytes',16384),('max_tokens',4096),('max_age_seconds',86400)]:
        value=getattr(plan,name,None)
        if type(value) is not int or not 1<=value<=maximum:errors.append(name)
    if plan.writeback_policy!='proposal_only':errors.append('writeback_policy')
    if plan.conflict_policy!='quarantine' or plan.provenance_required is not True:errors.append('provenance/conflict')
    if not isinstance(plan.trust_floor,(int,float)) or not math.isfinite(plan.trust_floor) or not 0<=plan.trust_floor<=1:errors.append('trust_floor')
    if current_source_revision is not None and current_source_revision!=plan.source_revision:errors.append('stale source revision')
    return dict(valid=not errors,reasons=errors,authority_granted=False)

def build_memory_query_plan(**fields):
    for name in ['binding_ids','memory_classes','tiers']:fields[name]=tuple(fields[name])
    fields['dependency_revisions']=tuple(sorted(fields['dependency_revisions'].items()))
    plan=MemoryQueryPlan(**fields)
    if not validate_memory_query_plan(plan)['valid']:raise ValueError('Invalid legacy plan')
    return plan
