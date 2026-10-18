# Owned upgrade and recovery qualification

The latest [private restore/resume receipt](../../evidence/implementation/private-upgrade-recovery/nsai-upgrade-aa7eef430226/receipt.json) passed 32 scoped checks on API `3b0fd264`. It exercises application-created private data, grants/revocation, a fresh restored container, full definition sealing, durable checkpoint reuse, and an original mixed PDF whose exact pre-OCR native text (including its trailing newline) and snapshot hash survive restore and migration. The synthetic encoder and synthetic OCR alternative qualify preservation/recovery behavior, not recognition or semantic quality. The earlier failed attempts remain retained. The separate [process-crash rehearsal](../../evidence/process-crash-recovery/d1e5ecd6e59d43a2a5c2492304357fde/receipt.json) passes acknowledged-commit and unfinished-source rollback checks after SIGKILL on an owned persistent volume, with all 40 public tables preserved. Concurrent backups, host power-loss recovery, PITR, RTO/RPO, long-lived API-pool recovery and full disaster recovery remain unaccepted.

This rehearsal exercises real PostgreSQL with original synthetic data. It does
not admit a live migration, full deployment, downgrade or rollback of user data.
The original live application, database, volumes, credentials and model endpoint
are never selected. Testing evidence is retained separately under
`evidence/implementation/upgrade-recovery/`.

## Scope and resource limits

Run `.venv/Scripts/python.exe scripts/qualify_upgrade_recovery.py` from the project
directory. It pins the locally available qualified database image
`sha256:e8d60b4d26e679424148c662d01229c05d0d661745d846e7911af78b88bd9f6d`
and checks actual PostgreSQL 16.15. A random owned internal Docker network has no
host-published ports. Each database uses a nonroot UID, read-only filesystem,
all capabilities dropped, no new privileges, PID limit64 and256MiB PostgreSQL
tmpfs with nodev/nosuid/noexec. One database runs at a time. Database limits are
0.75CPU/768MiB; the optional pinned-image package client uses0.25CPU/256MiB.
Aggregate limits remain1CPU/1GiB. The whole job is bounded to600seconds; backup
streams are limited to16MiB/90seconds. Cleanup bypasses the job deadline and
verifies exact random ownership labels before removing resources.

Fresh synthetic credentials remain private. SQL containing credentials is not
written to evidence; command outputs redact those fixture values. Evidence
records exact source/SQL-input/output/artifact hashes and real command exits.
Failed runs and incomplete captures remain inspectable and never become PASS.

## Test sequence

1. Copy exact current original SQL bytes through `0003_workflows.sql` into an
   owned temporary historical window. Apply the real migration journal helper.
   Populate20 synthetic documents/40 claims,10 sessions/messages, one explicitly
   failed synthetic inference and an inference-disabled policy. Record table
   bytes, schema indexes/triggers, canonical privilege/role policy and sequences.
2. Capture and independently admit an exclusive pre-upgrade SQL backup using its
   required size/SHA manifest. Apply the actual current ordered SQL and shared
   `role_sql` privilege contract. Require original table bytes unchanged and the
   complete journal equal to exact current migration-file hashes. Reapply and
   require an exact no-op.
3. Deliberately alter a journal hash in this disposable fixture, then require
   refusal and unchanged database fingerprint. Restore that owned test hash.
   Insert an unknown owned journal entry, require refusal and unchanged state,
   then remove only that explicitly introduced fixture row.
4. Append an owned failure-only migration that creates/inserts a probe table and
   divides by zero. Require nonzero exit and an identical complete fingerprint:
   no committed DDL, data, journal or privilege change may survive.
5. Preserve an owned hold tag for the exact compatibility image before work.
   Execute actual package helpers from retained previous privacy-only image
   `sha256:2ffe38c418aa16260baeaa9b6f0469ce9e58e84fdff792f7784746bef824113d`
   against the upgraded owned database using the shared current app role. Probe
   existing document/claim reads, ingest one new synthetic source and require
   exact original-byte retrieval. This is a package-helper compatibility smoke,
   not complete old HTTP/auth/UI/inference API compatibility. An explicitly
   reviewed alternative requires `--compatibility-image sha256:<64hex>`; mutable
   tags and invalid digests are refused. Cleanup removes only this run's hold
   tag after verifying its exact image identity, retaining all original tags.
6. Capture a verified-manifest upgraded dump; stop/remove the source database.
   Create a fresh second database, bootstrap only its role identity, restore the
   actual dump and apply the exact shared privilege contract. Compare every
   table byte hash, sequence state, index/trigger and canonical ACL/role policy
   against the source. Require a subsequent current migration to be a no-op.
7. Remove the current-schema restored database. Restore the pre-upgrade backup
   into a third sequential fresh database, require exact historical table bytes,
   sequences, indexes/triggers and role/ACL state, and admit its journal using
   the exact historical migrator. No destructive in-place downgrade is performed.
8. Require unchanged host migration/helper/runner hashes and remove all owned
   containers/network. The final receipt retains the cleanup outcome.

## Evidence and limits

`current.json` points to the latest run's receipt. Each run directory retains
bounded command stdout/stderr, backup bytes and manifests, pre/post/restore
fingerprints and an artifact SHA manifest. Eighteen pure contract tests additionally
exercise missing/tampered manifests, negative retained-data expectations,
ownership refusal, cleanup after the job deadline expires and preservation of
the previous receipt when a new atomic publication fails, exact image admission
and refusal to untag a hold reference whose image identity changed.
Actual runtime results must be read from that run's receipt; this document does
not assert a run passed merely because the runner exists.

The historical window is reconstructed from current original SQL files, not an
archived deployed schema. Arbitrary older documents lacking original bytes are
not backfilled or advertised as source-custody compatible. No concurrent live
application snapshot, maximum-capacity dataset, PITR, disk-full destruction,
power loss, real user-data recovery, complete old API behavior or destructive
downgrade is qualified here. Original backup manifests retain
`restore_verified:false`; a separate matching restore receipt records actual
verification without rewriting capture evidence. Independent card/dependency,
security, rights and final-release gates remain open.

The initial run `nsai-upgrade-e8815b5263a8` remains FAIL because its shared
qualification helper changed during execution. Its16 successful runtime cases
and source-binding failure are retained; cleanup passed. A fresh run after the
helper's announced freeze supplies the authoritative current attempt. The
initial failure is not relabeled or hidden.

The second run `nsai-upgrade-4cf4e7243e52` remains FAIL after10 passing migration
checks because the intermediate7194 image became unavailable after its admission
check while the candidate tag was replaced. Cleanup passed. This exposed an
artifact-preservation gap; the runner now holds the reviewed previous image
before starting. The earlier actual7194 package smoke remains historical within
the first failed run, not qualification of the current candidate. The fresh
attempt probes retained actual previous application2ffe instead. Neither failed
run is promoted to PASS.

## Completed owned result

Run `nsai-upgrade-c4f3c5aa43fe` passes all21 scoped cases and483 recorded command
operations. It proves the populated upgrade, refusal/transaction rollback paths,
actual previous2ffe package-helper probe, exact second-database current restore
and exact third-database pre-upgrade restore/historical journal admission.
Migration/helper/runner hashes remain unchanged. Source database cgroup peak is
91,607,040bytes; quota limits remain distinct from this one measured fixture.
All owned containers, internal network and temporary hold tag were removed.
See `evidence/implementation/upgrade-recovery/summary.json` and the run directory;
the two prior failed runs remain intact. No full old HTTP API, live rollback,
concurrent-write snapshot, general recovery SLO or card acceptance follows.
