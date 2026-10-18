"""Data-only proposals and explicit local approval contracts; centralized security is inactive."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from .assembly import canonical_hash, strict_json


@dataclass(frozen=True)
class Proposal:
    id: str
    capability: str
    actor: str
    data_sha256: str
    state: str = 'proposed'


class ProposalRegistry:
    CAPABILITIES = frozenset({'alias-proposal', 'extraction-correction', 'assembly-plan', 'retention-dry-run', 'metric-definition'})
    AUTHORITY_FIELDS = frozenset({'code', 'execute', 'enabled', 'grant', 'role', 'permissions', 'secret', 'token', 'api_key'})

    @classmethod
    def propose(cls, *, capability: str, actor: str, data: dict[str, Any]) -> Proposal:
        if capability not in cls.CAPABILITIES or not actor or len(actor) > 128 or not isinstance(data, dict):
            raise ValueError('Unsupported proposal or actor')
        serialized = __import__('json').dumps(data, allow_nan=False, ensure_ascii=False)
        normalized = strict_json(serialized)
        def inspect(value):
            if isinstance(value, dict):
                if any(key.casefold() in cls.AUTHORITY_FIELDS or any(fragment in key.casefold() for fragment in ('password', 'credential', 'access_token', 'private_key')) for key in value):
                    raise ValueError('Proposal contains authority or executable fields')
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        inspect(normalized)
        digest = canonical_hash(normalized)
        return Proposal(canonical_hash({'capability': capability, 'actor': actor, 'data_sha256': digest}), capability, actor, digest)


@dataclass(frozen=True)
class PendingAction:
    id: str
    action: str
    requested_by: str
    payload_sha256: str
    policy_revision: int
    expires_at: datetime
    requires_step_up: bool = True

    def __post_init__(self):
        if not self.id or len(self.id) > 128 or not self.requested_by or len(self.requested_by) > 128:
            raise ValueError('Action identity invalid')
        if type(self.policy_revision) is not int or self.policy_revision < 1 or type(self.requires_step_up) is not bool:
            raise ValueError('Action policy contract invalid')
        if self.expires_at.tzinfo is None or len(self.payload_sha256) != 64 or any(c not in '0123456789abcdef' for c in self.payload_sha256):
            raise ValueError('Action payload/expiry invalid')


@dataclass(frozen=True)
class ApprovalProof:
    action_id: str
    actor: str
    policy_revision: int
    payload_sha256: str
    authenticated: bool
    step_up_verified: bool

    def __post_init__(self):
        if type(self.authenticated) is not bool or type(self.step_up_verified) is not bool:
            raise ValueError('Authentication/step-up must be typed verified decisions')
        if type(self.policy_revision) is not int or self.policy_revision < 1:
            raise ValueError('Approval policy revision invalid')
        if not self.actor or len(self.actor) > 128 or not self.action_id or len(self.action_id) > 128:
            raise ValueError('Approval actor/action invalid')
        if len(self.payload_sha256) != 64 or any(c not in '0123456789abcdef' for c in self.payload_sha256):
            raise ValueError('Approval payload hash invalid')


def decide_local_action(action: PendingAction, proof: ApprovalProof, *, now: datetime,
                        approved_actor: str, completed_action_ids: frozenset[str] = frozenset()) -> dict:
    """Caller derives proof from authentication, never from model/user natural-language assent."""
    if not isinstance(proof, ApprovalProof) or not isinstance(action, PendingAction):
        raise ValueError('Structured authenticated approval is required')
    if action.action not in {'extraction-correction', 'retention-dry-run', 'metric-definition'}:
        return {'allowed': False, 'reason': 'action is not commissioned'}
    if now.tzinfo is None or action.expires_at.tzinfo is None:
        raise ValueError('Timezone-aware action clocks required')
    if action.id in completed_action_ids:
        return {'allowed': False, 'reason': 'action already completed', 'idempotent': True}
    checks = [now < action.expires_at, proof.action_id == action.id, proof.actor == approved_actor,
              bool(proof.actor), proof.actor != action.requested_by,
              proof.policy_revision == action.policy_revision, proof.payload_sha256 == action.payload_sha256,
              proof.authenticated is True, not action.requires_step_up or proof.step_up_verified is True]
    if not all(checks):
        return {'allowed': False, 'reason': 'approval binding, independence, expiry or step-up failed'}
    receipt = dict(action_id=action.id, actor=proof.actor, policy_revision=action.policy_revision,
                   payload_sha256=action.payload_sha256, decided_at=now.astimezone(timezone.utc).isoformat())
    return {'allowed': True, 'receipt': receipt, 'receipt_sha256': canonical_hash(receipt)}


def staged_central_decision(*, requested_provider: str = '', **unused) -> dict:
    """Uniform fail-closed boundary; importing or configuring a provider cannot activate it."""
    return {'allowed': False, 'enabled': False, 'provider': requested_provider[:128],
            'reason': 'central security provider is staged and inactive'}
