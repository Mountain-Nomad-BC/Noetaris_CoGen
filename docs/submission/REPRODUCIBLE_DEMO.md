# Reproducible demonstration

**Blocked — this procedure is not currently reproducible.** As of 2026-10-17 11:48 EDT, no Docker service has a host-published port, authentication is unavailable, and release admission is **DENY**. Do not start the existing persistent stack or run evidence-writing acceptance scripts. This scenario is a historical synthetic workflow, not a current pass or deployment claim. See [deployment state](../implementation/DEPLOYMENT_STATE.md) and [Start here](../../START_HERE.md).

Use the local deployment instructions in `docs/LOCAL_DEPLOYMENT.md`. Open `http://127.0.0.1:8787`.
Connect with the operator token in `secrets/api_token.txt`; do not show credentials in recordings.

1. Open Document library and choose Load synthetic demo. Revision 1 states 85 C and revision 2 states
   75 C for the fictitious Pump-X maximum operating temperature. Repeating the action deduplicates sources.
2. Generate the synthetic PDF with `.venv/Scripts/python.exe evaluations/synthetic_pdf.py`, then upload
   it with revision 2. Inspect ingestion receipts and preserved source hashes. PDF locators identify page/line.
3. Ask “What is the Pump-X maximum operating temperature?” Review evidence displays the source conflict.
   Ask connected AI runs the real local model, records provider/model/latency, and validates cited IDs.
4. Click a citation to inspect its exact original hash, revision and source span. Download original source
   to verify byte preservation. Citation ID checks do not establish semantic truth; answers stay unverified.
5. Open Memory & learning. Inspect scoped working messages, alternative hypotheses and the PX plan.
   Reflect on source conflicts creates bounded, deduplicated proposals without changing canonical claims.
6. Disconnect and connect using `secrets/reviewer_token.txt`. In Knowledge review, write a rationale and
   prefer revision 2. Older alternatives remain preserved as superseded claims. Stale reviews are rejected.
   Review a learning proposal; this marks the reflection reviewed and grants no execution authority.
7. Reconnect as operator and inspect memory. The human-reviewed claim appears in the separate canon
   projection; conversation and reflections remain distinct. A source-specific follow-up can use prior session context.
8. Connect as admin using `secrets/admin_token.txt`. Inspect policy, limits and audit verification.
   Disable local inference to demonstrate the enforced kill switch, then restore it. Central configuration
   may be staged but remains disabled; activation attempts fail closed.
9. Open Testing & evidence. Show the current automated/runtime results and AMD pending status separately
   from deployment instructions. Use `evidence/raw` and the submission documents for detailed inspection.

Automated reproduction: `.venv/Scripts/python.exe scripts/verify_system.py --model`, then
`.venv/Scripts/python.exe scripts/verify_persistence.py`. Browser reproduction:
`.venv/Scripts/python.exe scripts/verify_browser.py` after installing Playwright Chromium.
Acceptance writes fictitious proof documents with unique identities; it never removes existing evidence.
