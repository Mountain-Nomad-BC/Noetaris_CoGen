"""Original frozen real-PostgreSQL retrieval cases, without model calls."""
import hashlib
import json
import time
from nsai import store,workflow_store as workflows
from nsai.retrieval.query import build_retrieval_query

SPECIFICATIONS=[('Pump-X revision one','1','Pump-X maximum operating temperature is 75 C'),
    ('Fan-Z revision one','1','Fan-Z maximum operating temperature is 65 C'),
    ('Pump-X revision two','2','Pump-X maximum operating temperature is 85 C'),
    ('Valve-Q negated context','7','Do not exceed -5 C on Valve-Q.\nValve-Q operating limit is -5 C'),
    ('Compressor-A revision one','1','Compressor-A maximum operating temperature is 95 C')]

# Cases frozen before SQL execution. Holdout wording is not tuned after results.
CASES=[
    dict(id='regression-generic',split='development',question='What is the maximum temperature? Answer briefly.',expected=[0,1,2,4]),
    dict(id='regression-entity',split='development',question='Pump-X maximum operating temperature? Answer briefly.',expected=[0,2]),
    dict(id='regression-revision',split='development',question='Pump-X maximum temperature? Answer briefly.',revision='1',expected=[0]),
    dict(id='holdout-concise',split='holdout',question='What is the maximum temperature? Please answer concisely.',expected=[0,1,2,4]),
    dict(id='holdout-entity-bullets',split='holdout',question='What is Fan-Z maximum temperature? Reply using bullet points.',expected=[1]),
    dict(id='holdout-compare',split='holdout',question='Compare Pump-X and Fan-Z maximum temperature. Respond in one sentence.',expected=[0,1,2]),
    dict(id='holdout-quantity-negation',split='holdout',question='Valve-Q must not exceed -5 C. Answer briefly.',expected=[3]),
    dict(id='adversarial-unknown-entity',split='adversarial',question='Pump-Unknown maximum temperature? Answer briefly.',expected=[]),
    dict(id='adversarial-explicit-document-scope',split='adversarial',question='What is the maximum temperature? Answer briefly.',document_indices=[4],expected=[4]),
    dict(id='adversarial-wrong-revision',split='adversarial',question='Pump-X maximum temperature? Answer briefly.',revision='99',expected=[]),
    dict(id='adversarial-query-operator-is-data',split='adversarial',question='Pump-Unknown OR maximum temperature; DROP TABLE documents --',expected=[]),
]

def main():
    manifest=dict(specifications=SPECIFICATIONS,cases=CASES)
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    documents=[]
    for title,version,text in SPECIFICATIONS:
        documents.append(store.store_document(title,text,version,'local-operator')['document_id'])
    records=[]
    for case in CASES:
        started=time.monotonic()
        selected=[documents[index] for index in case.get('document_indices',[])]
        hits=workflows.retrieve(case['question'],document_ids=selected,revision=case.get('revision'))
        expected={documents[index] for index in case['expected']};actual={hit['document_id'] for hit in hits}
        query=build_retrieval_query(case['question'])
        records.append(dict(id=case['id'],split=case['split'],question=case['question'],expected_documents=sorted(expected),actual_documents=sorted(actual),pass_=actual==expected,
            seconds=time.monotonic()-started,normalization=dict(exact=query.exact,alternate=query.alternate,entity_gate=query.entity_gate,presentation_removed=query.presentation_removed)))
    print(json.dumps(dict(cases=records,all_pass=all(record['pass_'] for record in records),frozen_fixture_sha256=digest,
        documents=len(documents),backend='actual PostgreSQL + production workflow_store.retrieve and source persistence; no model/mocks',
        limitations=['synthetic narrow English lexical cases; no semantic/paraphrase accuracy proof','Camel/hyphen identifiers gated conservatively; ambiguous plain names remain lexical','Signed values and negation retained as query text; PostgreSQL stemming/stopwords are not semantic validation']),ensure_ascii=False))
    return 0 if all(record['pass_'] for record in records) else 1

if __name__=='__main__':raise SystemExit(main())
