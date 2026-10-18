"""Operator configuration and integer cost estimates; never client-selected authority."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
import os
import re


def microusd(value):
    if not isinstance(value,str) or re.fullmatch(r'(?:0|[1-9]\d{0,8})(?:\.\d{1,6})?',value) is None:
        raise ValueError('Money requires a nonnegative decimal with at most six places')
    return int(Decimal(value)*1000000)


@dataclass(frozen=True)
class OperationalPolicy:
    concurrent_users:int=5
    requests_per_minute:int=120
    generations_per_user:int=1
    ingestions_per_user:int=1
    generations_per_day:int=20
    gpu_jobs:int=1
    gpu_queue:int=10
    cash_microusd:int=20000000
    cloud_microusd:int=5000000
    api_microusd:int=10000000
    contingency_microusd:int=5000000
    amd_credit_limit:int=0
    evolus_credit_limit:int=0
    local_token_ceiling:None=None


def operational_policy(environment=None):
    env=os.environ if environment is None else environment
    defaults=OperationalPolicy();values={}
    integer_fields={
        'concurrent_users':('NSAI_CONCURRENT_USERS',1000),
        'requests_per_minute':('NSAI_REQUESTS_PER_MINUTE',10000),
        'generations_per_user':('NSAI_GENERATIONS_PER_USER',100),
        'ingestions_per_user':('NSAI_INGESTIONS_PER_USER',100),
        'generations_per_day':('NSAI_GENERATIONS_PER_DAY',100000),
        'gpu_jobs':('NSAI_GPU_ACTIVE_JOBS',100),
        'gpu_queue':('NSAI_GPU_QUEUE_SIZE',1000),
    }
    for field,(name,maximum) in integer_fields.items():
        raw=env.get(name,str(getattr(defaults,field)))
        if not isinstance(raw,str) or re.fullmatch(r'[1-9]\d{0,5}',raw) is None or int(raw)>maximum:
            raise ValueError('Invalid operator limit: '+name)
        values[field]=int(raw)
    for field,name in [('cash_microusd','NSAI_CASH_BUDGET_USD'),('cloud_microusd','NSAI_CLOUD_ALLOCATION_USD'),
                       ('api_microusd','NSAI_API_ALLOCATION_USD'),('contingency_microusd','NSAI_CONTINGENCY_USD')]:
        values[field]=microusd(env[name]) if name in env else getattr(defaults,field)
    for field,name in [('amd_credit_limit','NSAI_AMD_CREDIT_LIMIT'),('evolus_credit_limit','NSAI_EVOLUS_CREDIT_LIMIT')]:
        raw=env.get(name,'0')
        if not isinstance(raw,str) or re.fullmatch(r'(?:0|[1-9]\d{0,14})',raw) is None:
            raise ValueError('Invalid provider credit allowance')
        values[field]=int(raw)
    if sum(values[field] for field in ('cloud_microusd','api_microusd','contingency_microusd'))>values['cash_microusd']:
        raise ValueError('Cash allocations exceed maximum exposure')
    return OperationalPolicy(**values)


def is_ai_generation(kind):
    return kind=='generation'


def estimate_token_cost(input_tokens,output_tokens,input_usd_per_million,output_usd_per_million):
    for count in (input_tokens,output_tokens):
        if type(count) is not int or not 0<=count<=1000000000:
            raise ValueError('Invalid token estimate')
    for price in (input_usd_per_million,output_usd_per_million):
        if not isinstance(price,Decimal) or not price.is_finite() or not 0<=price<=Decimal('1000000'):
            raise ValueError('Prices require bounded nonnegative Decimal values')
    return int((input_tokens*input_usd_per_million+output_tokens*output_usd_per_million).to_integral_value(rounding=ROUND_CEILING))
