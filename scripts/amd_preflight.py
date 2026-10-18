"""Fail-closed AMD host inspection. Does not launch services or claim GPU inference."""
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def record(name,passed,detail):checks.append(dict(name=name,status='PASS' if passed else 'PENDING',detail=detail))
record('native Linux AMD host',platform.system()=='Linux' and 'microsoft' not in platform.release().lower(),platform.platform())
for device in ('/dev/kfd',os.getenv('NSAI_GPU_RENDER_DEVICE','/dev/dri/renderD128')):
    record('ROCm device '+device,Path(device).exists() and os.access(device,os.R_OK|os.W_OK),'Must be accessible to inference service identity')
image=os.getenv('NSAI_VLLM_IMAGE','')
record('immutable image selection',bool(re.fullmatch(r'[^\s]+@sha256:[a-f0-9]{64}',image)),image or 'Set verified image digest; starter tag is not deployment approval')
model=os.getenv('NSAI_VLLM_MODEL','')
record('model identity and license reviewed',bool(model) and os.getenv('NSAI_MODEL_LICENSE_REVIEWED')=='true',model or 'Model and license review missing')
probe=shutil.which('rocminfo')
if probe and platform.system()=='Linux':
    result=subprocess.run([probe],capture_output=True,text=True,timeout=30)
    record('ROCm GPU visibility',result.returncode==0 and 'gfx' in result.stdout,result.stdout[:12000])
else: record('ROCm GPU visibility',False,'rocminfo unavailable')
report=dict(captured_at=datetime.now(timezone.utc).isoformat(),checks=checks,
    deployment_admitted=all(c['status']=='PASS' for c in checks),gpu_inference='PENDING',performance='PENDING')
(ROOT/'evidence/raw/amd-preflight.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['deployment_admitted'] else 1)
