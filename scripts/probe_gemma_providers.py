"""Bounded partner discovery and optional synthetic-only Gemma smoke checks.

Never loads document/corpus data, starts GPU instances or executes workflows.
Keys are read from ignored server-side files; errors and headers are not logged.
"""
import argparse
import asyncio
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import httpx
from nsai.inference import _bounded_json
from nsai.integrations.gemma_routes import free_catalog_route
from nsai.store import _secret


async def probe(smoke=False):
    report=dict(captured_at=datetime.now(timezone.utc).isoformat(),
        scope='Provider discovery and synthetic READY smoke only; not application routing or dedicated AMD/Evolus qualification',
        private_sources_sent=False,checks=[])
    async with httpx.AsyncClient(timeout=60,follow_redirects=False,trust_env=False) as client:
        for name,base,models in [
            ('amd','https://developer.amd.com.cn/radeon/api/v1',['Gemma-4-31B-IT']),
            ('openrouter','https://openrouter.ai/api/v1',['google/gemma-4-31b-it:free','google/gemma-4-26b-a4b-it:free']),
        ]:
            try:key=_secret(str(ROOT/'secrets'/(name+'_api_key.txt')))
            except (OSError,RuntimeError,UnicodeError):
                report['checks'].append(dict(provider=name,status='credential-unavailable'));continue
            headers={'Authorization':'Bearer '+key}
            try:
                catalog=await _bounded_json(client,'GET',base+'/models',headers=headers,maximum=4*1024*1024,deadline=20)
                rows=catalog.get('data')
                if not isinstance(rows,list):raise ValueError('Invalid model catalog')
                report['checks'].append(dict(provider=name,catalog_reachable=True,models_present=[model for model in models if any(isinstance(r,dict) and r.get('id')==model for r in rows)]))
            except Exception as error:
                report['checks'].append(dict(provider=name,status='catalog-unavailable',failure_type=type(error).__name__));continue
            if not smoke:continue
            for index,model in enumerate(models):
                if not any(isinstance(r,dict) and r.get('id')==model for r in rows):continue
                payload=dict(model=model,messages=[dict(role='user',content='Reply with the single word READY.')],
                             max_tokens=64,temperature=0,stream=False)
                if name=='openrouter':
                    try:free_catalog_route('research' if index==0 else 'fallback',rows)
                    except ValueError:
                        report['checks'].append(dict(provider=name,model=model,status='free-pricing-not-confirmed'));continue
                    payload['provider']={'max_price':{'prompt':0,'completion':0},'allow_fallbacks':False}
                    payload['reasoning']={'enabled':False}
                started=time.monotonic()
                try:
                    result=await _bounded_json(client,'POST',base+'/chat/completions',headers=headers,payload=payload,maximum=128000,deadline=60)
                    content=result['choices'][0]['message']['content']
                    usage=result.get('usage',{})
                    if not isinstance(usage,dict):usage={}
                    report['checks'].append(dict(provider=name,model=model,status='returned',
                        ready=isinstance(content,str) and content.strip().upper().rstrip('.!')=='READY',
                        latency_seconds=round(time.monotonic()-started,3),
                        usage={k:usage[k] for k in ['prompt_tokens','completion_tokens','total_tokens','cost'] if k in usage}))
                except httpx.HTTPStatusError as error:
                    report['checks'].append(dict(provider=name,model=model,status='rate-limited' if error.response.status_code==429 else 'http-error',http_status=error.response.status_code))
                except Exception as error:
                    report['checks'].append(dict(provider=name,model=model,status='unavailable',failure_type=type(error).__name__))
    folder=ROOT/'state/integration/provider-discovery';folder.mkdir(parents=True,exist_ok=True)
    path=folder/('probe-'+uuid4().hex+'.json')
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke',action='store_true',help='One bounded synthetic call per model; AMD account allowance applies')
    args=parser.parse_args()
    asyncio.run(probe(args.smoke))
