# Current implementation provenance and candidate archive boundary

This document records an engineering disposition, not a comprehensive IP, legal,
privacy, or public-release certification. Publication is not authorized.

## Reference architecture and independently implemented contracts

Remy/RIE, Pacify-X and DVA references supplied architectural patterns and capability
requirements. New implementation must use independently specified local contracts;
corporate source bodies, dictionaries, rules, model artifacts, UI assets and corpora
are excluded. Source-import tooling is retired. Earlier imported-code receipts are
historical records, not current licensing or capability clearance. Runtime contract
replacement and current source review must be checked against an exact source hash
manifest before a source candidate archive is admitted.

## Declared third-party dependencies

The private PDF viewer uses the public PDF.js distribution, version 6.4.299. Its
upstream npm tarball was checked against the package SHA512 integrity value, and
bundled files have SHA256 identities in `assets/pdfjs/provenance.json`. The upstream
Apache-2.0 license is retained in `assets/pdfjs/LICENSE`. This dependency is distinct
from privately supplied architectural references. Other declared runtime and build
dependencies keep their respective licenses and require an exact image/SBOM review.

## Model identity and artifact-specific license

Model weights stay outside this repository and all candidate archives. CPU model
preparation requires an explicit matching SHA256 digest, a regular nonsymlink path,
and a bounded data-only GGUF metadata inspection. The verified artifact is identified
by its digest; file extension or filename never implies Qwen, model family, creator,
license, quality, or permission to redistribute. Metadata license declarations remain
unreviewed; absence is unknown. Historical declarations only apply to their exact
historical digest and do not supply current approval. No model is executed by this
inspection. License or deployment approval is not inferred from verification PASS.

## Packaging and submission disposition

Candidate creation requires a review receipt covering the exact member paths, bytes
and hashes. The documented allowlist includes this document, the project NOTICE,
synthetic-data README and the PDF.js license/provenance only. Historical audit files,
private evidence, plans, local state, credentials, personal absolute paths, model
weights and corporate reference trees are excluded. Source candidate creation also
requires an explicit current-source provenance disposition and explicit member list.
A review receipt is an inspectable local record, not proof of externally authenticated
reviewer authority or authorization to publish.

Every archive contains an exact member hash/size manifest and is independently
reopened and checked before its output is finalized. Duplicate, traversal, symlink,
encrypted, excluded and oversized members are rejected. Known local credentials and
narrow secret/private-path patterns are checked without printing their contents.
These checks are limited and cannot certify absence of every secret, personal datum
or proprietary element. Evidence and architecture qualifications remain separate
from deployment instructions. No archive is uploaded automatically, and the package
is labeled an unapproved candidate rather than public-safe.

## Qualification limits

Central security, AMD/Evolus activation and generated execution remain disabled or
deferred. Dedicated security scanning, exact-source provenance review, model-license
review and exact-archive privacy/license qualification are independent release gates.
A candidate archive or historical passing test receipt does not complete these gates.
