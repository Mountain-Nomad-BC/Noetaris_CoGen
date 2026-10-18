"""Normative privacy cases independent of storage and retrieval implementation."""
from dataclasses import replace
import pytest
from nsai.document_access import SourcePolicy,Grant,source_decision,derived_decision,cache_scope

PRIVATE=SourcePolicy('manual','alice',1)
PUBLIC=SourcePolicy('paper','bob',1)


@pytest.mark.parametrize('role',['operator','viewer','reviewer','admin','learning-agent'])
def test_project_roles_and_agents_do_not_imply_private_source_access(role):
    assert not source_decision(PRIVATE,'bob',role,'read',now=10).allowed


@pytest.mark.parametrize('action',['read','query','derive','manage','share','revoke'])
def test_owner_has_explicit_owner_authority(action):
    assert source_decision(PRIVATE,'alice','operator',action,now=10).allowed


def test_explicit_reader_can_query_but_cannot_delegate():
    policy=replace(PRIVATE,grants=(Grant('user','bob',frozenset({'read'})),))
    assert source_decision(policy,'bob','operator','query',now=10).allowed
    assert not source_decision(policy,'bob','operator','share',now=10).allowed
    assert not source_decision(policy,'bob','operator','manage',now=10).allowed


def test_server_group_membership_is_required_and_revocable():
    policy=replace(PRIVATE,grants=(Grant('group','demo-library',frozenset({'read'})),))
    assert source_decision(policy,'bob','viewer','read',groups={'demo-library'},now=10).allowed
    assert not source_decision(policy,'bob','viewer','read',groups=set(),now=10).allowed


@pytest.mark.parametrize('grant',[
    Grant('user','bob',frozenset({'read'}),revoked=True),
    Grant('user','bob',frozenset({'read'}),expires_at=10),
    Grant('user','bob',frozenset({'share'})),
])
def test_revoked_expired_and_delegation_only_grants_fail_closed(grant):
    assert not source_decision(replace(PRIVATE,grants=(grant,)),'bob','viewer','read',now=10).allowed


def test_administrative_access_requires_grant_and_audit_obligation():
    assert not source_decision(PRIVATE,'admin','admin','read',now=10).allowed
    policy=replace(PRIVATE,grants=(Grant('user','admin',frozenset({'read'})),))
    decision=source_decision(policy,'admin','admin','read',now=10)
    assert decision.allowed and decision.audit_required


def test_public_paper_private_manual_relationship_is_not_discoverable_by_paper_owner():
    policies={'manual':PRIVATE,'paper':PUBLIC}
    assert derived_decision(['paper'],policies,'bob','operator','query',now=10,provenance_complete=True).allowed
    decision=derived_decision(['paper','manual'],policies,'bob','operator','query',now=10,provenance_complete=True)
    assert not decision.allowed
    shared=replace(PRIVATE,grants=(Grant('user','bob',frozenset({'read'})),))
    assert derived_decision(['paper','manual'],{**policies,'manual':shared},'bob','operator','query',now=10,provenance_complete=True).allowed


@pytest.mark.parametrize('sources,complete',[([],True),(['paper'],False),(['unknown'],True)])
def test_empty_unknown_and_incomplete_provenance_deny(sources,complete):
    assert not derived_decision(sources,{'paper':PUBLIC},'bob','operator','read',now=10,provenance_complete=complete).allowed


def test_cache_identity_changes_on_revocation_or_group_membership_change():
    old=cache_scope({'paper':PUBLIC},['paper'],'bob',membership_epoch=1)
    assert old!=cache_scope({'paper':replace(PUBLIC,epoch=2)},['paper'],'bob',membership_epoch=1)
    assert old!=cache_scope({'paper':PUBLIC},['paper'],'bob',membership_epoch=2)
    assert old!=cache_scope({'paper':PUBLIC},['paper'],'alice',membership_epoch=1)
