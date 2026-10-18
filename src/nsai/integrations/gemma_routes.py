"""Server-side candidate ordering, separate from dispatch and admission.

AMD elevation is preferred when requested. External routes require an explicit
export decision; free OpenRouter identities must never become priced aliases.
This module alone does not commission a tokenizer adapter or remote execution.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Route:
    id: str
    model: str
    remote: bool
    funding: str


ROUTES = {
    'cpu': Route('cpu','google/gemma-3-1b-it',False,'local'),
    'amd': Route('amd','Gemma-4-31B-IT',True,'free'),
    'research': Route('research','google/gemma-4-31b-it:free',True,'free'),
    'fallback': Route('fallback','google/gemma-4-26b-a4b-it:free',True,'free'),
}


def candidates(purpose, *, export_authorized=False, available=(), cooldowns=None, now=0):
    if purpose not in {'default','cpu','elevation','research'}:
        raise ValueError('Unknown inference purpose')
    if type(export_authorized) is not bool:
        raise ValueError('Export decision must be boolean')
    if type(now) not in (int,float) or not math.isfinite(now) or now<0:
        raise ValueError('Invalid monotonic clock')
    if not isinstance(available,(list,tuple,set,frozenset)) or any(r not in ROUTES for r in available):
        raise ValueError('Unknown available route')
    cooldowns=cooldowns or {}
    if not isinstance(cooldowns,dict) or any(k not in ROUTES or type(v) not in (int,float) or not math.isfinite(v) or v<0 for k,v in cooldowns.items()):
        raise ValueError('Invalid route cooldown')
    order={'default':['amd','research','fallback','cpu'], 'cpu':['cpu'], 'elevation':['amd','cpu','fallback'],
           'research':['amd','research','fallback','cpu']}[purpose]
    return [ROUTES[key] for key in order if key in available and
            (not ROUTES[key].remote or export_authorized) and cooldowns.get(key,0)<=now]


def free_catalog_route(route, catalog):
    """Require current catalog metadata, exact model ID and zero listed charges."""
    from decimal import Decimal,InvalidOperation
    if route not in {'research','fallback'} or not isinstance(catalog,list):
        raise ValueError('Invalid free-provider catalog selection')
    matching=[item for item in catalog if isinstance(item,dict) and item.get('id')==ROUTES[route].model]
    if len(matching)!=1:
        raise ValueError('Exact free Gemma model not available')
    pricing=matching[0].get('pricing')
    if not isinstance(pricing,dict) or not {'prompt','completion'}<=pricing.keys():
        raise ValueError('Unknown provider pricing')
    try:
        # Reject every listed nonzero price, including extra request/image fees.
        if any(not isinstance(v,str) or not Decimal(v).is_finite() or Decimal(v)!=0 for v in pricing.values()):
            raise ValueError('Priced provider route denied')
    except (InvalidOperation,TypeError):
        raise ValueError('Invalid provider pricing') from None
    return ROUTES[route]
