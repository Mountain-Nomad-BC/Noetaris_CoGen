"""Fail-closed admission of one scoped receipt against an explicit immutable run identity."""
from datetime import datetime,timezone
import hashlib
import re

IDENTITY_FIELDS=('run_id','source_sha256','image_digest','effective_config_sha256','producer_sha256')

def admit_receipt(receipt,evidence,expected,*,now=None,max_age_seconds=86400):
    errors=[]
    if not isinstance(receipt,dict) or not isinstance(expected,dict):
        return {'status':'UNVERIFIED','errors':['Invalid receipt identity envelope']}
    if not isinstance(evidence,bytes) or len(evidence)>16*1024*1024:
        return {'status':'UNVERIFIED','errors':['Missing or oversized evidence bytes']}
    if type(max_age_seconds) is not int or not 1<=max_age_seconds<=86400:
        raise ValueError('Invalid receipt age policy')
    for key in IDENTITY_FIELDS:
        value=expected.get(key)
        valid=isinstance(value,str) and bool(value)
        if key!='run_id':valid=valid and bool(re.fullmatch(r'(?:sha256:)?[a-f0-9]{64}',value))
        elif valid:valid=bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{7,127}',value))
        if not valid or receipt.get(key)!=value:errors.append(key+': missing, invalid or mismatched binding')
    scope=receipt.get('scope')
    if not isinstance(scope,str) or scope not in {'static','runtime','quality','recovery'}:
        errors.append('Missing supported qualification scope')
    if receipt.get('status')!='PASS' or type(receipt.get('exit_code')) is not int or receipt['exit_code']!=0:
        errors.append('Missing successful scoped verdict')
    if receipt.get('evidence_sha256')!=hashlib.sha256(evidence).hexdigest():errors.append('Evidence digest mismatch')
    try:
        captured=datetime.fromisoformat(receipt['captured_at'].replace('Z','+00:00'))
        current=now or datetime.now(timezone.utc)
        if captured.tzinfo is None or current.tzinfo is None:raise ValueError('Naive time')
        age=(current-captured).total_seconds()
        if not 0<=age<=max_age_seconds:errors.append('Stale or future capture time')
    except (ValueError,TypeError,KeyError,AttributeError):errors.append('Missing valid capture time')
    return {'status':'UNVERIFIED' if errors else 'PASS_SCOPED','errors':errors,
        'scope':receipt.get('scope'),'release_approval':False,'certification':False}
