"""Cross-platform key-file contract required by the C++ model server."""
from pathlib import Path
import subprocess
import sys

def test_generated_model_key_is_lf_and_existing_value_is_preserved(tmp_path):
    root=Path(__file__).resolve().parents[1]
    scripts=tmp_path/'scripts';scripts.mkdir()
    script=scripts/'bootstrap_secrets.py';script.write_bytes((root/'scripts/bootstrap_secrets.py').read_bytes())
    subprocess.run([sys.executable,str(script)],capture_output=True,check=True)
    token=tmp_path/'secrets/model_token.txt'
    data=token.read_bytes()
    assert b'\r' not in data and data.endswith(b'\n') and len(data.strip())>=32
    token.write_bytes(data.replace(b'\n',b'\r\n'))
    subprocess.run([sys.executable,str(script)],capture_output=True,check=True)
    assert token.read_bytes()==data
