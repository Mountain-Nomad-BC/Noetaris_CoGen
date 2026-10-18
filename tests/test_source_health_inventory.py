"""Walk admission is bounded before files are decoded; links are never followed."""
import importlib.util
from pathlib import Path
import time
import pytest


@pytest.fixture
def inventory(monkeypatch):
    root=Path(__file__).resolve().parents[1];monkeypatch.syspath_prepend(str(root/'scripts'))
    spec=importlib.util.spec_from_file_location('source_health_inventory',root/'scripts/audit_source_health.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_directory_and_name_limits_cover_the_walk_phase(tmp_path,inventory):
    for name in ('a','b','c'):(tmp_path/name).mkdir()
    with pytest.raises(ValueError,match='directory_budget'):inventory.collect_paths([tmp_path],time.monotonic()+10,max_directories=2)
    with pytest.raises(ValueError,match='name_budget'):inventory.collect_paths([tmp_path],time.monotonic()+10,max_names=2)
    with pytest.raises(ValueError,match='walk_time_budget'):inventory.collect_paths([tmp_path],0)


def test_nested_roots_deduplicate_and_links_stay_outside_selected_set(tmp_path,inventory):
    folder=tmp_path/'nested';folder.mkdir();data=folder/'a.json';data.write_bytes(b'{}')
    outside=tmp_path/'outside';outside.mkdir();(outside/'b.json').write_bytes(b'{}')
    link=folder/'alias'
    try:link.symlink_to(outside,target_is_directory=True)
    except OSError:pytest.skip('Host cannot create test symlink')
    selected,blocked=inventory.collect_paths([folder,folder],time.monotonic()+10)
    assert selected=={data} and len(blocked)==1
    assert (outside/'b.json').read_bytes()==b'{}'
