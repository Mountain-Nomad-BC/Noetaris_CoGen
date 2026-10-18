"""Original model and archive boundary fixtures; no production source archive."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys
from zipfile import ZipFile
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_cpu_model import verify_model,gguf_metadata
from package_submission import build_candidate
from release_audit import audit_payloads,audit_archive,MANIFEST

def tiny_model(path,metadata=None):
    fields=metadata or {'general.architecture':'fixture-unknown-family'}
    data=b'GGUF'+struct.pack('<IQQ',3,0,len(fields))
    for key,value in fields.items():
        key=key.encode();value=value.encode()
        data+=struct.pack('<Q',len(key))+key+struct.pack('<IQ',8,len(value))+value
    path.write_bytes(data);return hashlib.sha256(data).hexdigest()

def test_model_requires_explicit_digest_and_never_infers_qwen_or_license(tmp_path):
    model=tmp_path/'Qwen-branded.gguf';digest=tiny_model(model)
    for expected in [None,'',digest[:-1],'a'*64]:
        with pytest.raises(ValueError):verify_model(model,expected)
    result=verify_model(model,digest)
    assert result['license_status']=='unknown' and result['license'] is None
    assert result['metadata']['declared']['general.architecture']=='fixture-unknown-family'
    assert result['artifact_id']=='sha256:'+digest and not result['redistribution_approved']

def test_declared_model_license_is_unreviewed_and_truncated_metadata_fails(tmp_path):
    model=tmp_path/'model.gguf';digest=tiny_model(model,{'general.license':'fixture-restricted-license'})
    assert verify_model(model,digest)['license_status']=='artifact-declared-unreviewed'
    model.write_bytes(b'GGUF'+struct.pack('<IQQ',3,0,1))
    with pytest.raises(ValueError):gguf_metadata(model)

def test_original_symlink_policy_precedes_resolution(tmp_path):
    target=tmp_path/'target.gguf';digest=tiny_model(target);link=tmp_path/'alias.gguf'
    try:link.symlink_to(target)
    except OSError:pytest.skip('Host symlink privilege unavailable; production rejection also covers junctions')
    with pytest.raises(ValueError,match='symlinks'):verify_model(link,digest)

def test_exact_reviewed_candidate_roundtrip_and_stale_review_rejection(tmp_path):
    (tmp_path/'NOTICE').write_text('Original fixture notice')
    allowlist=['NOTICE'];records=audit_payloads([('NOTICE',(tmp_path/'NOTICE').read_bytes())])
    review={'disposition':'reviewed-candidate','publication_approved':False,'members':records,'review_id':'fixture-review','reviewer':'fixture-independent-reviewer'}
    target=tmp_path/'candidate.zip';report=build_candidate(tmp_path,target,allowlist,review=review)
    assert report['status']=='PASS' and not report['published']
    assert audit_archive(target,expected_allowlist=allowlist)['members']==records
    (tmp_path/'NOTICE').write_text('Changed after review')
    with pytest.raises(ValueError,match='stale'):build_candidate(tmp_path,tmp_path/'second.zip',allowlist,review=review)
    with pytest.raises(ValueError):audit_archive(target,expected_allowlist=['unknown'])

@pytest.mark.parametrize('name',['../outside.txt','secrets/token.txt','state/model.gguf','C:/Users/Private/file','docs/../file','a\\b','.env.local','docs/CON.txt','docs/trailing.','docs/trailing '])
def test_malicious_archive_member_names_are_rejected(name):
    with pytest.raises(ValueError):audit_payloads([(name,b'synthetic')])

def test_duplicate_secret_privatepath_and_tampered_manifest_rejected(tmp_path):
    with pytest.raises(ValueError):audit_payloads([('NOTICE',b'a'),('notice',b'b')])
    with pytest.raises(ValueError):audit_payloads([('NOTICE',b'C:\\Users\\fixture\\private')])
    with pytest.raises(ValueError):audit_payloads([('NOTICE',b'fixture-private-token')],forbidden_values=[b'fixture-private-token'])
    target=tmp_path/'bad.zip'
    with ZipFile(target,'w') as archive:
        archive.writestr('NOTICE','original');archive.writestr(MANIFEST,json.dumps({'publication_approved':False,'privacy_qualification':'offline-limited','members':[]}))
    with pytest.raises(ValueError,match='manifest mismatch'):audit_archive(target)


def test_aws_pattern_requires_actual_uppercase_key_shape():
    with pytest.raises(ValueError):audit_payloads([('NOTICE',b'AKIA'+b'A'*16)])
    assert audit_payloads([('NOTICE',b'akia'+b'a'*16)])


def test_cpu_deployment_refuses_relabelled_non_gemma_artifact(tmp_path):
    from prepare_cpu_model import require_gemma
    model=tmp_path/'gemma-renamed.gguf'
    digest=tiny_model(model,{'general.architecture':'qwen2'})
    with pytest.raises(ValueError,match='Gemma'):require_gemma(verify_model(model,digest))
    digest=tiny_model(model,{'general.architecture':'gemma3'})
    assert require_gemma(verify_model(model,digest))['sha256']==digest
