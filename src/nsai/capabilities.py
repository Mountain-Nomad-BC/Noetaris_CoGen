"""Declared code surfaces and qualification limits, never an authority grant."""
def registry(ocr_configured=False):
    specifications=[
        ('identity','active-candidate',['/v1/capabilities'],'read','CORE-03','Shared local role credentials; individual identity not commissioned'),
        ('ingestion','active-candidate',['/v1/documents','/v1/files'],'ingest','CORE-01,13,14','Fixed bounded parser; originals immutable'),
        ('pdf-workspace','active-candidate',['/v1/sources/{id}','/v1/sources/{id}/original'],'read','REF-02,03','Pinned private renderer; page scope and processing completeness distinct from accuracy'),
        ('ocr','configured-candidate' if ocr_configured else 'staged-not-enabled',['/v1/files'],'ingest','REF-04,05,06,07,08','Printed English conservative transforms only; degraded/table/formula quality withheld'),
        ('retrieval','active-candidate',['/v1/search','/v1/chat'],'read','CORE-02,12','Scoped lexical exact and OR alternatives, fused with MiniLM semantic matches when the isolated encoder is configured; response receipts report actual availability'),
        ('cpu-draft','active-candidate',['/v1/reason'],'chat','CORE-04,09,11,16','Actual tokenizer admission; independent support guard is conservative, not full entailment proof'),
        ('review','active-candidate',['/v1/review/{id}'],'review','CORE-05,06','Independent local-role source review; no model approval'),
        ('memory','active-candidate',['/v1/memory/{id}'],'chat','CORE-07,08,10','Bounded original query contract, relevant reviewed context, conflict quarantine'),
        ('engineering-flow','active-candidate',['/v1/issues/analyze'],'propose','REF-19,20,21','Issue descriptions assembled as source-bound candidate observations and review-order flows; not actual transcripts'),
        ('assembly','active-candidate',['/v1/assembly/{id}','/v1/governed/proposals'],'propose','REF-11,12,13','Data-only graph and proposals; no execution or automatic promotion'),
        ('local-governance','active-candidate',['/v1/admin/security','/v1/admin/actions'],'review','REF-15','Sensitive increases need independent stored approval; OIDC step-up unavailable'),
        ('retention','inspection-only',['/v1/admin/retention'],'admin','SUP-17','Growth visibility; all originals/audit held; no automatic cleanup'),
        ('central-security','disabled',['/v1/admin/policy'],'admin','REF-16,27','All activation denied; provider contracts only'),
        ('generated-execution','disabled',['/v1/execute'],'none','REF-26','No admitted executor'),
        ('amd-evolus','deferred',[],'none','REF-28','No GPU or external workflow commissioning'),
        ('semantic-index','candidate-local-worker',['/v1/knowledge/{id}','/v1/knowledge/{id}/formulas','/v1/knowledge/semantic-search'],'read','REF-29','Pinned optional CPU encoder, source/model-scoped exact cosine and authorized library rank fusion; no automatic canon promotion'),
        ('signed-anchor','deferred',[],'none','REF-31','Local digest chain is not an external signature'),
    ]
    return [dict(id=i,state=s,routes=r,permissions=[p] if p!='none' else [],requirement_ids=f.split(','),
        limitations=l,qualification='partial; fresh independent evidence required',evidence=['evidence/implementation/'],authority_granted=False) for i,s,r,p,f,l in specifications]
