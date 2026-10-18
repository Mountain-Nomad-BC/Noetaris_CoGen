"""Container configuration smoke only; deliberately does not execute generated code."""
import os
from pathlib import Path

if os.getuid() == 0:
    raise SystemExit("FAIL: sandbox process is root")
if not (Path('/proc/self/status').exists()):
    raise SystemExit("FAIL: expected Linux proc status")
print("sandbox smoke ran as non-root without intentionally invoking subprocesses/network")
