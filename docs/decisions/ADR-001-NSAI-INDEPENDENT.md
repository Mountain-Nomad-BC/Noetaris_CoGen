# ADR-001: NSAI independent architecture, selective ideas from Remy/PX

Status: Accepted for hackathon prototype, October 12 2026.

Context: Remy contains useful interaction and TurnBurn ingestion patterns but proprietary root licensing; PX has powerful knowledge, memory and safety semantics but tightly coupled runtime and Windows-specific enforcement. Full direct inheritance would create deadline and IP risk.

Decision: Original NSAI standalone source; Remy design/reference only; optional cleanly attributed per-file PX adaptation after closure/notice validation. Typed, versioned interfaces. Demo prioritizes provenance/contradictions/AMD and real business need.

Consequences: Some sophisticated PX/Remy capabilities must be independently reimplemented or deferred; fewer hidden dependencies and cleaner public publication boundary.
