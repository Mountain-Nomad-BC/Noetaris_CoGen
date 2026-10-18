# Security controls and limitations

Local authentication is active with distinct operator, viewer, reviewer and administrator tokens.
The server owns role grants; request bodies cannot specify authority. Operator cannot review or
administer; viewer cannot ingest or infer; reviewer cannot operate inference. Separate reviewer identities,
source-integrity checks, rationale and expected revisions gate conflict resolution. Shared role tokens are
demo identities, not production identity assurance. The project has one shared local evidence scope.

Central security provider/issuer configuration and admin controls are built as a staged interface.
Central integration is disabled by default and cannot be activated by policy requests. Setting its environment
flag true fails closed. There is no operational central OIDC/Remy/RIE authorization adapter.

API and parser containers run as UID 10001, use read-only root filesystems, drop all capabilities,
set no-new-privileges and resource/PID limits, and retain Docker default seccomp. Only the API has a
loopback host port. DB, parser and model publish none. The parser has a dedicated internal network,
no database/model credentials, bounded worker concurrency, a fixed child program, CPU/address-space
limits and a 20-second wall timeout. This is a bounded parser, not an arbitrary-code security sandbox.
PDFs are extracted as text; embedded JavaScript/actions are not executed or displayed as trusted content.

There are no Docker socket mounts, privileged services, host networks, unconfined seccomp shortcuts,
or model tool-execution APIs. All roles are denied generated execution. Windows PX Gremlin/Nanny
mechanisms are not described as Linux enforcement. Arbitrary generated-code execution stays disabled.

Original source bytes, spans and chunks are immutable via DB permissions and triggers. API uses a
non-superuser role with bounded column updates, without schema CREATE or evidence DELETE rights.
Owner DB credentials are not mounted into API or parser. The audit chain is verified and immutable to
the app role, but lacks an external signature/anchor and can be rewritten by a sufficiently privileged
host/database owner. Input, rate, concurrency, context, output and UTC daily attempt limits contain load.

Browser renders untrusted text through textContent; tokens stay out of localStorage, URLs, model prompts
and evidence logs. Source downloads use attachment/octet-stream. CSP, frame denial, no-store and
nosniff headers protect normal responses. Prompt instructions are untrusted; this is not proof that a model
cannot hallucinate. Missing or invented citation IDs cause a source-excerpt fallback; valid IDs alone do
not prove that an answer is entailed by the cited source. The server warns on unresolved conflicts.

Local Ollama still uses its image's default root identity, with no production credentials, read-only root,
dropped capabilities and a single model-cache volume. PostgreSQL entrypoint initializes as root and
drops to its database user. Rootless engine, custom LSM policy, parser kernel exploits, hostile code escape
testing, production TLS/OIDC, per-user multi-tenancy, advanced egress filtering and external audit anchoring
are not established. API/model networks allow intentional backend access and model downloads.

The demonstrated llama.cpp CPU backend is stricter: UID 10001, no capabilities, readonly root and
GGUF file mount, dedicated internal model network, no host ports/GPU devices, explicit zero GPU layers,
a dedicated key-file secret, and disabled built-in agent tools/UI/slot endpoints. Its authenticated model
API is actually tested: absent key is 401 and the admitted key accesses the configured model. The API
has that model key; the parser does not. Windows model-key files use LF because the upstream C++
line reader retains CRLF's carriage return; normalization preserves the credential value.

Do not expose this local role-token app publicly. Image/dependency scan results are evidence, not blanket
assurance; any findings or unavailable scans must remain visible. Public source packaging is blocked
because Remy-derived code is restricted. Publication requires separate authorization and license review.
