"""Strict, source-carrying evidence exchange objects.

These *proposed* objects are intentionally separate from starter SQL tables.
Persist only after introducing a versioned migration and adapter (TASK DATA-03).
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClaimState(str, Enum):
    CANDIDATE = "candidate"
    CONTESTED = "contested"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


def canonical_hash(payload: BaseModel | dict) -> str:
    """Canonical JSON digest. Not a digital signature or authority receipt."""
    data = payload.model_dump(mode="json", exclude_none=True) if isinstance(payload, BaseModel) else payload
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class EvidenceSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_id: str = Field(min_length=8, max_length=128)
    revision: str = Field(min_length=1, max_length=80)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    locator: str = Field(min_length=1, max_length=500)
    media_type: str = Field(min_length=3, max_length=120)


class CandidateClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1.0"
    claim_id: str = Field(min_length=8, max_length=128)
    subject: str = Field(min_length=1, max_length=250)
    predicate: str = Field(min_length=1, max_length=250)
    value: str = Field(min_length=1, max_length=2000)
    source: EvidenceSource
    state: ClaimState = ClaimState.CANDIDATE
    observed_at: datetime
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)

    @field_validator("observed_at", "valid_from", "valid_until")
    @classmethod
    def aware_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("timestamps must have explicit timezones")
        return value

    @field_validator("schema_version")
    @classmethod
    def v1_only(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported schema version")
        return value
