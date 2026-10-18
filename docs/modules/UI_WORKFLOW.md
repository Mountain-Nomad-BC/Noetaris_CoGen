# Console specification — borrow the good interface idea, not Remy proprietary code

## Desktop composition

- **Left rail**: sessions, document sets, task runs, active corpus/index version.
- **Main panel**: persistent chat with streamed user turns, assistant response, mode badge `deterministic` / `AMD model` / `unavailable`, evidence links.
- **Right panel**: evidence inspector with document name, exact span/page, hash, version, claim state and conflict alternatives.
- **Bottom drawer**: job progress, validation tests, learning candidates, log trace. Add optional graph map only if basic flow stable.

## Primary user journey (must work end to end)

1. User uploads synthetic supplier old/current specs. UI shows real job statuses, source hashes and revision metadata.
2. Candidate extraction creates claims with original source locations.
3. Contradiction panel shows `Pump-X operating limit: 85 C` versus `75 C` with source citations, not a forced choice.
4. User asks a question; NSAI explains uncertainty without claiming verified truth.
5. With configured AMD endpoint, a real model explains the conflict based only on bounded candidate evidence; UI shows `model_unverified` until validation.
6. Reviewer approves/resolves only if independent backend authority feature passes. Otherwise show `REVIEW NOT ENABLED` and a demo-only review preview.
7. Optional Evolus action makes a vendor-review ticket / workflow and records external confirmation.

## Functional UI checks

- No token in localStorage, URL, logs, copied screenshots or page source; local text-field token is transient in memory. Production changes to OIDC session.
- No raw HTML insertion from generated content or document text (XSS test).
- Every source link resolves to permission-checked source span, not an arbitrary URL from LLM output.
- No "approve" button until backend reviewer authorization is available; disabled state explains why.
- Model response should display source state and uncertainty; don't style candidate as verified.
- Keyboard navigable, readable on 1366x768 and mobile; accessible contrast.
- Offline/provider down states show deterministic fallback labeled correctly.

## Key reusable original files already in kit

`assets/index.html`, `assets/index.css`, `assets/app.js`, and `src/nsai/api.py`. Replace the three assets with a built app only if time allows; no need for Node/npm pipeline to win the event.
