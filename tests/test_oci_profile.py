from pathlib import Path
import sys
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_oci_profile import inspect_profile


def fixture():
    source=yaml.safe_load((ROOT/'deploy/oci/compose.yaml').read_text())
    for name,service in source['services'].items():
        service['image']='registry.example/noetaris/'+name+'@sha256:'+'a'*64
        if name=='edge':service['ports']=[dict(published='443',target=8443,protocol='tcp')]
    return source


def test_oci_profile_is_arm64_private_and_bounded_without_claiming_arm_execution():
    source=fixture();assert inspect_profile(source)==[]
    assert sum(float(s['cpus']) for s in source['services'].values())==3.75


def test_shared_role_tokens_and_internal_published_ports_are_not_production_identity():
    source=fixture();source['services']['api']['environment']['NSAI_API_TOKEN_FILE']='/run/secrets/operator'
    source['services']['db']['ports']=[dict(published='5432',target=5432)]
    errors=inspect_profile(source)
    assert any('role credentials' in e for e in errors) and any('internal port' in e for e in errors)


def test_mutable_images_x86_and_public_data_networks_fail():
    source=fixture();source['services']['api']['image']='api:latest';source['services']['encoder']['platform']='linux/amd64'
    source['networks']['data']['internal']=False
    assert len(inspect_profile(source))>=3


def test_compose_normalized_public_network_omits_false_internal():
    source=fixture();source['networks']['front'].pop('internal')
    assert inspect_profile(source)==[]
    source['networks']['data'].pop('internal')
    assert 'Internal network isolation differs' in inspect_profile(source)
