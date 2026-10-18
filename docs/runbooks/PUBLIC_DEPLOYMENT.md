# Public deployment — explicit NOT-READY checklist

The included Compose stack is meant for local development. **It is not a publicly secure application as-is.** In particular, the browser uses a shared local API token, not OIDC; data has no tenant isolation, uploads are text-only, and logs/metrics are incomplete.

## Minimum target topology

- CDN/edge ingress and TLS (Vercel or equivalent) -> authenticated frontend -> backend API.
- Backend on private host/service network; API validates OIDC tokens and project-scoped roles. Never place service-role Supabase key in browser.
- Managed PostgreSQL/Supabase configured with separate DB roles, backups, migration strategy and RLS where applicable.
- AMD private vLLM endpoint separate from frontend; if partner requires cloud-to-cloud inference, dedicated secured TLS gateway.
- Worker queues have separate least-privilege identities. Generated execution service remains off until containment evidence exists.

## Required go/no-go gates

- [ ] IP release cleared for every source, image, training artifact and demo document.
- [ ] No source or tokens leaked in Git history, binaries, config or application responses.
- [ ] HTTPS only, CSP and CORS limited, rate limits and abuse controls.
- [ ] Identity/authorization tests for every claim/file/project endpoint.
- [ ] Data backups and tested recovery; migrations tested on staging snapshots.
- [ ] Dedicated worker timeouts, bounded file size and request volume, safe MIME parsing.
- [ ] No public Postgres or vLLM listening sockets.
- [ ] External endpoint auth: replay, expired tokens, malformed claims and role privilege tested.
- [ ] Container provenance pinned digests, SBOM, dependency/container scans reviewed.
- [ ] Monitoring, host firewall, outage response, secret rotation and cost threshold documented.
- [ ] Golden evaluations with unsupported-answer rates and real AMD traces saved.
- [ ] Public access tested through actual URL, not only localhost.

If these are not complete, demonstrate behind a controlled private ingress or a local screen recording rather than exposing local shared-token mode publicly.

## Rollback protocol

1. Stop public ingress and revoke compromised tokens first if necessary.
2. Switch read operations to prior stable deployment/index generation; **do not overwrite canonical evidence**.
3. Preserve failed deployment image digest, logs and DB snapshot for forensic review.
4. Restore database only from a verified backup with explicit migrations / RPO expectations.
5. Validate user/project permissions and end-to-end citations before re-enabling public traffic.
6. Document incident and update versioned release ledger.
