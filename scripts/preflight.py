"""Host preflight for local NSAI engineering. No network traffic or secret output.
Not a GPU qualification test or deployment certificate.
"""
import argparse
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def command_output(args):
    if not shutil.which(args[0]):
        return {"ok":False,"detail":"not installed"}
    try:
        p=subprocess.run(args, capture_output=True,text=True,timeout=8,check=False)
        return {"ok":p.returncode==0,"detail":(p.stdout or p.stderr).strip()[:300]}
    except (OSError,subprocess.TimeoutExpired) as e:
        return {"ok":False,"detail":type(e).__name__}

def inspect():
    python_ok=sys.version_info >= (3,12)
    docker=command_output(['docker','version','--format','{{.Server.Version}}'])
    compose=command_output(['docker','compose','version','--short'])
    free=shutil.disk_usage(ROOT).free//(1024**3)
    secrets = [ROOT/'secrets/api_token.txt',ROOT/'secrets/db_password.txt']
    return {"system":platform.platform(), "python":sys.version.split()[0], "python_312_plus":python_ok,
            "docker_server":docker, "compose_plugin":compose, "disk_free_gib":free,
            "secrets_exist":all(p.is_file() for p in secrets),
            "amd_gpu_verified":False,
            "notes":["docker unavailable here does not mean Compose file invalid", "run AMD host checks on actual Linux GPU machine"]}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--json',action='store_true');args=parser.parse_args()
    out=inspect()
    print(json.dumps(out,indent=2))
    if not out['python_312_plus']:raise SystemExit(1)
