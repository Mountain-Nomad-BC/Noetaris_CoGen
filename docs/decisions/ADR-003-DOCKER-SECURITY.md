# ADR-003: Docker as deployment isolation, not arbitrary-code containment

Status: Accepted, October 12 2026.

Decision: Use non-root/read-only/cap_drop/limited resources/private networks for normal application containers. Generated executable work will require a separate Linux confinement backend, denied network by default, immutable artifact admission and runtime tests. No Docker daemon socket in NSAI API/agents.

Rationale: Unix sockets can enable Docker API management even mounted read-only, and Windows Gremlin Job Object enforcement is not portable to Linux AMD infrastructure.
