# Public-repo IP and provenance boundary — mandatory release gate

## Session authorization update — 2026-10-14

Current-byte clarification (2026-10-15): `NOTICE` records replacement of the
earlier runtime imports with local contracts and compatibility names. The current
files differ from the historical adopted hashes. See
[current-component-inventory.json](current-component-inventory.json). The
historical authorization/adoption description below does not constitute a current
file manifest or comprehensive legal clearance; public publication remains denied.

The user explicitly authorized selective Pacify-X and Remy/RIE source reuse for this private build,
subject to licensing, dependency validation and integration testing. That authorization supersedes
the kit's private reference-only workflow. It does not authorize public publication or relicense Remy
source. The adopted Remy manifest remains restricted and excluded from the documentation-only
public-safe preview. Current origin/adopted hashes are in `docs/component-provenance.json`.
The original kit's public-release restrictions below continue to apply to any future publication.

## Allowed / disallowed

| Content | Private analysis | Public NSAI repository |
|---|---|---|
| Independent original code in this package | Yes | Yes, subject to your review |
| Remy/RIE code and static assets in uploaded ZIP | Review only | **No**, absent authorized written permission |
| Remy TurnBurn conceptual architecture descriptions | Yes | New original implementations only |
| Proprietary company manuals, customer data, internal tests or screenshots | Do not distribute | **No** |
| PX Apache-2.0 original source | Review, selectively adapt after verifying provenance | Requires license + notices and per-file third-party checks; prefer adapters/independent code in short event |
| Synthetic samples in `datasets/synthetic` | Yes | Yes, labeled fictitious |
| GPU model files | Verify per-model license and allowed use | Do not bundle huge weights / unreviewed license |
| API keys, tokens, .env, service-role keys, PDFs with private data | Local secrets storage only | Never |

The uploaded Remy root LICENSE states it is proprietary to Rheem Manufacturing Company. A file's individual old license header must not be used to overrule the archive's root restriction. The package includes neither copied Remy source nor internal corpora.

Hackathon public page notes **original, MIT-compliant** submission and a public GitHub repo; this kit's new standalone code is MIT-licensed, but **adding an Apache-2.0 PX file may create a mixed-license tree and requires preserving its Apache terms**. Confirm event rules and owner obligations before publishing any port. `SOURCE_USAGE_MATRIX.csv` identifies references only, not transferred source.

## Required pre-publication review

1. `git status --short` and full `git ls-files`: manually inspect everything added.
2. Run `python scripts/release_audit.py .` then a dedicated credential scanner such as Gitleaks/GitGuardian (a local regex is not a comprehensive detector).
3. Examine binary contents and git history for accidental prior Remy data; deleting only a working file does not clean leaked history.
4. Document each copied component origin, exact upstream commit, license, third-party notices and modification list.
5. Verify synthetic demo values and company name are clearly fictional.
6. Public release is blocked until both licensing and secret reports pass.

## NOTICE handling

If **any** Apache-2.0 PX source is actually incorporated, preserve copyright notices in the adopted files, include a compatible Apache-2.0 copy and any original NOTICE obligations, and update `docs/THIRD_PARTY_PROVENANCE.md`. This clean-room kit makes no claim that arbitrary third-party dependencies have MIT licenses; installed packages carry their own licenses.
