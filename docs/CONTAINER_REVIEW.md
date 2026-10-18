# Container review and remaining advisories

Python runtime dependencies were upgraded after known inherited advisories were detected.
The exact runtime dependency closure is pinned and hash-verified during Docker installation.
Current package audit reports no known advisories; this is not a comprehensive security guarantee.

Image scans retain all findings. The original database image reported 72 advisories, including
4 critical and 31 high. Its old Go-based gosu helper was replaced with Alpine's C su-exec helper;
zlib, OpenSSL, LDAP and timezone packages were refreshed. The final database artifact copies the
merged patched filesystem into a clean image so removed helpers and superseded layers are absent
from distribution. PostgreSQL remains 16.15 and preserves its data path, entrypoint, stop signal,
ownership and named volume. Exact build output and runtime startup/persistence tests are retained.

The corrected database image scan reports 11 remaining libxml2 advisories: 1 high, 5 medium,
5 low, with no fixes reported by the scanner for the selected distribution. There are no retained
Go helper critical findings in that final filesystem. Source-image scans remain as historical evidence.
The API image reports 28 OS advisories including one high; the CPU model image reports 139 low/
medium advisories. Neither currently reports fixable high/critical advisories. These findings are not
suppressed or assumed non-exploitable. Read `evidence/raw/image-scan-summary.json` and SARIF.

Public production deployment remains blocked. Local safeguards reduce exposure: loopback API,
private DB/model/parser networks, authenticated model API, immutable validated model file,
non-root read-only application/parser/model, no generated execution, dropped capabilities, seccomp
and resource bounds. They do not replace patch availability or independent production assessment.

Docker Scout produced valid reports alongside Windows temporary-archive cleanup warnings.
Those logs are retained; its external temporary files were not deleted or misrepresented as clean.
Rootless Docker, external image signing verification and hostile-code containment certification are pending.
