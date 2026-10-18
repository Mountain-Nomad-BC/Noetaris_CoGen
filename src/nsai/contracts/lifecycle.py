"""Index, proposed skill and authorization-envelope contracts.

An AuthorityDecision record is a data shape ONLY. It does not validate
signatures or confer authority. Promotion endpoints must remain disabled until
independent verification, separate roles and durable audit are implemented.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class IndexGeneration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1.0"
    generation_id: str = Field(min_length=8, max_length=128)
    source_set_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    embedder_identity: str = Field(min_length=1, max_length=250)
    index_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    tested: bool = False
    activated: bool = False

    @field_validator("activated")
    @classmethod
    def activation_requires_test(cls, value: bool, info):
        if value and not info.data.get("tested"):
            raise ValueError("index may not be marked activated without test status")
        return value


class SkillProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    proposal_id: str = Field(min_length=8, max_length=128)
    description: str = Field(min_length=1, max_length=1000)
    inputs_schema_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    code_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    required_capabilities: list[str] = Field(default_factory=list, max_length=20)
    execution_enabled: bool = False

    @field_validator("execution_enabled")
    @classmethod
    def proposals_cannot_execute(cls, value: bool) -> bool:
        if value:
            raise ValueError("skill proposals cannot enable execution")
        return False


class Decision(str, Enum):
    APPROVE = "approve"
    DENY = "deny"


class AuthorityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision_id: str = Field(min_length=8, max_length=128)
    subject_id: str = Field(min_length=8, max_length=128)
    actor_id: str = Field(min_length=3, max_length=128)
    decision: Decision
    reason: str = Field(min_length=1, max_length=1000)
    recorded_at: datetime
    signature: str | None = None  # not verified by this type

    @field_validator("recorded_at")
    @classmethod
    def require_timezone(cls, value: datetime):
        if value.utcoffset() is None:
            raise ValueError("recorded_at must be timezone-aware")
        return value
