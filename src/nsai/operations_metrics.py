"""Finite, source-bound operational metrics and immutable local resource reservations."""
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .assembly import canonical_hash


def finite_decimal(value: str | int | Decimal) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)) or len(str(value)) > 64:
        raise ValueError('Invalid bounded decimal')
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValueError('Invalid decimal') from error
    if not parsed.is_finite() or abs(parsed.as_tuple().exponent) > 18 or len(parsed.as_tuple().digits) > 28:
        raise ValueError('Non-finite or excessive decimal')
    return parsed


@dataclass(frozen=True)
class MetricInput:
    value: Decimal
    source_sha256: str
    cohort: str
    grain: str
    version: str
    observed_at: datetime

    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            raise ValueError('Metric values must be finite Decimal instances')
        finite_decimal(self.value)
        if not self.cohort or not self.grain or not self.version or self.observed_at.tzinfo is None:
            raise ValueError('Metric lineage incomplete')
        if len(self.source_sha256) != 64 or any(c not in '0123456789abcdef' for c in self.source_sha256):
            raise ValueError('Metric source hash invalid')


def ratio(numerator: MetricInput, denominator: MetricInput, *, now: datetime, max_age_seconds: int = 86400) -> dict:
    if now.tzinfo is None or type(max_age_seconds) is not int or max_age_seconds <= 0:
        raise ValueError('Metric freshness contract invalid')
    for item in (numerator, denominator):
        age = (now - item.observed_at).total_seconds()
        if age < 0 or age > max_age_seconds:
            return {'state': 'unknown', 'value': None, 'reason': 'stale or future input'}
    if (numerator.cohort, numerator.grain, numerator.version) != (denominator.cohort, denominator.grain, denominator.version):
        return {'state': 'unknown', 'value': None, 'reason': 'incompatible cohort/grain/version'}
    if denominator.value <= 0 or numerator.value < 0:
        return {'state': 'unknown', 'value': None, 'reason': 'missing or invalid denominator/value'}
    value = numerator.value / denominator.value
    if not value.is_finite():
        raise ValueError('Metric computation is non-finite')
    receipt = {'cohort': numerator.cohort, 'grain': numerator.grain, 'version': numerator.version,
               'numerator': str(numerator.value), 'denominator': str(denominator.value),
               'source_sha256': [numerator.source_sha256, denominator.source_sha256], 'value': str(value)}
    return {'state': 'measured', 'value': str(value), 'lineage': receipt, 'receipt_sha256': canonical_hash(receipt),
            'causal_attribution': 'not_established'}


@dataclass(frozen=True)
class Reservation:
    id: str
    tokens: int
    expires_at: datetime
    state: str = 'reserved'
    charged_tokens: int = 0


@dataclass(frozen=True)
class ResourceLedger:
    token_limit: int
    attempt_limit: int
    reservations: tuple[Reservation, ...] = ()

    def __post_init__(self):
        if type(self.token_limit) is not int or type(self.attempt_limit) is not int or self.token_limit < 1 or self.attempt_limit < 1:
            raise ValueError('Invalid local resource limits')
        if len(self.reservations) > 4096 or len({r.id for r in self.reservations}) != len(self.reservations):
            raise ValueError('Invalid or excessive resource ledger')
        for row in self.reservations:
            if not row.id or type(row.tokens) is not int or row.tokens < 1 or row.expires_at.tzinfo is None:
                raise ValueError('Invalid resource reservation')
            if row.state not in {'reserved', 'succeeded', 'failed', 'abandoned'} or type(row.charged_tokens) is not int or not 0 <= row.charged_tokens <= row.tokens:
                raise ValueError('Invalid resource state/charge')
        if len(self.reservations) > self.attempt_limit or self.committed_tokens > self.token_limit:
            raise ValueError('Ledger exceeds resource budget')

    @property
    def committed_tokens(self):
        return sum(r.tokens if r.state == 'reserved' else r.charged_tokens for r in self.reservations)

    def reserve(self, *, id: str, tokens: int, expires_at: datetime, now: datetime) -> ResourceLedger:
        if not isinstance(id, str) or not id or len(id) > 128 or type(tokens) is not int or tokens < 1:
            raise ValueError('Reservation identity/token budget invalid')
        if now.tzinfo is None or expires_at.tzinfo is None or not now < expires_at:
            raise ValueError('Reservation expiry invalid')
        existing = next((r for r in self.reservations if r.id == id), None)
        if existing:
            if existing.tokens != tokens or existing.expires_at != expires_at:
                raise ValueError('Idempotency key payload mismatch')
            return self
        if len(self.reservations) >= min(self.attempt_limit, 4096) or self.committed_tokens + tokens > self.token_limit:
            raise ValueError('Local resource budget exhausted')
        return replace(self, reservations=self.reservations + (Reservation(id, tokens, expires_at),))

    def settle(self, *, id: str, actual_tokens: int, succeeded: bool) -> ResourceLedger:
        if type(actual_tokens) is not int or actual_tokens < 0 or type(succeeded) is not bool:
            raise ValueError('Invalid settlement')
        existing = next((r for r in self.reservations if r.id == id), None)
        if existing is None:
            raise ValueError('Unknown reservation')
        state = 'succeeded' if succeeded else 'failed'
        if existing.state != 'reserved':
            if existing.state == state and existing.charged_tokens == actual_tokens:
                return self
            raise ValueError('Terminal reservation cannot transition')
        if actual_tokens > existing.tokens:
            raise ValueError('Settlement exceeds reservation; provider must enforce token cap')
        settled = replace(existing, state=state, charged_tokens=actual_tokens)
        return replace(self, reservations=tuple(settled if r.id == id else r for r in self.reservations))

    def reconcile_expired(self, *, now: datetime) -> ResourceLedger:
        if now.tzinfo is None:
            raise ValueError('Timezone-aware ledger clock required')
        # Lost work is conservatively charged its full reservation, never silently made free.
        return replace(self, reservations=tuple(replace(r, state='abandoned', charged_tokens=r.tokens)
                       if r.state == 'reserved' and now >= r.expires_at else r for r in self.reservations))
