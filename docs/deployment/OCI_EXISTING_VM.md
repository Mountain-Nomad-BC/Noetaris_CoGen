# Existing Oracle VM deployment

This target supersedes the laptop-hosted backend and older ARM64 OCI target. Use the existing instance; do not recreate, resize, terminate or upgrade billing.

- Host: `opc@129.80.119.161`, Oracle Linux 9.8, x86-64.
- Application source: `/opt/noetaris/current`.
- Existing Spark frontend: https://noetaris-cogen.web.app.
- Confirmed Firebase project/site: `noetaris-cogen`. The new instructions mention `noetaris`; this is a historical project mismatch, not permission to replace the deployed frontend.
- SSH verified. The disclosed download key was replaced: replacement login verified before the old public key was removed. New private key remains owner-local under `.ssh`, outside the repository.
- Outbound HTTPS verified. Initial firewall allows SSH only. No application/database/admin ports have been opened.
- Docker 29.9.1 and Compose 5.6.0 installed; Docker is enabled at boot. API, parser and MiniLM encoder are running under `/opt/noetaris/compose.json`. API loopback readiness returned HTTP 200 with database reachable/schema verified; anonymous document request returned 401.
- Existing Neon production `neondb` migrated with 40 schema entries after branch qualification. Native PostgreSQL 18 access contract matches the PostgreSQL 16 definitions except its additional NOT NULL catalog constraints. Production did not receive qualification fixture uploads.
- Six real application/ownership checks passed on the disposable Neon branch. MiniLM on Oracle generated an actual 384-dimensional embedding with complete input coverage.
- Index worker is deliberately not yet activated: canonical provider-account worker admission and complete public sign-in/indexing qualification remain pending. Remote model dispatch and R2 application custody remain pending. No public backend URL or full application acceptance is claimed.

## Owner access

```powershell
ssh -i "$env:USERPROFILE\.ssh\noetaris-oci-deploy-ed25519" opc@129.80.119.161
```

Do not use the retired download key. Do not publish private keys or copy them into application configuration.

## Compatibility work still required

The older `deploy/oci/compose.yaml` explicitly selects ARM64 and is not this host's launch configuration. Native PostgreSQL 18 is now separately packaged in `database/access-contract-pg18.json`; PostgreSQL 16 retains its original contract. Managed role setup verifies dangerous role flags are absent instead of issuing unsupported superuser-only ALTER attributes. Both paths retain least-privilege grants and schema validation.

Firebase ID-token integration, private R2 application custody, hosted AMD dispatch and actual public end-to-end checks remain pending. Source availability, a healthy host or a container build is not evidence that those workflows work.

## Current VM operations

```bash
sudo systemctl status noetaris-demo.service
sudo docker compose -f /opt/noetaris/compose.json ps
sudo docker compose -f /opt/noetaris/compose.json logs --tail 100 api parser encoder
sudo systemctl restart noetaris-demo.service
curl --fail http://127.0.0.1:8787/readyz
sudo systemctl stop noetaris-demo.service
```

The systemd unit is `deploy/oci/noetaris-demo.service`. It references the actual installed Compose file and starts existing images, without rebuilding at boot. API binds only `127.0.0.1:8787`; parser/encoder publish no host ports. Credentials are mounted from `/etc/noetaris/secrets`, readable by container UID 10001. Docker and application logs have bounded rotation.

Stopping preserves Neon data and model/secret files. Never use `down --volumes` as routine shutdown. Docker restart and a real VM reboot both passed; Docker and the application service became active again and API readiness verified Neon/schema. The VM is independent of laptop Docker, but the public frontend is not yet connected to it.

A temporary Neon compatibility branch `noetaris-oci-compat-20261018` contains synthetic qualification documents and expires October 18, 2026 at 06:00 UTC. It is not the production application database. Production migrations were refused unless its public schema was empty.

