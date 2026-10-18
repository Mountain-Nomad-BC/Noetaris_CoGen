# Submission copy — editable text and storyboard

## Name
NSAI — Evidence-Governed Autonomous Knowledge Operations

## Short description
A source-aware AI knowledge system that detects conflicting information, preserves revision history, and uses AMD-hosted open models to propose verifiable business actions.

## Long description
Businesses accumulate changing manuals, supplier specifications, process documents, and operating records. Conventional retrieval can surface a document but cannot reliably distinguish revised specifications, conflicting assertions, or unverified conclusions. NSAI ingests documents with source fingerprints and locators, extracts candidate knowledge, identifies contradictions, and preserves the provenance of every claim. An AMD ROCm/vLLM-served open model helps users reason over bounded evidence while independent policy controls prevent model output from silently becoming canonical truth. NSAI is designed to evolve via evaluated hypotheses, candidate retrieval indexes and human-reviewed improvements; those advanced capabilities are included in the demonstration only to the extent actually implemented and tested. [Remove the preceding qualification when authoring the final pitch; replace with actual implemented/verified capabilities.]

## Primary user
Operations engineer or supply-chain analyst managing evolving supplier/product specifications.

## Business outcome to measure
Time required to locate a contradictory specification and return source-backed evidence; number and proportion of conflicts detected in a fixed test set; supported-answer and citation-match rates.

## Proposed tech tags
AMD, ROCm, vLLM, Open Models, Python, FastAPI, Docker, PostgreSQL, Retrieval, Evidence Provenance, AI Agents.

## Suggested pitch slides
1. Problem and cost of stale/conflicting knowledge.
2. One real end-to-end user journey.
3. NSAI architecture with explicit trust boundaries.
4. Live AMD inference and measured tests.
5. Business value and what remains for production.

**Publication note:** update copy from the final capability matrix and raw metrics; do not publish claims for not-yet-built parts.
