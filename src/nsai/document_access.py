"""Private-first authorization decisions over trusted server-side policy snapshots.

This pure policy is not a database enforcement adapter. Callers must resolve
complete provenance, load current grants/memberships, and audit privileged reads
before releasing bytes. Unknown provenance denies rather than broadens access.
"""
from dataclasses import dataclass

READ_ACTIONS=frozenset({'read','query','derive'})
OWNER_ACTIONS=READ_ACTIONS|{'manage','share','revoke'}


@dataclass(frozen=True)
class Grant:
    subject_kind: str
    subject_id: str
    actions: frozenset[str]
    expires_at: int | None = None
    revoked: bool = False


@dataclass(frozen=True)
class SourcePolicy:
    document_id: str
    owner: str
    epoch: int
    grants: tuple[Grant, ...] = ()


@dataclass(frozen=True)
class Decision:
    allowed: bool
    audit_required: bool
    reason: str


def source_decision(policy, actor, role, action, *, groups=frozenset(), now):
    """No role, including admin or learning agent, bypasses a source grant.

    `groups` is a trusted membership snapshot, never request-supplied metadata.
    Only owners manage/share/revoke. Explicit reader grants cannot delegate.
    """
    if (not actor or action not in OWNER_ACTIONS or type(now) is not int
            or not isinstance(policy, SourcePolicy) or not policy.owner
            or type(policy.epoch) is not int or policy.epoch < 1):
        return Decision(False,False,'invalid-policy-or-request')
    if actor == policy.owner:
        return Decision(True,role=='admin','owner')
    if action not in READ_ACTIONS:
        return Decision(False,False,'owner-required')
    for grant in policy.grants:
        if not isinstance(grant,Grant) or grant.revoked:
            continue
        if grant.expires_at is not None and (type(grant.expires_at) is not int or grant.expires_at <= now):
            continue
        matches=(grant.subject_kind=='user' and grant.subject_id==actor) or (
            grant.subject_kind=='group' and grant.subject_id in groups)
        # A read grant admits querying/derivation of that same source, not sharing.
        if matches and 'read' in grant.actions:
            return Decision(True,role=='admin','explicit-share')
    return Decision(False,False,'not-shared')


def derived_decision(source_ids, policies, actor, role, action, *, groups=frozenset(), now,
                     provenance_complete=False):
    """An edge, cached answer or memory requires every contributing source.

    Filtering an edge's private endpoint after exposing its label is too late.
    The caller must evaluate this decision before serialization or generation.
    """
    if (provenance_complete is not True or not isinstance(source_ids,(tuple,list,frozenset,set))
            or not source_ids or len(source_ids)>1000 or action not in READ_ACTIONS):
        return Decision(False,False,'incomplete-provenance')
    privileged=False
    for document_id in source_ids:
        policy=policies.get(document_id)
        if policy is None or policy.document_id != document_id:
            return Decision(False,False,'unresolved-source')
        decision=source_decision(policy,actor,role,action,groups=groups,now=now)
        if not decision.allowed:
            return Decision(False,False,'source-denied')
        privileged |= decision.audit_required
    return Decision(True,privileged,'all-sources-authorized')


def cache_scope(policies, source_ids, actor, *, membership_epoch):
    """Internal cache identity; reauthorization is still required on each read."""
    if not actor or type(membership_epoch) is not int or membership_epoch<1 or not source_ids:
        raise ValueError('Cache scope requires current actor, membership and provenance')
    revisions=[]
    for source in sorted(set(source_ids)):
        policy=policies[source]
        if policy.document_id!=source or type(policy.epoch) is not int or policy.epoch<1:
            raise ValueError('Invalid source policy epoch')
        revisions.append((source,policy.epoch))
    return actor,membership_epoch,tuple(revisions)
