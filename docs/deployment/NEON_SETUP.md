# Neon tooling and optional fallback status

Neon is optional per the latest owner clarification. The existing NSAI authentication authority and local/OCI PostgreSQL remain authoritative. Cloudflare is intended for document/image object storage, subject to verification of the actual products/bucket bindings. No Neon services, schema or app data have been deployed or migrated by these setup commands.

## Verified tooling

- Neon CLI8.8.0 installed globally with `npm i -g neon@latest`.
- Nine official Neon skills installed under `.agents/skills/`. The exact requested skill URL was fetched separately into `state/neon-setup/requested-neon-SKILL.md`, read and compared without overwriting the installed skill.
- The earlier requested `neon init -y` installed global Neon plugins for Codex, Claude Code, Grok Build and VS Code, plus global skills/OAuth MCP configuration for detected Antigravity, Gemini, Copilot and Windsurf agents. No plaintext API keys were written into project MCP configuration.
- Native Codex registration was incomplete after Neon init. `codex plugin add neon-postgres@plugins-cli --json` registered the existing plugin. Native plugin inventory now confirms installed/enabled version2.3.0. It bundles `https://mcp.neon.tech/mcp`. A duplicate standalone MCP server was not added. Reload Codex for newly installed tooling; live MCP OAuth and tool discovery are not yet verified in this agent session.
- CLI sign-in completed. Existing project `royal-haze-42950645`, organization `org-jolly-water-13321639`, branch `production`, region `aws-us-east-2`, free plan and ADMIN permission were verified read-only.

## Every project change from Neon setup

- `.agents/skills/neon*`: nine installed skill directories and their references.
- `.neon`: ignored offline link to the owner-specified existing project/branch. The CLI project lookup later succeeded; no replacement project was created.
- `.gitignore`: Neon init added `.neon` and `node_modules/` ignore entries.
- `package.json` and `package-lock.json`: Neon init created root `@neon/config`/`@neon/env` dependencies. A root build script now runs the real frontend build plus three authenticated Function boundary tests.
- `neon.ts`: generated service declarations for Auth, AI Gateway, private assets bucket and hello Function, plus branch policy. It is retained rather than overwritten. Declarations do not mean services are live.
- `hello.ts`: generated unauthenticated Hello World was replaced with an authenticated server-to-server connectivity check. Missing configuration returns503, invalid/missing credentials401, unsupported methods405 and paths404. It does not grant document access, execute inference or claim database connectivity.
- `deploy/neon/free.config.ts`: separate, unapplied alternative retaining the owner config and disabling paid AI Gateway, with a required server-only Function secret. The CLI8.8.0 dotenv reader returned no keys for a valid one-line env file; the initial dry-run failed closed. Re-running the read-only plan with the secret supplied only in the child process environment succeeds. No deploy was performed.
- `tests/neon-function.test.ts`: three bounded Function contract tests pass. Existing source-provenance hashing was extended to include root Neon/Node inputs, the public env example and Function tests.
- `state/neon-setup/`: ignored skill comparison, installation audit, native registration inventory, dry-run logs and restricted Function secret file. Credentials are not copied into documentation.

## Retained limits

The live account is on Neon's Free plan. `neon config plan` warns AI Gateway cannot serve requests there; no plan upgrade or paid generation was authorized or performed. Neon remains optional, not a substitute for Gemma CPU/AMD or exact free fallback routes. The authenticated Function is only a connectivity scaffold, not NSAI's backend. No live service E2E is claimed. Root `npm run build` passes frontend105tests, bundle/source checks and3Function tests; this does not qualify cloud deployment.

Official skill source: https://neon.com/.well-known/agent-skills/neon/SKILL.md
