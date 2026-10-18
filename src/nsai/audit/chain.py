"""Tamper-evident digest-chain helper for local event traces.

It is not a secure audit ledger by itself: privileged DB writers could rewrite
all rows unless hashes are anchored/signed outside the DB and append-only
permissions are enforced.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from nsai.contracts.evidence import canonical_hash

class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_id: str = Field(min_length=8)
    kind: str = Field(min_length=3)
    actor: str = Field(min_length=3)
    subject_id: str = Field(min_length=3)
    happened_at: datetime
    previous_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    details: dict[str, str] = Field(default_factory=dict)

    def digest(self) -> str:
        return canonical_hash(self)
