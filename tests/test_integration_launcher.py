"""Model selection and byte-preserving SQL pipe regressions; no Docker changes."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest


def launcher():
    path=Path(__file__).resolve().parents[1]/'scripts/start_integration.py'
    spec=importlib.util.spec_from_file_location('integration_launcher_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_sql_pipe_preserves_lf_bytes(monkeypatch):
    module=launcher();observed={}
    def run(args,**kwargs):
        observed.update(kwargs)
        return SimpleNamespace(returncode=0,stdout=b'OK\n')
    monkeypatch.setattr(module.subprocess,'run',run)
    assert module.run(['docker','exec','owned'],body='BEGIN;\nCOMMIT;\n')=='OK'
    assert observed['input']==b'BEGIN;\nCOMMIT;\n'
    assert 'text' not in observed


@pytest.mark.parametrize('change',[
    {'model_id':'Qwen/Qwen2.5'}, {'sha256':'not-a-digest'},
    {'artifact_path':'relative.gguf'}, {'extra':True},
])
def test_invalid_or_non_gemma_selection_rejected(tmp_path,change):
    config=dict(model_id='google/gemma-selected',artifact_path=str(tmp_path/'model.gguf'),sha256='a'*64)
    config.update(change)
    path=tmp_path/'selection.json';path.write_text(json.dumps(config))
    with pytest.raises(ValueError):launcher().load_gemma_config(path)


def test_explicit_gemma_selection_roundtrips(tmp_path):
    config=dict(model_id='google/gemma-selected',artifact_path=str(tmp_path/'model.gguf'),sha256='a'*64)
    path=tmp_path/'selection.json';path.write_text(json.dumps(config))
    assert launcher().load_gemma_config(path)==config
