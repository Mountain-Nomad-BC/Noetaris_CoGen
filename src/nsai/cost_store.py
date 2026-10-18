"""Typed cost ledger operations; providers must reserve before dispatch, then reconcile."""
import re
from . import store
from .contracts.evidence import canonical_hash


def reserve(*,request_id,provider,account,estimated_units,input_token_ceiling=0,output_token_ceiling=0):
    if isinstance(account,str) and account.startswith('cash-'):
        raise PermissionError('Cash dispatch is prohibited; cost governance is demonstration only')
    identity=store.request_identity()
    if identity is None or identity.get('role')!='operator' or identity.get('identity_kind')=='source-job':
        raise PermissionError('Cost reservation requires an authenticated operator')
    if not isinstance(request_id,str) or re.fullmatch('[a-f0-9]{32}',request_id) is None:
        raise ValueError('Cost reservation requires a stable request identity')
    if not isinstance(provider,str) or re.fullmatch('[a-z][a-z0-9_-]{0,63}',provider) is None:
        raise ValueError('Invalid provider identity')
    if account not in {'cash-cloud','cash-api','cash-contingency','amd-credits','evolus-credits'}:
        raise ValueError('Invalid exposure account')
    for value,maximum in [(estimated_units,1000000000000),(input_token_ceiling,1000000000),(output_token_ceiling,1000000000)]:
        if type(value) is not int or not 0<=value<=maximum:raise ValueError('Invalid integer reservation')
    # Do not put prices/ceilings in the key: changed retry estimates must conflict.
    key=canonical_hash(dict(actor=identity['actor'],request_id=request_id,provider=provider,account=account))
    with store.connect() as conn:
        return conn.execute('SELECT nsai_reserve_cost(%s,%s,%s,%s,%s,%s)',
            (key,account,provider,estimated_units,input_token_ceiling,output_token_ceiling)).fetchone()[0]


def settle(reservation_id,*,actual_units,input_tokens=0,output_tokens=0):
    identity=store.request_identity()
    if identity is None or identity.get('role')!='operator' or identity.get('identity_kind')=='source-job':
        raise PermissionError('Cost settlement requires an authenticated operator')
    if not isinstance(reservation_id,str) or re.fullmatch('[a-f0-9]{64}',reservation_id) is None:
        raise ValueError('Invalid reservation identity')
    for value,maximum in [(actual_units,1000000000000),(input_tokens,1000000000),(output_tokens,1000000000)]:
        if type(value) is not int or not 0<=value<=maximum:raise ValueError('Invalid settlement units')
    with store.connect() as conn:
        return conn.execute('SELECT nsai_settle_cost(%s,%s,%s,%s)',
            (reservation_id,actual_units,input_tokens,output_tokens)).fetchone()[0]


def status():
    with store.connect() as conn:return conn.execute('SELECT nsai_cost_status()').fetchone()[0]


def demonstration():
    return dict(mode='demonstration-only',cash_dispatch_enabled=False,
        title='Cost governance demonstration',
        explanation='Illustrative settings only. No money is allocated, charged or authorized.',
        example=dict(currency='USD',maximum='20.00',cloud='5.00',api_voice='10.00',contingency='5.00'),
        actual_usage_governance='Request rates, generation allowances and concurrency limits',
        credit_accounts=['amd-credits','evolus-credits'])


def admin_overview():
    """Read-only governance projection; cash balances never imply dispatch authority."""
    from .operational_policy import operational_policy
    limits=operational_policy()
    ledger=status()
    return dict(**demonstration(),credit_ledger=dict(
        accounts=[row for row in ledger['accounts'] if row['name'] in {'amd-credits','evolus-credits'}],
        unknown_outcomes_remain_reserved=ledger['unknown_outcomes_remain_reserved'],
        provider_billing_cap_guaranteed=ledger['provider_billing_cap_guaranteed']),
        limits={key:getattr(limits,key) for key in ('concurrent_users','requests_per_minute',
            'generations_per_user','ingestions_per_user','generations_per_day','gpu_jobs','gpu_queue')},
        local_token_ceiling=None,
        generation_accounting='Only AI generations; retrieval, authentication, streaming chunks and ASR partials are excluded.',
        configuration_source='Operator environment; changes require validated deployment configuration.')
