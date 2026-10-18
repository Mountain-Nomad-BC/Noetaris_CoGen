# Optional local identity registry

This staged authentication interface is not a completed multiuser deployment. Authentication does not enforce source authorization. Distinct users must not gain document access until the source-policy adapter enforces uploader-private defaults, explicit user/group shares and audited explicit administrator grants. Administrator role alone must not bypass source policy. The API integration must fail closed for local-user content requests until that enforcement exists. No registry or credentials have been provisioned by this change.

`NSAI_LOCAL_IDENTITIES_FILE` optionally points to an absolute, operator-controlled JSON file, re-read on each authentication attempt. The file contains no bearer values:

```json
{
  "schema_version": "nsai.local-identities/1",
  "identities": [
    {
      "actor": "local-user-alice",
      "role": "operator",
      "token_file": "/run/secrets/alice_token"
    }
  ]
}
```

The registry is limited to 64 KiB and 1–1,000 entries. Actor IDs use `local-user-` followed by a lowercase letter and up to 63 lowercase letters, digits, underscores or hyphens. Stable actors must never be reassigned to a different person. Roles come from the existing local role definitions. Group membership is deliberately absent; clients cannot supply it. Registry and token paths must be absolute regular files, with direct symbolic links rejected. Directory ownership and mount permissions remain operator responsibilities; this does not sandbox arbitrary paths or make unsafe writable directories trustworthy.

Every configured registry credential and every configured legacy role credential is validated before resolving any match. Duplicate tokens or actors, unknown fields, missing files, malformed JSON and invalid credentials fail the entire configuration closed with a generic 503. Invalid or unknown bearer values return 401. Registry snapshots are not cached. Replace the registry atomically to avoid requests observing an intermediate invalid file. Token files are read through the existing bounded credential loader; use atomic replacement for rotations.

Registry principals retain `actor`, `role` and `permissions` and add `identity_kind: "local-user"`. Legacy role-token principals retain their existing response shape and shared `local-operator` / `local-viewer` / `local-reviewer` / `local-admin` actors. Absence of `identity_kind` therefore means legacy shared-role authentication, never an individually identified user. Shared tokens cannot establish uploader privacy. A private multiuser admission policy must explicitly require `identity_kind == "local-user"` and enforce source policy; it must not fall back to a legacy role on rejection.

This interface does not enable central security, OIDC, group management, source sharing, TLS or administrator access grants. Configuration, provisioning, deployment and source-authorization integration remain separate gated work.
