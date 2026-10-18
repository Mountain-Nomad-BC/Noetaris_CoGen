# Demo script and submission playbook

## One sentence pitch

**NSAI is an evidence-governed autonomous knowledge operations system that ingests changing information, exposes contradictions and source history, and proposes safe next steps using an open model on AMD GPUs.**

## Demo sequence (3–5 minute recording target, adjust to organizer limits)

1. **Problem (20 s):** changing supplier manuals and purchasing specs create conflicting operational knowledge.
2. **Upload (30 s):** load entirely fictional supplier revision A, revision B and order record; show hashes and version metadata.
3. **Conflict (35 s):** real candidate extraction creates two incompatible limits with precise source locators, neither auto-verified.
4. **Explain (40 s):** ask a question; show sourced answer and explicit uncertainty. Model runs on AMD-hosted vLLM; show actual provider/model/usage trace.
5. **Governance (40 s):** show blocked auto-promotion, separate human review and historical evidence. Only show working approval controls if actually implemented.
6. **Action (40 s):** optionally execute real Evolus document/workflow path and display resulting trace. If optional partner not ready, show an NSAI-generated non-executable review plan.
7. **Metrics (30 s):** measured citation match, contradiction precision/recall, p50/p95 latency, cost per validated doc when available. Compare against baseline only if both measured under same workload.
8. **Architecture + next steps (20 s):** independent NSAI code + carefully selected source inspiration; Docker controls and planned sandbox separation.

## Minimum submission assets

- Project title + short/long description (see `SUBMISSION_COPY.md`).
- Public repository with MIT-compatible own code, Docker files, executable README, clearly described known limitations.
- Hosted demo URL if safe public deployment complete, otherwise follow exact event requirements and controlled live demo strategy (do not invent hosted URL).
- Video, cover image, slide deck, measured screenshot(s) and tech tags.
- Event dashboard exact closing time verified and documented; page confirms event Oct 12–18, not clear exact submission hour in inspected text.
- Evidence of **real AMD usage**: instance/GPU, model, trace, benchmark and inference calls.
- Evolus partner proof only if fully configured and active.

## Demo failure contingencies

- AMD network error: show error clearly; never label a local or replay model response "AMD". Keep earlier capture of successful live AMD run as evidence.
- Candidate conflict detection unexpectedly fails: use fixture reproducibility tests to debug, do not edit data after capture.
- Public endpoint not safely exposed: present a screen recording and docs rather than exposing unsafe local shared-token mode.
- Budget running low: record model trace, shut idle instance, allocate final live window after rehearsal.

## Measurement claim policy

A metric claim must link to raw case results and the exact code/model/run config. Don't claim accelerated by 80% or 100% hallucination prevention without a measured controlled comparison. See `docs/validation/METRIC_DEFINITIONS.md`.
