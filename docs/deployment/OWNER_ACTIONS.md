# Owner actions before publication

Selected target: Firebase static frontend, OCI ARM64 API/PostgreSQL, protected AMD ROCm/vLLM. Google project selection and Firebase API enablement are complete; no app has been published, no host has been provisioned and no production database migration has been performed.

| Input or action | Required details |
| --- | --- |
| Firebase | Owner selected `noetaris`; Google CLI account/project access succeeds. Firebase Management/Hosting APIs were enabled. Current project/Hosting discovery returns404 NOT_FOUND because the Google project is not yet initialized as a Firebase project/site. Earlier403 observations are historical; see `state/google-deployment/firebase-apis-enabled-check.json`. Confirm site and owned app/API domains before publication. |
| Domains | Supply an owned site with `https://app.<site>` and `https://api.<site>`, TLS certificates and approved DNS. Arbitrary web.app/OCI cross-site origins are rejected. |
| OCI | Confirm tenancy, compartment, region, A1 capacity/quota, host access and free/credit-only budget. Provisioning requires approval. |
| Identity | Register Google and GitHub OAuth apps. Exact API callbacks are `/auth/google/callback` and `/auth/github/callback`. Inject client secrets and session key server-side only. Both real provider flows require browser acceptance. |
| External storage / fallback | Neon is optional fallback per the latest owner clarification, not a replacement database/identity authority. Cloudflare is intended for documents and extracted images; confirm whether these are R2 buckets, exact names, endpoint/account and server-side credential file. The pasted token permissions summary alone is not a usable S3 credential. PostgreSQL remains authoritative. |
| AMD | Confirm authenticated serving endpoint, Gemma artifact/tokenizer, ROCm/vLLM image, hardware, quota and accounting/export policy. Existing synthetic API success is insufficient. |
| Evolus (optional) | Missing verified API base/workspace URL, application ID, workflow ID, agent ID, extractor ID and payload-schema hash. Keep NOT_CONFIGURED/OFF. A key alone is insufficient; no verified bindings were found. |
| Acceptance | Independent security, rights/licensing, identity/ACL and private-content acceptance for the exact candidate. Current release verdict is DENY. |

Do not paste credentials into chat. Use restricted server-side files and the supplied secret mounts. No Firebase Auth authority is added. Public publishing, production data transfer, spending and DNS changes need owner approval after review of the exact candidate.
