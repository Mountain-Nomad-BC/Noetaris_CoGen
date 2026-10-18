# Pitch and slide outline

NSAI turns changing supplier documents into inspectable evidence. When two revisions disagree,
it preserves both source statements, exposes their provenance, and lets an independent reviewer
make an explicit decision. Local AI helps explain the retrieved material without authorizing itself.

1. **Problem:** a fictitious Pump-X supplier changes its temperature limit from 85 C to 75 C.
   A confident answer from the wrong revision is a poor operational decision.
2. **Evidence path:** bounded TXT/MD/PDF ingestion → original bytes/hash → page/line spans → indexed
   chunks → retrieved source citations. Show a real ingestion receipt and source inspector.
3. **Human review:** competing claims remain candidates until a separate reviewer checks the source,
   supplies a rationale and reviews the current revision. Older alternatives stay available.
4. **Memory and learning:** scoped working conversation, hypotheses, reviewed canon and reflections;
   selected PX query plans and Remy source manifests are real bounded integrations. Learning proposes,
   it does not self-promote, execute code or train weights.
5. **Deployment and governance:** private Docker topology, separate restricted parser, least-privilege
   app DB role, enforced local RBAC, inference budgets/kill switch, append-only audit. Central integration
   is staged and disabled. Testing & evidence is a distinct UI section.
6. **Measured results and next gate:** use current `assets/verification.json` and `evidence/raw` for test
   counts and actual CPU model timing. AMD ROCm adapter/deployment is prepared; actual GPU evidence
   remains PENDING. Do not describe this CPU demonstration as an AMD-qualified final submission.

Video storyboard: open library → ingest revisions/PDF → ask a question → click citations → inspect
conflict → show independent reviewer controls → inspect memory → show policy boundaries → show
the separate evidence view and explicit AMD pending status. Keep credentials and company sources off screen.
Browser screenshots are authentic local demo artifacts. Any generated silent walkthrough is a draft
recording, not a narrated final submission video.
