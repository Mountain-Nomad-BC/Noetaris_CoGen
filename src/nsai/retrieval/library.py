"""Natural-language retrieval across current authorized published generations."""
import asyncio
import os
import httpx
from .. import store
from ..semantic_encoder import PINNED_MODEL_SHA256
from .fusion import reciprocal_rank_fusion
from .query import build_retrieval_query


def semantic_hits(question,limit,*,document_ids=None,revision=None,pages=None):
    from ..semantic_jobs import encode_texts
    from ..knowledge import _vector
    query=build_retrieval_query(question)
    encoded=asyncio.run(encode_texts([query.exact]))
    if encoded.get('model_identity',{}).get('sha256')!=PINNED_MODEL_SHA256:
        raise ValueError('Query encoder model mismatch')
    vectors=encoded.get('vectors',[])
    coverage=encoded.get('coverage',[])
    if (len(vectors)!=1 or len(coverage)!=1 or coverage[0].get('complete') is not True
        or type(coverage[0].get('input_tokens')) is not int or coverage[0]['input_tokens']<1
        or coverage[0].get('covered_tokens')!=coverage[0]['input_tokens']):
        raise ValueError('Invalid complete query encoding')
    vector=_vector(vectors[0],384)
    with store.connect() as conn:
        return [row[0] for row in conn.execute(
            'SELECT * FROM nsai_library_semantic_search(%s,%s,%s,%s,%s,%s)',
            (vector,document_ids or None,revision,pages or None,query.entity_gate,limit)).fetchall()]


def retrieve(question,limit=12,*,document_ids=None,revision=None,pages=None):
    from ..workflow_store import retrieve as lexical_retrieve,RetrievalHits
    lexical=lexical_retrieve(question,limit,document_ids=document_ids,revision=revision,pages=pages)
    if not os.getenv('NSAI_ENCODER_URL'):
        lexical.coverage['semantic_state']='not-configured'
        return lexical
    try:
        semantic=semantic_hits(question,limit+1,document_ids=document_ids,revision=revision,pages=pages)
    except (httpx.HTTPError,TimeoutError,ValueError):
        lexical.coverage.update(semantic_state='unavailable',exhaustive_answer=False)
        return lexical
    by_id={item['id']:item for item in [*semantic,*lexical]}
    ranked=reciprocal_rank_fusion([[item['id'] for item in lexical],[item['id'] for item in semantic]])
    observed=[dict(by_id[identity],fusion_score=score) for identity,score in ranked]
    result=RetrievalHits(observed,limit)
    result.coverage.update(method='authorized-lexical-semantic-rank-fusion',semantic_state='ready',
        semantic_minimum_cosine=0.35,exhaustive_answer=False,corpus_scope='authorized-current-publications')
    if lexical.coverage['additional_matches_exist']:
        result.coverage.update(additional_matches_exist=True,total_matching_chunks=None)
    return result
