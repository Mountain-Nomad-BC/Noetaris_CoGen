# Isolated printed English OCR

This fixed CPU worker accepts original PDF bytes at private `POST /ocr` on port
8091 with an independent `NSAI_OCR_TOKEN_FILE` bearer token. It has no database,
model or central-security credentials. Activation and Compose release policy are
owned by the project release gate; building this image does not enable it.

The image pins the Python base digest, every observed Debian package version and
the pypdf wheel SHA256. A removed repository version causes a build failure;
updating the closure requires deliberate requalification. Debian package and
upstream notices are retained in `/usr/share/doc/`; standard third-party software
licenses apply. This image includes Poppler and is not an IP-free binary.

Run with UID 10002, read-only root, dropped capabilities, no-new-privileges,
an internal network with no host ports, one CPU, 768 MiB memory, 64 PIDs, and a
128 MiB noexec/nosuid tmpfs at `/tmp`. Mount only its own token read-only. The
qualification command uses `--network none` and synthetic inputs.

The child enforces 512 MiB address space, CPU/file/FD limits, 12 million pixels
before rendering, 300 DPI, ten seconds combined rendering/OCR per page and a
120 second job budget. The HTTP parent has a 125 second child deadline and kills
the child process group on expiration. Outputs and diagnostics are bounded files
in tmpfs rather than unlimited memory captures. Language selection is English
only. Raster-only PDFs have an explicit OCR-required native-parser receipt.

OCR text stays unverified source extraction. Page `complete` means processing
coverage; it does not mean accuracy or authority. Word engine scores are not
probabilities. Failed/unsupported pages remain incomplete. Handwriting, formula
recognition, other languages, deskew, orientation recovery, cropped/rotated PDFs,
and non-default UserUnit are unsupported initially. Complex transforms are
withheld instead of issuing incorrect citation boxes. General OCR accuracy and
tail latency gates require labeled held-out calibration; one exact synthetic
page is a smoke check only.

Primary CLI references:

- [Tesseract command-line and TSV output](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html)
- [Debian pdftoppm manual](https://manpages.debian.org/bookworm/poppler-utils/pdftoppm.1.en.html)

Fresh qualification lives separately under `evidence/implementation/parser-ocr-*`.
