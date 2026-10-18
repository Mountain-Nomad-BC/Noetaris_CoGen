# Firebase Spark static Hosting

## Published frontend

- Homepage: **https://noetaris-cogen.web.app**
- Firebase project/site: `noetaris-cogen` (owner explicitly confirmed; distinct from the earlier Google CLI project `noetaris`).
- Service: Firebase static Hosting only. No App Hosting, Functions, Cloud Run or billing enablement was performed.
- Current Hosting version: `9250d0a8f600b82e`.
- Current deployment configuration: `state/firebase-preparation/3c6dd53fb4fe425abe0e71ab0afcec8d/firebase.json` (owner-held generated state).
- Target configuration: `state/google-deployment/firebase-static-target.json`.
- CLI deployment receipt: `state/google-deployment/firebase-static-deploy-final.json`.
- Public Chromium HTTPS/page/layout receipt: `state/google-deployment/firebase-public-verification.json`.

The published artifact includes the actual React public pages, docs, Terms, Privacy and AI disclosure plus allowlisted PDF runtime assets. Private verification files, source maps, raw evidence and server secrets are excluded. Public notices disclose remaining retention/contact and service activation limitations. Local bearer-credential fallback is offered only on loopback hosts, not the public site.

## Backend boundary

Static Hosting serves files. It does not run the Python NSAI API, PostgreSQL, indexing worker, parser or MiniLM encoder. The current static build is bound to its exact Hosting origin with same-origin API paths; there is not yet a live API gateway behind them. This is a published frontend, **not a qualified working public SSO/document application**. No synthetic API responses or shared demo identity were substituted.

Default HTTPS hostnames are acceptable under the owner's new demo scope. Separate-origin authenticated API deployment still requires a qualified cookie/CSRF/origin approach; don't simply enable wildcard CORS or replace HttpOnly sessions with browser-persisted credentials. No OCI host is assumed, no paid compute is authorized. A free existing Python/container host or an owner-approved temporary Docker tunnel is needed next.

Rebuild with the exact `VITE_APP_ORIGIN` and `VITE_API_ORIGIN`, create a fresh bounded bundle with `scripts/prepare_firebase.py`, verify it and deploy only `hosting:noetaris-cogen` with an explicit project/config. Do not deploy historical `.test` rehearsals or claim a static site created the backend.
