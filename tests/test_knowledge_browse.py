import hashlib
import pytest
from nsai import knowledge_browse as browse,research_store,ingestion


@pytest.fixture
def artifact(monkeypatch):
    text='\n'.join(f'Section {number} records a candidate observation.' for number in range(70))+'\nE = m*c^2.'
    parsed=ingestion.parse_source(text.encode(),'fixture.txt');value=research_store.build('a'*32,'1',parsed)
    value.update(document_id='a'*32,revision='1',source_sha256=parsed['original_sha256'],artifact_sha256=research_store.artifact_hash(value))
    monkeypatch.setattr(browse.research_store,'get',lambda document:value)
    monkeypatch.setattr(browse.workflow_store,'source',lambda document:dict(title='Fixture',revision='1',
        original_sha256=parsed['original_sha256'],media_type='text/plain'))
    return value


def test_node_pages_are_complete_bounded_and_formula_lineage_is_preserved(artifact):
    collected=[];offset=0
    while True:
        result=browse.page('a'*32,offset=offset,limit=7)
        assert len(result['items'])<=7 and result['authority_granted'] is False
        collected.extend(node['id'] for node in result['items'])
        if result['next_offset'] is None:break
        offset=result['next_offset']
    assert collected==[node['id'] for node in artifact['knowledge']['nodes']]
    formulas=browse.page('a'*32,kind='formula')
    assert formulas['items'] and formulas['summary']['formula_detection_exhaustive'] is False
    node=formulas['items'][0]
    detail=browse.detail('a'*32,node['id'],limit=1)
    assert detail['node']['formula_data']['evaluation']=='not_attempted'
    assert detail['node']['source_sha256']==hashlib.sha256(('\n'.join(f'Section {number} records a candidate observation.' for number in range(70))+'\nE = m*c^2.').encode()).hexdigest()
    assert detail['total_relationships']>=2 and len(detail['relationships'])==1
    assert detail['citation']['document_id']=='a'*32
    assert detail['authority_granted'] is False


def test_every_page_and_detail_reloads_authorized_artifact(artifact,monkeypatch):
    initial=browse.page('a'*32)
    def denied(document):raise LookupError('Source unavailable')
    monkeypatch.setattr(browse.research_store,'get',denied)
    with pytest.raises(LookupError):browse.page('a'*32,offset=25)
    with pytest.raises(LookupError):browse.detail('a'*32,initial['items'][0]['id'])


@pytest.mark.parametrize('arguments',[dict(limit=51),dict(offset=-1),dict(kind='verified'),dict(query='x'*201)])
def test_navigation_bounds_fail_before_artifact_loading(monkeypatch,arguments):
    monkeypatch.setattr(browse.research_store,'get',lambda document:pytest.fail('Invalid bounds reached storage'))
    with pytest.raises(ValueError):browse.page('a'*32,**arguments)


def test_automatic_source_organization_accounts_for_every_extracted_node(artifact):
    result=browse.page('a'*32,limit=25)
    groups=result['summary']['node_kinds']
    assert set(groups)=={'document','passage','source_span','observation','concept_mention','formula'}
    assert sum(groups.values())==result['summary']['nodes']
    assert groups['document']==1
    assert groups['formula']>=1
    assert result['authority_granted'] is False
