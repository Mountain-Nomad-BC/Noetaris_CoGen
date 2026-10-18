"""Acquisition failures preserve foreign files and exclusively publish new models."""
from io import BytesIO
import sys
import pytest
from test_ops_implementation import load


def test_existing_partial_survives_failed_download(monkeypatch,tmp_path):
    module=load('fetch_semantic_model');module.ROOT=tmp_path
    directory=tmp_path/'state/models/all-MiniLM-L6-v2';directory.mkdir(parents=True)
    partial=directory/'model.onnx.partial';partial.write_bytes(b'previous interrupted acquisition bytes')
    monkeypatch.setattr(sys,'argv',['fetch_semantic_model.py','--download'])
    calls=[]
    def download(*args,**kwargs):calls.append(True);return BytesIO(b'new acquisition')
    monkeypatch.setattr(module.urllib.request,'urlopen',download)
    with pytest.raises(FileExistsError):module.main()
    assert partial.read_bytes()==b'previous interrupted acquisition bytes'
    assert calls==[]


def test_owned_partial_is_cleaned_when_network_fails(monkeypatch,tmp_path):
    module=load('fetch_semantic_model');module.ROOT=tmp_path
    monkeypatch.setattr(sys,'argv',['fetch_semantic_model.py','--download'])
    def failed(*args,**kwargs):raise OSError('synthetic offline error')
    monkeypatch.setattr(module.urllib.request,'urlopen',failed)
    with pytest.raises(OSError,match='synthetic offline'):module.main()
    assert list((tmp_path/'state/models/all-MiniLM-L6-v2').iterdir())==[]


def test_parallel_published_target_survives_download(monkeypatch,tmp_path):
    module=load('fetch_semantic_model');module.ROOT=tmp_path
    monkeypatch.setattr(sys,'argv',['fetch_semantic_model.py','--download'])
    directory=tmp_path/'state/models/all-MiniLM-L6-v2';target=directory/'model.onnx'
    class ConcurrentPublication(BytesIO):
        def __exit__(self,*args):
            target.write_bytes(b'parallel published bytes')
            return super().__exit__(*args)
    monkeypatch.setattr(module.urllib.request,'urlopen',lambda *a,**k:ConcurrentPublication(b'new acquisition'))
    with pytest.raises(FileExistsError):module.main()
    assert target.read_bytes()==b'parallel published bytes'
    assert not (directory/'model.onnx.partial').exists()
