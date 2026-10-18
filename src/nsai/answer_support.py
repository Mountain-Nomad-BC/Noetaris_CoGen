"""Conservative source-form checks; never a general semantic or truth proof.

Accept complete source observations as attributed quotations, or the existing
unconditional temperature forms and exact conversions. Other generated claims
are withheld rather than approved from matching numbers or vocabulary alone.
"""
import re
import unicodedata
from .models import extract_claims,quantity_identity

VERSION='nsai.answer-support/2'
_CITATION=re.compile(r'\[(?:[a-f0-9]{32}|[a-f0-9]{64})\]')
_TEMP=re.compile(r'(?<![\w-])([+-]?\d+(?:\.\d+)?)\s*\u00b0?\s*([CF])\b',re.I)
_ENTITY=re.compile(r'\b[a-z]+-[a-z0-9]+\b',re.I)
_QUALIFIED=re.compile(r'(?<![\w-])(?:if|unless|when|provided|under|not|no|never|previously|formerly|historical|was|were|may|might|could|would|should|can|approximately|about|around|roughly|estimated|typical|nominal|usually|possibly|perhaps|uncertain|likely)(?![\w-])',re.I)
_PREFIX=re.compile(r'^(?:the\s+)?(?:cited\s+)?sources?\s+(?:says?|states?|reports?)\s+(?:that\s+)?',re.I)
_SAFE_MODES={'evidence-extract','citation_guard_fallback','source_support_guard_fallback'}
_VALUE_QUESTION=re.compile(r'what is (?:the )?(maximum operating temperature|operating limit) (?:of|for) ([a-z][a-z0-9_-]{1,79})\s*\??',re.I)


def _parts(text):
    # The existing extractor's observation unit is a source line. Separate its
    # supported temperature statements, without inventing generic clause rules.
    return [part.strip() for part in re.split(r'\n+|(?<=[CF])\.\s+',text) if part.strip()]


def _literal(text):
    return ' '.join(unicodedata.normalize('NFC',text).casefold().split()).rstrip(' .')


def _quantity(match):
    if len(match.group(1))>128:return None
    return quantity_identity(match.group(1)+match.group(2).upper())


def _facts(text):
    if _QUALIFIED.search(text):return []
    result=[]
    for claim in extract_claims(text.replace('\u00b0','')):
        match=_TEMP.fullmatch(claim.value)
        if match is not None:
            identity=_quantity(match)
            if identity is not None:result.append((claim.subject,claim.predicate,identity))
    return result


def assess(answer,hits,*,question=''):
    failure=dict(valid=False,policy_version=VERSION,claims=[],rendered_answer=None)
    if not isinstance(answer,str) or not 1<=len(answer)<=12000 or not isinstance(hits,list) or len(hits)>12:
        return dict(failure,reason='input-budget')
    if any(not isinstance(hit,dict) or not isinstance(hit.get('text'),str) for hit in hits):
        return dict(failure,reason='source-shape')
    if sum(len(hit['text']) for hit in hits)>64000:return dict(failure,reason='source-budget')
    rows=[(hit.get('id'),row,_facts(row)) for hit in hits for row in _parts(hit['text'])]
    statements=_parts(_CITATION.sub('',answer))
    if not statements or len(statements)>64:return dict(failure,reason='statement-budget')
    query_entities=set(_ENTITY.findall(question.casefold()))
    proofs=[];rendered=[];covered=set()
    for index,raw in enumerate(statements):
        statement=_PREFIX.sub('',raw).strip()
        wanted=_facts(statement)
        matches=[];method=None;rendered_text=raw
        if wanted:
            for wanted_fact in wanted:
                entity=set(_ENTITY.findall(wanted_fact[0]))
                if query_entities and (not entity or not entity<=query_entities):break
                found=[row for row in rows if wanted_fact in row[2]]
                if not found:break
                matches.extend(found)
            else:method='unconditional-temperature-form'
        if method is None:
            quantity=_TEMP.fullmatch(statement.rstrip(' .'))
            if quantity is not None:
                identity=_quantity(quantity)
                question_form=_VALUE_QUESTION.fullmatch(question.strip()) if question else None
                eligible=[(row,fact) for row in rows for fact in row[2]
                    if (not query_entities or set(_ENTITY.findall(fact[0]))==query_entities)
                    and (not question or (question_form is not None
                        and fact[0]==question_form[2].casefold() and fact[1]==question_form[1].casefold()))]
                values={fact[2] for row,fact in eligible}
                if identity is not None and len(query_entities)<=1 and len(values)==1 and identity in values:
                    matches=[row for row,fact in eligible if fact[2]==identity]
                    method='unconditional-temperature-value'
        if method is None:
            matches=[row for row in rows if _literal(row[1])==_literal(statement)
                and (not query_entities or query_entities<=set(_ENTITY.findall(row[1].casefold())))]
            if matches:
                method='source-quotation'
                rendered_text='The cited excerpt states: "'+matches[0][1]+'"'
        if method is None:return dict(failure,reason='unsupported-statement',unsupported_statement_index=index)
        ids=sorted({row[0] for row in matches if isinstance(row[0],str)})
        proofs.append(dict(statement_index=index,method=method,citation_ids=ids))
        rendered.append(rendered_text)
        if method=='unconditional-temperature-value':
            covered.update(query_entities)
        else:covered.update(_ENTITY.findall(statement.casefold()))
    if query_entities and not query_entities<=covered:
        return dict(failure,reason='question-entities-not-covered')
    return dict(valid=True,policy_version=VERSION,claims=proofs,rendered_answer='\n'.join(rendered),
        reason=None,limitation='Source quotations and narrow unconditional temperature forms; no general semantic or factual verification')


def response_is_current(response):
    if not isinstance(response,dict):return False
    if response.get('mode') in _SAFE_MODES:return True
    return response.get('mode')=='model_unverified' and response.get('support_policy_version')==VERSION


def require_current_response(response):
    if not response_is_current(response):
        raise ValueError('Stored completion requires current support validation; send the question as a new request')
    return response
