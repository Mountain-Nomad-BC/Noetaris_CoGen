"""Original source-backed engineering issue structure, not transcript processing.

Deterministic interpretations are proposals. Edges express review order, never
inferred physical causality. No diagnostic action or executable flow is emitted.
"""
import re
from decimal import Decimal
from .assembly import canonical_hash,AssemblyPlan,AssemblyNode

UNITS={'C':'temperature','F':'temperature','V':'voltage','A':'current','W':'power','Hz':'frequency',
       'mm':'length','ms':'time','s':'time','rpm':'rotation-rate','psi':'pressure','bar':'pressure','%':'ratio'}

def build_engineering_flow(*,document_id,revision,source_sha256,spans):
    if not re.fullmatch(r'[a-f0-9]{32}',document_id) or not re.fullmatch(r'[a-f0-9]{64}',source_sha256):
        raise ValueError('Engineering issue requires exact source identity')
    if not isinstance(revision,str) or not 1<=len(revision)<=50 or not isinstance(spans,list) or not 1<=len(spans)<=5000:
        raise ValueError('Invalid engineering source envelope')
    nodes=[];limitations=[]
    for span in spans[:60]:
        text=span.get('text');locator=span.get('locator')
        if not isinstance(text,str) or not 1<=len(text)<=20000 or not isinstance(locator,str):raise ValueError('Invalid engineering span')
        lower=text.casefold();flags=[]
        if re.search(r'\b(fails?|failure|stops?|overheat|hot|vibrat\w*|noise|leak\w*|slow|broken|issue|error)\b',lower):flags.append('reported-symptom')
        if re.search(r'\b(if|when|under|during|after|before|unless)\b',lower):flags.append('operating-context-or-condition')
        if re.search(r'\b(measured|reading|observed|recorded|sensor|meter)\b',lower):flags.append('reported-observation')
        if re.search(r'\b(may|might|suspect|possibly|could be|because)\b',lower):flags.append('unverified-hypothesis')
        if text.rstrip().endswith('?') or re.search(r'\b(check|inspect|test|compare|measure)\b',lower):flags.append('proposed-check')
        if re.search(r'\b(replaced|adjusted|reset|repaired)\b',lower):flags.append('reported-action')
        if re.search(r'\b(resolved|fixed|completed|remains|persist\w*)\b',lower):flags.append('reported-outcome-unverified')
        if re.search(r"\b(no|not|never|without)\b|n['\u2019]t\b",lower):flags.append('negated')
        quantities=[]
        for match in re.finditer(r'(?<![\w.])([+-]?\d{1,28}(?:\.\d{1,18})?)\s*°?\s*(C|F|V|A|W|Hz|mm|ms|s|rpm|psi|bar|%)(?!\w)',text):
            value=Decimal(match[1])
            quantities.append(dict(raw_text=match.group(),value=str(value),unit=match[2],dimension=UNITS[match[2]],
                offset_start=match.start(),offset_end=match.end(),interpretation='source-reported-quantity',
                instrument='unknown',location='unknown',measurement_verified=False))
        if quantities:flags.append('source-reported-quantity')
        if not flags:flags=['unclassified-source-observation']
        body=dict(source_id=document_id,revision=revision,source_sha256=source_sha256,locator=locator,raw_text=text,
            categories=flags,quantities=quantities,state='candidate',confidence_probability=None,
            engineering_interpretation='Review source categories, operating conditions and measurement method before diagnosing.',
            authority_granted=False,executable=False)
        body['id']=canonical_hash(body)[:32];nodes.append(body)
    if len(spans)>60:limitations.append(f'{len(spans)-60} spans withheld by flow-node budget; narrow source scope before further assembly')
    observed=[n['id'] for n in nodes if 'reported-observation' in n['categories'] and not {'negated','proposed-check'} & set(n['categories'])]
    # Disjoint review tiers keep overlapping source categories from introducing cycles.
    hypotheses=[n['id'] for n in nodes if 'unverified-hypothesis' in n['categories'] and n['id'] not in observed]
    checks=[n['id'] for n in nodes if 'proposed-check' in n['categories'] and n['id'] not in observed+hypotheses]
    edges=[dict(source=a,target=b,relation='evidence-review-precedes-hypothesis',causality_verified=False) for a in observed for b in hypotheses if a!=b][:128]
    edges += [dict(source=a,target=b,relation='hypothesis-review-precedes-proposed-check',causality_verified=False) for a in hypotheses for b in checks if a!=b][:128]
    questions=[]
    if not observed:questions.append('What measurements or direct observations support the reported issue?')
    if any(n['quantities'] for n in nodes):questions.append('Which instrument, location, time and operating conditions produced each quantity?')
    if not checks:questions.append('Which bounded, approved check would distinguish the competing explanations?')
    if not any('reported-outcome-unverified' in n['categories'] for n in nodes):questions.append('What independent outcome evidence would demonstrate that the issue is resolved?')
    return dict(kind='engineering-issue-flow',document_id=document_id,revision=revision,source_sha256=source_sha256,
        nodes=nodes,edges=edges,open_questions=questions,limitations=limitations,
        state='candidate-and-withheld',flow_execution=False,diagnosis_verified=False,
        interpretation_policy='original-patterns/1; categories and review ordering only',receipt_sha256=canonical_hash(dict(nodes=nodes,edges=edges)))
