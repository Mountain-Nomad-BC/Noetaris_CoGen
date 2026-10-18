# Privacy operations and release review

Status: working implementation/operations dossier, not a GDPR certificate or legal opinion. Public personal-data admission remains denied. Owner confirmed an independent US project operated under Mountain Nomad BC, a public noncommercial experimental hackathon demonstration for adults 18+, with no invitations. Public privacy/support contact, any required legal identity/address details, processing regions, legal bases and retention decisions remain unresolved. Sensitive/proprietary/personal uploads are prohibited and only publicly available authorized documents are eligible. Public Terms and Privacy are explicitly drafts until those decisions are complete.

## Processing inventory / Article 30 starting record

| Activity | Data and source | Purpose | Basis/retention decision | Recipients and current status |
| --- | --- | --- | --- | --- |
| Authentication | Internal actor identifier, provider and stable subject, session hash/expiry, security events | Account recognition and access control | Controller to approve necessary account-processing basis and session/security retention | Existing NSAI database; Google/GitHub tokens transient; real provider commissioning pending |
| Source ingestion | Authorized original files, text, metadata, checksums | User-requested storage, indexing and retrieval | Verify user authority, purpose and rights; approve retention/deletion including backups | Current local PostgreSQL custody; R2 application offload not yet implemented |
| Semantic indexing | Passages, embeddings, graph and claim records | Source search and navigation | Same documented compatible purpose; embeddings may still be personal data | Local MiniLM and database; no anonymity claim |
| AI generation | Questions, selected passages, answers, source references and usage events | Requested research assistance | Approve basis, content eligibility and export before hosted use | Local CPU workflow; AMD/OpenRouter hosted dispatch unfinished; no assumed provider non-training promise |
| Audit/security | Bounded operational/security metadata and review events | Security, traceability, abuse response | Assess legitimate interests or other applicable basis; justify event fields, access and retention | Restricted server/database; no raw provider secrets in logs |
| Static delivery | Network requests and infrastructure logs | Deliver website | Confirm actual hosting logs, duration, terms and geographic processing | Firebase intended, not publicly deployed |

This is a starting record. Complete actual controller/processor roles, categories of data subjects, transfer destinations/safeguards, deletion time limits and technical/organizational measures for the real deployment. A UUID is pseudonymous where linkable, not necessarily anonymous.

## Processor and transfer register

Record provider legal entity, service, role, region/subprocessors, signed data-processing terms where required, security measures, retention/training policies and transfer mechanism before activation. Intended vendors: Google/Firebase, OCI, Cloudflare R2, AMD hosted inference, OpenRouter and actual downstream inference providers; Evolus optional and NOT_CONFIGURED, Neon optional and undeployed. Do not treat an OpenRouter route as disclosure to only one entity. Do not claim EU residency, adequacy, SCC execution or no-training without verified contracts/configuration.

## Rights request procedure

1. Commission a monitored private contact. Log receipt, scope, deadline and owner without unnecessarily copying request content.
2. Confirm identity proportionately using existing account/session channels where possible; do not solicit identity documents in public issues or AI prompts.
3. Determine applicable rights and legal conditions: access, correction, erasure, restriction, portability, objection, consent withdrawal and applicable automated-decision safeguards.
4. Search by the canonical identity across originals, semantic derivatives, source dependencies, conversation histories, review/audit records and commissioned providers. Provide data through an authenticated channel; never expose another user or protected third party.
5. Complete within the applicable Article 12 deadline, normally one month; assess any lawful extension and notify reasons within the initial period. Record lawful refusals/exceptions and complaint rights.
6. Verify execution and downstream propagation. Revocation from retrieval is not full erasure. Record backup expiry and exceptional audit/legal retention; prevent deleted records being silently resurrected after restore.

Implementation gap: a complete self-service export/erasure pipeline, production request channel, cross-provider deletion workflow and measured retention jobs are not yet qualified. A written procedure does not implement them.

## Retention decision register

Approve specific periods or documented criteria for provider bindings, active/revoked sessions, source originals/derivatives, conversations, audit/security logs and backups. Verified current `retention_dry_run` reports delete_enabled=false, automatic_cleanup=false and holds for all originals/audit events. OAuth browser sessions default to 12 hours within an allowed 1-24-hour configuration; expiry does not erase the row. Owner-held backups have no qualified expiry. No invented universal retention period is adopted here. Define scheduled disposal, legal holds, backup restore suppression and test receipts. Update the public notice when these decisions are approved.

## Incident response

Restrict exposure, preserve proportionate evidence, rotate compromised credentials as authorized, assess individuals' risk and document facts, impact and remediation. Where GDPR applies, assess supervisory-authority notification under Article 33 (without undue delay and, where feasible, within 72 hours after awareness unless the risk exception applies), and affected-person notice under Article 34 where required. Establish the controller's actual on-call contacts and processor escalation process before launch. Do not assert notification solely because a scanner found a vulnerability; assess an actual personal-data breach.

## DPIA and AI assessment

Screen whether processing is likely to result in high risk, and whether special categories, children, systematic monitoring or consequential automated decisions are involved. Complete a DPIA where required and consult the authority where required for unresolved high risk. The preview does not authorize those use cases. Record AI Act role/classification, interaction disclosures, output labeling, provider machine-readable provenance/marking obligations and any applicable exceptions. A banner or liability waiver does not replace these duties.

## Security and release acceptance

Required: canonical identity/ACL acceptance, RLS/grants contract, encrypted verified transport, host/secret-manager custody, safe session/CSRF, limited logs, known-vulnerability remediation, least-privilege provider access, immutable source digests, bounded storage/request allowances, tested revocation/deletion/backup recovery and independently verified operations. Current independent release DENY remains binding. Terms acceptance is not source-export authorization and is not GDPR consent for every processing purpose.

## Authoritative references reviewed October 17, 2026

- GDPR text: https://eur-lex.europa.eu/eli/reg/2016/679/oj (Articles 5, 6, 9, 12?22, 28, 30, 32?35, 44?49).
- European Commission individual rights: https://commission.europa.eu/law/law-topic/data-protection/information-individuals_en
- Commission business guidance: https://europa.eu/youreurope/business/governance-and-sustainability/digital-and-data-compliance/data-protection-gdpr/index_en.htm
- AI Act Article 50: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50
- Current Commission transparency guidance: https://digital-strategy.ec.europa.eu/en/policies/guidelines-ai-transparency-obligations

Applicability, effective provisions, jurisdiction-specific consumer/contract limits and actual processor terms require review for the final service. No generic claim that every AI response is a GDPR automated decision is made.
