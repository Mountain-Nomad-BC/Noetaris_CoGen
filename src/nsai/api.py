from __future__ import annotations
import asyncio
import base64
from collections import deque
import os
from pathlib import Path
import time
import re
from datetime import datetime,timezone
from contextlib import asynccontextmanager
from typing import Annotated, Literal
import httpx
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, Path as APIPath
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict, model_validator
from . import store, workflow_store as workflows
from .upload_limits import ACTIVE as UPLOAD_LIMITS
from .inference import generate_from_sources, model_status,prepare_source_request,admit_source_request
from .models import conflict_groups
from .operation_admission import guarded as admitted_operation
from .citation_anchors import citation_from_hit
from .retrieval.library import retrieve as library_retrieve
from .source_dependencies import stamp_result
from .security import principal, resolve_principal, require, PolicyUpdate, security_status
from .table_analysis import TableAnalysisInput

@asynccontextmanager
async def application_lifespan(app):
    from .operational_policy import operational_policy
    operational_policy()  # Reject ambiguous or overallocated operator settings.
    from .shared_rate_limit import validate_runtime
    validate_runtime()
    from .oauth_http import validate_runtime as validate_oauth
    validate_oauth()
    setting=os.getenv('NSAI_INDEX_WORKER_ENABLED','false')
    if setting not in {'true','false'}:raise ValueError('Invalid index worker activation setting')
    tasks=[]
    if setting=='true':
        from . import semantic_jobs
        semantic_jobs.encoder_settings()
        for _ in range(semantic_jobs.worker_concurrency()):
            tasks.append(asyncio.create_task(semantic_jobs.worker_loop()))
    try:yield
    finally:
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)


app = FastAPI(title='NSAI evidence workspace',docs_url=None,redoc_url=None,openapi_url=None,lifespan=application_lifespan)
ASSET_ROOT = Path(__file__).resolve().parents[2] / 'assets'
PUBLIC_ASSETS=frozenset({'app.js','index.css','index.html','pdf-quotes.mjs','pdf-canvas.mjs','pdfjs/pdf.mjs',
    'pdfjs/pdf.worker.mjs','pdfjs/license','pdfjs/provenance.json',
    'pdfjs/standard_fonts/provenance.json','pdfjs/standard_fonts/license_foxit',
    'pdfjs/standard_fonts/license_liberation','pdfjs/standard_fonts/foxitdingbats.pfb',
    'pdfjs/standard_fonts/foxitfixed.pfb','pdfjs/standard_fonts/foxitfixedbold.pfb',
    'pdfjs/standard_fonts/foxitfixedbolditalic.pfb','pdfjs/standard_fonts/foxitfixeditalic.pfb',
    'pdfjs/standard_fonts/foxitserif.pfb','pdfjs/standard_fonts/foxitserifbold.pfb',
    'pdfjs/standard_fonts/foxitserifbolditalic.pfb','pdfjs/standard_fonts/foxitserifitalic.pfb',
    'pdfjs/standard_fonts/foxitsymbol.pfb','pdfjs/standard_fonts/liberationsans-bold.ttf',
    'pdfjs/standard_fonts/liberationsans-bolditalic.ttf','pdfjs/standard_fonts/liberationsans-italic.ttf',
    'pdfjs/standard_fonts/liberationsans-regular.ttf'})

class PublicAssets(StaticFiles):
    async def get_response(self,path,scope):
        # StaticFiles has already normalized separators/dot segments here.
        # Admit exact public resources rather than comparing the raw request URL.
        if path.replace('\\','/').casefold() not in PUBLIC_ASSETS:
            return JSONResponse({'detail':'Not found'},404)
        return await super().get_response(path,scope)

app.mount('/assets',PublicAssets(directory=str(ASSET_ROOT)),name='assets')
auth = principal
inference_lock = asyncio.Lock()
rate_window = deque()

def browser_headers(response):
    response.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY',
        'Referrer-Policy':'no-referrer','Cache-Control':'no-store',
        'Content-Security-Policy':"default-src 'none'; script-src 'self'; worker-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"})
    return response


def reauthorize_response_sources(sources):
    if sources:
        from .source_dependencies import validate_sources
        with store.connect() as conn:validate_sources(conn,sources)


async def protect_private_response(response,authorization,identity):
    """Buffer bounded private output, then check current identity and all inputs.

    No streaming private bytes are released before the final policy transaction
    commits. That final committed check is the authorization linearization point.
    """
    parts=[];size=0
    try:
        async with asyncio.timeout(15):
            async for part in response.body_iterator:
                size+=len(part)
                if size>32*1024*1024:raise ValueError('Private response budget exceeded')
                parts.append(part)
        current=await asyncio.to_thread(resolve_principal,authorization)
        if current!=identity:
            return JSONResponse({'detail':'Authentication changed; retry'},401)
        sources=store.request_source_dependencies()
        await asyncio.to_thread(reauthorize_response_sources,sources)
        return Response(b''.join(parts),status_code=response.status_code,
                        headers=dict(response.headers),background=response.background)
    except HTTPException as error:
        return JSONResponse({'detail':error.detail},error.status_code,headers=error.headers)
    except LookupError:
        return JSONResponse({'detail':'Source unavailable'},404)
    except Exception:
        return JSONResponse({'detail':'Private response unavailable'},503)

@app.middleware('http')
async def protections(request, call_next):
    identity=None
    from .oauth_http import request_credential,protect_mutation
    authorization=request_credential(request)
    if request.url.path.rstrip('/')=='/assets/verification.json':
        return browser_headers(JSONResponse({'detail':'Not found'},404))
    if os.getenv('NSAI_CENTRAL_SECURITY_ENABLED','false').lower() != 'false':
        return browser_headers(JSONResponse({'detail':'Central integration is not admitted; fail closed'},503))
    if request.url.path.startswith('/v1/'):
        try:identity=principal(authorization)
        except HTTPException as error:
            return browser_headers(JSONResponse({'detail':error.detail},error.status_code,headers=error.headers))
        except Exception:return browser_headers(JSONResponse({'detail':'Authentication unavailable'},503))
        from .rate_limit import admit
        from .operational_policy import operational_policy
        try:request_limit=operational_policy().requests_per_minute
        except ValueError:
            return browser_headers(JSONResponse({'detail':'Operational policy unavailable'},503))
        from . import shared_rate_limit
        try:
            allowed=(await asyncio.to_thread(shared_rate_limit.admit,identity['actor'],request_limit)
                     if shared_rate_limit.backend()=='redis' else
                     admit(rate_window,identity['actor'],time.monotonic(),per_principal=request_limit))
        except (RuntimeError,ValueError,OSError,KeyError):
            return browser_headers(JSONResponse({'detail':'Request coordination unavailable'},503))
        if not allowed:
            return browser_headers(JSONResponse({'detail':'Local request rate limit exceeded'},429,headers={'Retry-After':'60'}))
        expected=request.headers.get('X-NSAI-Expected-Actor')
        if expected is not None and expected!=identity['actor']:
            return browser_headers(JSONResponse({'detail':'Authentication changed; reload the workspace'},401))
        from .oauth_accounts import SessionCredential
        if isinstance(authorization,SessionCredential) and request.method not in {'GET','HEAD','OPTIONS'}:
            try:await protect_mutation(request,authorization)
            except HTTPException as error:
                return browser_headers(JSONResponse({'detail':error.detail},error.status_code,headers=error.headers))
        if identity.get('identity_kind')=='local-user' and request.url.path not in {'/v1/capabilities','/v1/model/status'}:
            # Distinct user authentication must not inherit the legacy project's
            # shared-content access while private-source enforcement is staged.
            return browser_headers(JSONResponse({'detail':'Private document access integration is not yet admitted'},503))
    if request.method in {'POST','PUT','PATCH'}:
        parts, total = [], 0
        body_limit=2_200_000
        if request.url.path.startswith('/auth/'):body_limit=4096
        if request.method=='POST' and request.url.path=='/v1/files' and request.headers.get('content-type','').split(';')[0]=='multipart/form-data':
            body_limit=UPLOAD_LIMITS.max_bytes+65536
        try:
            async with asyncio.timeout(15):
                async for part in request.stream():
                    total += len(part)
                    if total > body_limit:
                        return browser_headers(JSONResponse({'detail':'Request exceeds source budget'},413))
                    parts.append(part)
        except TimeoutError:return browser_headers(JSONResponse({'detail':'Request body deadline exceeded'},408))
        request._body = b''.join(parts)
        if request.headers.get('content-type','').split(';')[0]=='application/json':
            from .assembly import strict_json
            try:strict_json(request._body,max_bytes=2_200_000,max_depth=32,max_items=100000)
            except ValueError:return browser_headers(JSONResponse({'detail':'Invalid or ambiguous JSON request'},422))
    try:
        if identity is not None:
            with store.identity_context(identity):
                response=await call_next(request)
                if identity.get('identity_kind')=='local-user':
                    response=await protect_private_response(response,authorization,identity)
                if response.status_code<400:response.headers['X-NSAI-Actor']=identity['actor']
        else:response=await call_next(request)
    except Exception:return browser_headers(JSONResponse({'detail':'Service unavailable'},503))
    return browser_headers(response)

from . import oauth_http
app.add_middleware(oauth_http.BrowserSessions)
from .deployment_cors import DeploymentCORS
app.add_middleware(DeploymentCORS)
app.include_router(oauth_http.router)

class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
class DocumentInput(StrictInput):
    title: str = Field(min_length=1,max_length=180)
    text: str = Field(min_length=1,max_length=20000)
    version: str = Field(default='1',min_length=1,max_length=50)
    upload_ack: str | None = Field(default=None,max_length=64)
class Question(StrictInput):
    question: str = Field(min_length=1,max_length=1000)
    session_id: str | None = Field(default=None,pattern=r'^[a-f0-9]{32}$')
    request_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{32}$')
    document_ids:list[Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]]=Field(default_factory=list,max_length=20)
    revision:str|None=Field(default=None,min_length=1,max_length=50)
    pages:list[Annotated[int,Field(ge=1,le=1000,strict=True)]]=Field(default_factory=list,max_length=100)
    @model_validator(mode='after')
    def validate_source_scope(self):
        if (self.revision is not None or self.pages) and not self.document_ids:
            raise ValueError('Revision/page scope requires selected source IDs')
        if len(set(self.document_ids)) != len(self.document_ids):
            raise ValueError('Select distinct source IDs')
        return self
class Review(StrictInput):
    decision: Literal['accept','reject','contest']
    expected_revision: int = Field(ge=1)
    rationale: str = Field(min_length=10,max_length=2000)
    expected_context: str | None = Field(default=None,pattern=r'^[a-f0-9]{64}$')
class Reflection(StrictInput):
    source_claim_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    reflection: str = Field(min_length=10,max_length=2000)
class LearningReview(StrictInput):
    expected_revision: int = Field(ge=1)
    approve: bool
    rationale: str | None = Field(default=None,min_length=10,max_length=2000)

class IssueInput(StrictInput):
    document_id:str=Field(pattern=r'^[a-f0-9]{32}$')

class DataProposal(StrictInput):
    document_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    capability:str=Field(min_length=1,max_length=64)
    data:dict

class GovernedReview(StrictInput):
    decision:Literal['reviewed','rejected']
    rationale:str=Field(min_length=10,max_length=2000)

class ActionApproval(StrictInput):
    approve:bool=Field(strict=True)

class SemanticInput(StrictInput):
    vector:list[float]=Field(min_length=384,max_length=384)
    model_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    document_ids:list[Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]]=Field(min_length=1,max_length=20)
    limit:int=Field(default=12,ge=1,le=20)
    include_supplements:bool=Field(default=False,strict=True)

class EmbeddingInput(StrictInput):
    vectors:dict
    model_identity:dict
    coverage:dict


class SourceShare(StrictInput):
    expected_epoch:int=Field(ge=1,le=9223372036854775806,strict=True)
    subject_kind:Literal['user','group']
    subject_id:str=Field(min_length=1,max_length=128)
    expires_at:datetime|None=None
    revoke:bool=Field(default=False,strict=True)
    @model_validator(mode='after')
    def validate_target(self):
        pattern=r'^local-user-[a-z][a-z0-9_-]{0,63}$' if self.subject_kind=='user' else r'^[a-z][a-z0-9_-]{0,63}$'
        if not re.fullmatch(pattern,self.subject_id):raise ValueError('Invalid sharing target')
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
                raise ValueError('Expiry requires an explicit timezone')
            if self.expires_at<=datetime.now(timezone.utc):raise ValueError('Expiry must be in the future')
        return self


class IndexRetry(StrictInput):
    expected_epoch:int=Field(ge=1,le=9223372036854775806,strict=True)


class IndexPriority(IndexRetry):
    priority:int=Field(ge=0,le=9,strict=True)

def translate_error(error):
    if getattr(error,'sqlstate',None)=='42501':
        raise HTTPException(404,'Source unavailable') from None
    if getattr(error,'sqlstate',None)=='40001':
        raise HTTPException(409,'State changed; reload and retry') from None
    if getattr(error,'sqlstate',None)=='54000':
        raise HTTPException(409,'Workspace capacity reached; contact the local administrator') from None
    if isinstance(error,PermissionError): code=403
    elif isinstance(error,LookupError): code=404
    elif isinstance(error,ValueError): code=409
    else: code=503
    raise HTTPException(code,str(error) if code != 503 else 'Service unavailable') from None

@app.get('/healthz')
def health(): return {'status':'alive','component':'api'}
@app.get('/readyz')
def ready():
    try:
        with store.connect() as conn:
            from .schema_contract import verify_database_contract
            verify_database_contract(conn)
            conn.execute('SELECT 1 FROM local_policy')
        return {'status':'ready','database':'reachable','schema':'verified'}
    except Exception:
        raise HTTPException(503,'Database unavailable, migrations pending, or schema contract failed') from None
@app.get('/')
def ui(): return FileResponse(ASSET_ROOT/'index.html')
@app.get('/v1/capabilities')
def capabilities(identity=Depends(principal)):
    from .capabilities import registry
    return dict(identity=identity,content_access=dict(admitted=identity.get('identity_kind')!='local-user',
        reason='Private document access awaits independent authorization acceptance' if identity.get('identity_kind')=='local-user' else None),
        upload_limits=UPLOAD_LIMITS.metadata(),items=registry(bool(os.getenv('NSAI_OCR_URL'))),ingestion='bounded TXT/MD/CSV/TSV/JSON/XLSX/text-PDF + isolated parser + durable source-bound indexing queue',
        indexing=dict(configured=os.getenv('NSAI_INDEX_WORKER_ENABLED','false')=='true',
                      publication='Validated generation commits atomically; queued/failed sources are not searchable'),
        retrieval='Authorized library lexical + natural-language pretrained semantic rank fusion when the isolated encoder is configured; explicit scope is preserved',
        knowledge='candidate + independent human-reviewed projection',
        memory='original NSAI bounded query-plan and source envelope; candidate-only writeback',
        remy='architecture reference only; independently implemented PDF workspace',local_inference='qualified llama.cpp CPU adapter; others unqualified',
        amd_inference='deferred; not commissioned',pdf_viewer='private bundled PDF.js worker; no active actions',
        learning='source-backed proposals only; no weight training',skill_execution='disabled')
@app.get('/v1/model/status')
async def model_readiness(identity=Depends(require('read'))): return await model_status()
@app.get('/v1/integrations/status')
def integration_configuration(identity=Depends(require('read'))):
    from .integrations.configuration import integration_setup
    return integration_setup()
def require_upload_acknowledgment(value):
    selected=os.getenv('NSAI_PUBLIC_DEMO','false')
    if selected not in {'true','false'}:raise HTTPException(503,'Invalid public demonstration configuration')
    if selected=='true' and value!='public-demo-2026-10-17':
        raise HTTPException(428,'Acknowledge the adult public-document experimental-use restrictions before uploading')


@app.post('/v1/documents')
@admitted_operation('ingestion')
def ingest(payload:DocumentInput,identity=Depends(require('ingest'))):
    require_upload_acknowledgment(payload.upload_ack)
    if len(payload.text)>int(os.getenv('NSAI_MAX_INPUT_CHARS','20000')): raise HTTPException(413,'Input limit exceeded')
    try: return store.store_document(payload.title,payload.text,payload.version,identity['actor'])
    except Exception as error: translate_error(error)
@app.post('/v1/files')
@admitted_operation('ingestion')
async def upload(file:Annotated[UploadFile,File()],version:Annotated[str,Form(min_length=1,max_length=50)]='1',upload_ack:Annotated[str|None,Form(max_length=64)]=None,identity=Depends(require('ingest'))):
    require_upload_acknowledgment(upload_ack)
    try:
        data = await file.read(UPLOAD_LIMITS.max_bytes+1)
        if not data or len(data)>UPLOAD_LIMITS.max_bytes: raise HTTPException(413,f'File must be nonempty and at most {UPLOAD_LIMITS.max_bytes // (1024*1024)} MiB')
        name = file.filename or 'source.txt'
        token = store._secret(os.environ['NSAI_PARSER_TOKEN_FILE'])
        endpoint=os.environ['NSAI_PARSER_URL']
        if endpoint!='http://parser:8788':raise ValueError('Parser endpoint is not admitted')
        from .inference import _bounded_json
        async with httpx.AsyncClient(timeout=25,follow_redirects=False,trust_env=False) as client:
            try:result=await _bounded_json(client,'POST',endpoint+'/parse',headers={'Authorization':'Bearer '+token},payload=dict(filename=name,data=base64.b64encode(data).decode()),maximum=16*1024*1024,deadline=25)
            except (httpx.HTTPError,ValueError,TimeoutError):raise HTTPException(422,'Parser rejected source or exceeded limits') from None
        from .ingestion import validate_parsed_source
        parsed=validate_parsed_source(data,result)
        if parsed['media_type']=='application/pdf' and any(p['status']=='ocr_required' for p in parsed['pages']) and os.getenv('NSAI_OCR_URL'):
            endpoint=os.environ['NSAI_OCR_URL']
            if endpoint!='http://ocr:8091':raise ValueError('OCR endpoint is not admitted')
            token=store._secret(os.environ['NSAI_OCR_TOKEN_FILE'])
            from .inference import _bounded_json
            async with httpx.AsyncClient(timeout=130,follow_redirects=False,trust_env=False) as client:
                parsed=await _bounded_json(client,'POST',endpoint+'/ocr',headers={'Authorization':'Bearer '+token},
                    payload=dict(filename=name,data=base64.b64encode(data).decode(),language='eng'),maximum=16*1024*1024)
            parsed=validate_parsed_source(data,parsed)
        return await asyncio.to_thread(workflows.persist_source,name,version,data,parsed,identity['actor'])
    except HTTPException: raise
    except Exception as error: translate_error(error)
    finally: await file.close()
@app.get('/v1/documents')
def documents(limit:Annotated[int,Query(ge=1,le=100)]=25,
              cursor:Annotated[str|None,Query(max_length=512)]=None,
              q:Annotated[str|None,Query(max_length=200)]=None,identity=Depends(require('read'))):
    from .library_store import page
    try:return page(limit=limit,cursor=cursor,query=q)
    except ValueError as error:raise HTTPException(400,str(error)) from None
    except Exception as error:translate_error(error)

@app.get('/v1/knowledge/{document_id}')
def research_knowledge(document_id:str,identity=Depends(require('read'))):
    from . import research_store
    from .semantic_jobs import require_readable_index
    try:
        require_readable_index(document_id)
        return research_store.get(document_id)
    except Exception as error:translate_error(error)

@app.get('/v1/knowledge/{document_id}/formulas')
def research_formulas(document_id:str,identity=Depends(require('read'))):
    from . import research_store
    from .semantic_jobs import require_readable_index
    try:
        require_readable_index(document_id)
        return research_store.get(document_id)['formulas']
    except Exception as error:translate_error(error)

@app.get('/v1/knowledge/{document_id}/browse')
def browse_knowledge(document_id:str,
    kind:Annotated[str,Query(pattern=r'^(all|document|passage|source_span|observation|concept_mention|formula)$')]='all',
    q:Annotated[str,Query(max_length=200)]='',offset:Annotated[int,Query(ge=0,le=40000)]=0,
    limit:Annotated[int,Query(ge=1,le=50)]=25,identity=Depends(require('read'))):
    from .knowledge_browse import page
    try:return page(document_id,kind=kind,query=q,offset=offset,limit=limit)
    except Exception as error:translate_error(error)

@app.get('/v1/knowledge/{document_id}/nodes/{node_id}')
def knowledge_node(document_id:str,node_id:str,offset:Annotated[int,Query(ge=0,le=40000)]=0,
    limit:Annotated[int,Query(ge=1,le=50)]=25,identity=Depends(require('read'))):
    from .knowledge_browse import detail
    try:return detail(document_id,node_id,offset=offset,limit=limit)
    except Exception as error:translate_error(error)

@app.get('/v1/knowledge/{document_id}/units')
def research_document_units(document_id:str,identity=Depends(require('read'))):
    from . import research_store
    from .semantic_jobs import require_readable_index
    try:
        require_readable_index(document_id)
        return research_store.document_units(document_id)
    except Exception as error:translate_error(error)

@app.get('/v1/knowledge/{document_id}/supplements')
def research_supplements(document_id:str,identity=Depends(require('read'))):
    from . import research_store
    from .semantic_jobs import require_readable_index
    try:
        require_readable_index(document_id)
        return dict(items=research_store.supplements(document_id),authority_granted=False)
    except Exception as error:translate_error(error)

@app.post('/v1/knowledge/{document_id}/embeddings')
def research_embeddings(document_id:str,payload:EmbeddingInput,identity=Depends(require('ingest'))):
    from . import research_store
    try:return research_store.put_embeddings(document_id,**payload.model_dump(),actor=identity['actor'])
    except Exception as error:translate_error(error)

@app.post('/v1/knowledge/semantic-search')
def semantic_search(payload:SemanticInput,identity=Depends(require('read'))):
    from . import research_store
    try:return research_store.search(**payload.model_dump())
    except Exception as error:translate_error(error)
@app.get('/v1/sources/{document_id}')
def source(document_id:str,locator:str|None=None,identity=Depends(require('read'))):
    try: return workflows.source(document_id,locator)
    except Exception as error: translate_error(error)


@app.get('/v1/sources/{document_id}/access')
def source_access(document_id:str,identity=Depends(require('read'))):
    from .private_access_store import source_access as get_access
    try:return get_access(document_id)
    except Exception as error:translate_error(error)


@app.post('/v1/sources/{document_id}/analysis')
def source_analysis(document_id:str,payload:TableAnalysisInput,identity=Depends(require('read'))):
    from .table_analysis import analyze_source
    try:return analyze_source(document_id,payload)
    except Exception as error:translate_error(error)


@app.post('/v1/sources/{document_id}/access')
def source_share(document_id:str,payload:SourceShare,identity=Depends(require('read'))):
    from .private_access_store import change_share,source_access as get_access
    try:
        get_access(document_id)  # establish owner authority before directory validation
        if payload.subject_kind=='user' and not payload.revoke:
            from .security import _local_identities
            if payload.subject_id not in {entry['actor'] for entry,_ in _local_identities()}:
                from .private_access_store import provider_sharing_target
                if not provider_sharing_target(document_id,payload.subject_id):
                    raise ValueError('Unknown or unavailable sharing target')
        return change_share(document_id,**payload.model_dump())
    except Exception as error:translate_error(error)


@app.get('/v1/sources/{document_id}/index')
def source_index(document_id:str,identity=Depends(require('read'))):
    from .semantic_jobs import source_status
    try:return source_status(document_id)
    except Exception as error:translate_error(error)


@app.post('/v1/sources/{document_id}/retry-index')
def retry_source_index(document_id:str,payload:IndexRetry,identity=Depends(require('ingest'))):
    from .semantic_jobs import retry
    try:return retry(document_id,payload.expected_epoch)
    except Exception as error:translate_error(error)
@app.post('/v1/sources/{document_id}/cancel-index')
def cancel_source_index(document_id:str,payload:IndexRetry,identity=Depends(require('ingest'))):
    from .semantic_jobs import cancel
    try:return cancel(document_id,payload.expected_epoch)
    except Exception as error:translate_error(error)


@app.post('/v1/sources/{document_id}/index-priority')
def priority_source_index(document_id:str,payload:IndexPriority,identity=Depends(require('ingest'))):
    from .semantic_jobs import set_priority
    try:return set_priority(document_id,payload.expected_epoch,payload.priority)
    except Exception as error:translate_error(error)


@app.get('/v1/sources/{document_id}/original')
@app.head('/v1/sources/{document_id}/original')
def original(document_id:str,identity=Depends(require('read'))):
    try:
        data,media = workflows.original_source(document_id)
        from urllib.parse import quote
        title=workflows.source(document_id)['title']
        filename=title.replace('/','_').replace('\\','_').replace('\r','').replace('\n','')[:180]
        return Response(data,media_type=media,headers={'Content-Disposition':"attachment; filename=source; filename*=UTF-8''"+quote(filename,safe='')})
    except Exception as error: translate_error(error)
@app.get('/v1/claims')
def claims(limit:Annotated[int,Query(ge=1,le=100)]=25,
       cursor:Annotated[str|None,Query(max_length=512)]=None,identity=Depends(require('read'))):
    from .claim_pages import page
    try:return page(limit=limit,cursor=cursor)
    except Exception as error:translate_error(error)
@app.post('/v1/review/{claim_id}')
def review(claim_id:str,payload:Review,identity=Depends(require('review'))):
    try: return workflows.review(claim_id,**payload.model_dump(),actor=identity['actor'])
    except Exception as error: translate_error(error)

@app.get('/v1/claims/{claim_id}')
def claim_inspection(claim_id:str,offset:Annotated[int,Query(ge=0,le=2000)]=0,identity=Depends(require('read'))):
    from .claim_review import detail
    try:return detail(claim_id,offset=offset)
    except Exception as error:translate_error(error)

@app.get('/v1/claims/{claim_id}/events')
def claim_event_history(claim_id:str,before_id:Annotated[str|None,Query(pattern=r'^[1-9][0-9]{0,18}$')]=None,
                        identity=Depends(require('read'))):
    from .claim_review import events
    try:return events(claim_id,before_id=before_id)
    except Exception as error:translate_error(error)
@app.get('/v1/search')
def search(q:Annotated[str,Query(min_length=1,max_length=1000)],identity=Depends(require('read'))):
    hits=library_retrieve(q)
    return dict(items=hits,retrieval_coverage=retrieval_coverage(hits))

def validate_question_scope(document_ids,revision,pages):
    if (revision or pages) and not document_ids:raise ValueError('Revision/page scope requires selected source IDs')
    for document_id in document_ids or []:
        selected=workflows.source(document_id)
        if revision is not None and selected['revision']!=revision:raise ValueError('Stale selected source revision')
        if pages:
            metadata=selected.get('manifest',{}).get('documents',[{}])[0].get('metadata',{})
            count=max((p.get('page') or 0 for p in metadata.get('pages',[])),default=0)
            if not count or any(p>count for p in pages):raise ValueError('Unsupported selected page scope')

def _claim_context_for_hits(hits,*,document_ids=None,revision=None,pages=None):
    all_claims = workflows.claim_context(hits,document_ids=document_ids,revision=revision,pages=pages)
    def passage_spans(hit):
        return {(hit['document_id'],locator) for locator in
                [hit['locator'],*[segment['locator'] for segment in hit.get('source_segments',[])]]}
    selected_spans = set().union(*(passage_spans(hit) for hit in hits))
    matched = [r for r in all_claims if (r['document_id'],r['locator']) in selected_spans and r['status'] not in {'rejected','superseded'}]
    groups={(r['subject'],r['predicate']) for r in matched}
    matched=[r for r in all_claims if (r['subject'],r['predicate']) in groups
             and r['status'] not in {'rejected','superseded'}
             and (not document_ids or r['document_id'] in document_ids)]
    return all_claims,matched


def require_current_claim_context(hits,expected,*,document_ids=None,revision=None,pages=None):
    _,current=_claim_context_for_hits(hits,document_ids=document_ids,revision=revision,pages=pages)
    from .contracts.evidence import canonical_hash
    fingerprint=lambda claims:canonical_hash(sorted(claims,key=lambda claim:claim['id']))
    if fingerprint(current)!=fingerprint(expected):
        raise ValueError('Source claims changed during inference; retry')


def evidence(question,memory=None,*,document_ids=None,revision=None,pages=None):
    validate_question_scope(document_ids,revision,pages)
    hits = library_retrieve(question,document_ids=document_ids,revision=revision,pages=pages)
    from .retrieval.query import build_retrieval_query
    implicit_subject=(not build_retrieval_query(question).entities and
                      bool(set(re.findall(r'\b\w+\b',question.casefold())) & {'it','that','this','they','revision','previous'}))
    if not hits and memory and implicit_subject:
        previous = next((m['text'] for m in reversed(memory['working']) if m['role']=='user'),None)
        if previous: hits = library_retrieve(previous[:1000],document_ids=document_ids,revision=revision,pages=pages)
    all_claims,matched=_claim_context_for_hits(hits,document_ids=document_ids,revision=revision,pages=pages)
    if hasattr(hits,'coverage'):
        hits.coverage['claim_context']='passage-claims-and-distinct-alternative-witnesses'
    def passage_spans(hit):
        return {(hit['document_id'],locator) for locator in
                [hit['locator'],*[segment['locator'] for segment in hit.get('source_segments',[])]]}
    for hit in hits:
        observed = [r for r in all_claims if (r['document_id'],r['locator']) in passage_spans(hit)]
        hit['projection_status'] = ','.join(sorted({r['status'] for r in observed})) or 'source-only'
        if pages:
            coverage=[p for p in hit.get('page_coverage',[]) or [] if p.get('page') in pages]
            hit['extraction_complete']=len(coverage)==len(set(pages)) and all(p['complete'] for p in coverage)
    conflicts = conflict_groups(matched)
    citations = [citation_from_hit(h) for h in hits]
    return hits,matched,conflicts,citations
def retrieval_coverage(hits):
    coverage=getattr(hits,'coverage',None)
    return dict(coverage) if coverage is not None else dict(
        method='unknown',returned_chunks=len(hits),total_matching_chunks=None)

def attach_retrieval_coverage(result,hits):
    coverage=getattr(hits,'coverage',None)
    result['retrieval_coverage']=retrieval_coverage(hits)
    if coverage and coverage.get('semantic_state')=='unavailable':
        result['answer']='Semantic retrieval is unavailable; this response uses lexical matches only.\n'+result['answer']
    if coverage and coverage.get('additional_matches_exist') is True:
        result['answer']='RETRIEVAL LIMIT: additional matching excerpts were omitted; this response is not exhaustive.\n'+result['answer']
    selection=result.get('source_selection')
    omitted=selection.get('omitted_units') if isinstance(selection,dict) else None
    if type(omitted) is int and omitted>0:
        result['answer']=f'CPU SOURCE SELECTION LIMIT: {omitted} distinct text units in the retrieved excerpts were excluded from answer choices; this response is not exhaustive.\n'+result['answer']
    return result


def require_current_evidence(hits,memory):
    identity=store.request_identity()
    if identity is not None and identity.get('identity_kind')=='local-user':
        from .source_dependencies import collect_sources,validate_sources
        with store.connect() as conn:validate_sources(conn,collect_sources(hits,memory,conn=conn))


async def _await_task_completion(task: asyncio.Task):
    while True:
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            if task.cancelled():
                raise
            current=asyncio.current_task()
            if current is not None:
                current.uncancel()


async def _persist_reason_completion(payload,identity,sid,result,run_id=None):
    """Settle the completion sequence even if the HTTP caller disconnects.

    Once these writes begin, transport cancellation cannot roll back a committed
    transaction. Finish the receipt so polling reports the actual saved result.
    """
    if run_id is not None:
        result['audit_receipt']=await asyncio.to_thread(workflows.finish_inference,run_id,identity['actor'],
            {k:result.get(k) for k in ('provider','model','latency_ms','usage','citation_validation','answer_strategy','source_selection',
                                      'token_admission','source_dependencies','provenance_complete')})
    await asyncio.to_thread(workflows.save_exchange,sid,payload.question,result,identity['actor'])
    await asyncio.to_thread(workflows.finish_invocation,identity['actor'],payload.request_id,result)


@app.post('/v1/chat')
def chat(payload:Question,identity=Depends(require('chat'))):
    admitted=False
    try:
        cached=workflows.begin_invocation(identity['actor'],payload.request_id,dict(mode='chat',**payload.model_dump()))
        if cached is not None:return cached
        admitted=True
        sid = workflows.session(identity['actor'],payload.session_id)
        memory = workflows.memory_context(identity['actor'],sid,payload.question,document_ids=payload.document_ids,revision=payload.revision,pages=payload.pages)
        hits,matched,conflicts,citations = evidence(payload.question,memory,document_ids=payload.document_ids,revision=payload.revision,pages=payload.pages)
        if not hits: answer='No supporting source evidence found. Try a source-specific term; NSAI will not invent an answer.'
        elif conflicts:
            answer='Unresolved conflicting source statements: '+'; '.join(f"{g['subject']} {g['predicate']}: {', '.join(g['alternatives'])}" for g in conflicts)+'. Independent review is required.'
        else: answer='Source excerpts with review status (historical alternatives remain visible):\n'+'\n'.join(f"[{h['id']}] ({h['projection_status']}) {h['text']}" for h in hits[:6])
        if any(not h.get('extraction_complete',True) for h in hits):answer='INCOMPLETE SOURCE COVERAGE: some pages are unreadable or unsupported. These excerpts cannot establish absence of other facts.\n'+answer
        result=dict(mode='evidence-extract',answer=answer,citations=citations,conflicts=conflicts,session_id=sid,answer_verified=False,memory=memory)
        attach_retrieval_coverage(result,hits)
        stamp_result(result,hits,memory)
        workflows.save_exchange(sid,payload.question,result,identity['actor'])
        workflows.finish_invocation(identity['actor'],payload.request_id,result)
        return result
    except Exception as error:
        if admitted:workflows.finish_invocation(identity['actor'],payload.request_id,dict(error_type=type(error).__name__),failed=True)
        translate_error(error)
@app.post('/v1/reason')
@admitted_operation('generation')
async def reason(payload:Question,identity=Depends(require('chat'))):
    if inference_lock.locked(): raise HTTPException(429,'Inference busy; retry later')
    run_id = None
    admitted=False
    completion=None
    async with inference_lock:
        try:
            invocation=asyncio.create_task(asyncio.to_thread(workflows.begin_invocation,identity['actor'],
                payload.request_id,dict(mode='reason',**payload.model_dump())))
            try:
                cached=await asyncio.shield(invocation)
            except asyncio.CancelledError as cancellation:
                try:
                    cached=await _await_task_completion(invocation)
                except Exception:
                    raise cancellation
                admitted=cached is None and payload.request_id is not None
                raise cancellation
            if cached is not None:return cached
            admitted=True
            sid = await asyncio.to_thread(workflows.session,identity['actor'],payload.session_id)
            memory = await asyncio.to_thread(workflows.memory_context,identity['actor'],sid,payload.question,document_ids=payload.document_ids,revision=payload.revision,pages=payload.pages)
            hits,matched,conflicts,citations = await asyncio.to_thread(evidence,payload.question,memory,document_ids=payload.document_ids,revision=payload.revision,pages=payload.pages)
            if not hits or conflicts or any(not h.get('extraction_complete',True) for h in hits):
                answer='No supporting source evidence found; no model call made.' if not hits else ('Unresolved authorized source conflict; independent review required. No model call made.' if conflicts else 'Incomplete selected source coverage; unsupported pages are withheld. No model call made.')
                result=dict(mode='evidence-extract',answer=answer,citations=citations,conflicts=conflicts,session_id=sid,answer_verified=False,memory=memory)
                attach_retrieval_coverage(result,hits)
                stamp_result(result,hits,memory)
                completion=asyncio.create_task(_persist_reason_completion(payload,identity,sid,result))
                await asyncio.shield(completion)
                return result
            current=await asyncio.to_thread(workflows.policy)
            if not current['inference_enabled']:raise PermissionError('Inference disabled by local administrator')
            await asyncio.to_thread(require_current_evidence,hits,memory)
            prepared=prepare_source_request(payload.question,hits,max_tokens=current['max_output_tokens'],memory=memory)
            admission=await admit_source_request(prepared)
            await asyncio.to_thread(require_current_claim_context,hits,matched,
                document_ids=payload.document_ids,revision=payload.revision,pages=payload.pages)
            reservation=asyncio.create_task(asyncio.to_thread(workflows.reserve_inference,identity['actor']))
            try:
                run_id, output_budget = await asyncio.shield(reservation)
            except asyncio.CancelledError as cancellation:
                try:
                    run_id, _ = await _await_task_completion(reservation)
                except Exception:
                    raise cancellation
                finish=asyncio.create_task(asyncio.to_thread(workflows.finish_inference,run_id,identity['actor'],
                    dict(error_type='CancelledError'),failed=True))
                await _await_task_completion(finish)
                run_id = None
                raise cancellation
            if output_budget!=prepared['max_tokens']:raise ValueError('Policy changed during token admission; retry')
            await asyncio.to_thread(require_current_evidence,hits,memory)
            result = await generate_from_sources(payload.question,hits,max_tokens=output_budget,memory=memory,prepared=prepared,admission=admission)
            await asyncio.to_thread(require_current_claim_context,hits,matched,
                document_ids=payload.document_ids,revision=payload.revision,pages=payload.pages)
            result.update(session_id=sid,conflicts=conflicts,memory=memory,answer_verified=False)
            attach_retrieval_coverage(result,hits)
            stamp_result(result,hits,memory)
            result['run_id']=run_id
            if conflicts: result['answer']+='\n\nUnresolved source conflict: '+'; '.join(f"{g['subject']}: {', '.join(g['alternatives'])}" for g in conflicts)
            await asyncio.to_thread(require_current_evidence,hits,memory)
            completion=asyncio.create_task(_persist_reason_completion(payload,identity,sid,result,run_id))
            await asyncio.shield(completion)
            return result
        except asyncio.CancelledError:
            if completion is not None:
                try:
                    await _await_task_completion(completion)
                except Exception:
                    # Completion failed rather than merely losing its HTTP
                    # delivery. Continue normal durable failure cleanup.
                    pass
                else:
                    raise
            if run_id:
                finish=asyncio.create_task(asyncio.to_thread(workflows.finish_inference,run_id,identity['actor'],
                    dict(error_type='CancelledError'),failed=True))
                await _await_task_completion(finish)
            if admitted:
                finish=asyncio.create_task(asyncio.to_thread(workflows.finish_invocation,identity['actor'],
                    payload.request_id,dict(error_type='CancelledError'),failed=True))
                await _await_task_completion(finish)
            raise
        except Exception as error:
            if run_id: await asyncio.to_thread(workflows.finish_inference,run_id,identity['actor'],dict(error_type=type(error).__name__),failed=True)
            if admitted:await asyncio.to_thread(workflows.finish_invocation,identity['actor'],payload.request_id,dict(error_type=type(error).__name__),failed=True)
            if isinstance(error,(PermissionError,ValueError)): translate_error(error)
            raise HTTPException(502,'Inference unavailable; inspect model status') from None
@app.get('/v1/chat/sessions')
def conversation_sessions(limit:Annotated[int,Query(ge=1,le=50)]=25,
                          cursor:Annotated[str|None,Query(max_length=512)]=None,identity=Depends(require('read'))):
    from .conversation_history import sessions
    try:return sessions(limit=limit,cursor=cursor)
    except Exception as error:translate_error(error)


@app.get('/v1/chat/sessions/{session_id}/messages')
def conversation_messages(session_id:str,limit:Annotated[int,Query(ge=1,le=50)]=25,
                          before_id:Annotated[str|None,Query(pattern=r'^[1-9][0-9]{0,18}$')]=None,identity=Depends(require('read'))):
    from .conversation_history import messages
    try:return messages(session_id,limit=limit,before_id=before_id)
    except Exception as error:translate_error(error)


@app.get('/v1/chat/sessions/{session_id}/messages/{message_id}')
def conversation_message(session_id:str,message_id:str,identity=Depends(require('read'))):
    from .conversation_history import message
    try:return message(session_id,message_id)
    except Exception as error:translate_error(error)


@app.get('/v1/memory/{session_id}')
def memory(session_id:Annotated[str,APIPath(pattern=r'^[a-f0-9]{32}$')],identity=Depends(require('chat')),
           document_ids:Annotated[list[Annotated[str,Field(pattern=r'^[a-f0-9]{32}$')]],Query(max_length=20)]=[],
           revision:Annotated[str|None,Query(min_length=1,max_length=50)]=None,
           pages:Annotated[list[Annotated[int,Field(ge=1,le=1000)]],Query(max_length=100)]=[]):
    try:
        scope=Question(question='Inspect candidate memory',document_ids=document_ids,revision=revision,pages=pages)
        validate_question_scope(scope.document_ids,scope.revision,scope.pages)
        return workflows.memory_context(identity['actor'],session_id,document_ids=scope.document_ids,revision=scope.revision,pages=scope.pages)
    except Exception as error: translate_error(error)

@app.get('/v1/invocations/{request_id}')
def invocation(request_id:Annotated[str,APIPath(pattern=r'^[a-f0-9]{32}$')],identity=Depends(require('chat'))):
    try:return workflows.invocation_status(identity['actor'],request_id)
    except Exception as error:translate_error(error)

@app.get('/v1/admin/resources')
def resources(identity=Depends(require('admin'))):
    return workflows.resource_usage()
@app.post('/v1/learning')
def propose(payload:Reflection,identity=Depends(require('propose'))):
    try: return workflows.propose_learning(identity['actor'],**payload.model_dump())
    except Exception as error: translate_error(error)
@app.post('/v1/learning/reflect')
def reflect(identity=Depends(require('propose'))):
    try: return workflows.reflect_on_conflicts(identity['actor'])
    except Exception as error: translate_error(error)
@app.get('/v1/learning')
def proposals(limit:Annotated[int,Query(ge=1,le=100)]=100,
              cursor:Annotated[str|None,Query(max_length=512)]=None,
              state:Annotated[str,Query(pattern=r'^(all|candidate|reviewed|rejected)$')]='all',
              identity=Depends(require('review'))):
    from .learning_pages import page
    try:return page(limit=limit,cursor=cursor,state=state)
    except Exception as error:translate_error(error)

@app.get('/v1/learning/own')
def own_proposals(limit:Annotated[int,Query(ge=1,le=100)]=25,
                  cursor:Annotated[str|None,Query(max_length=512)]=None,
                  state:Annotated[str,Query(pattern=r'^(all|candidate|reviewed|rejected)$')]='all',
                  identity=Depends(require('propose'))):
    from .learning_pages import page
    try:return page(own=True,limit=limit,cursor=cursor,state=state)
    except Exception as error:translate_error(error)
@app.post('/v1/learning/{pid}/review')
def learning_review(pid:str,payload:LearningReview,identity=Depends(require('review'))):
    try: return workflows.review_learning(identity['actor'],pid,**payload.model_dump())
    except Exception as error: translate_error(error)
@app.get('/v1/admin/security')
def security(identity=Depends(require('admin'))): return dict(**security_status(),policy=workflows.policy())
@app.put('/v1/admin/policy')
def policy(payload:PolicyUpdate,identity=Depends(require('admin'))):
    try:
        data=payload.model_dump(); data['central_config']=payload.central_config.staged()
        current=workflows.policy()
        if ((data['inference_enabled'] and not current['inference_enabled']) or data['daily_call_limit']>current['daily_call_limit'] or data['max_output_tokens']>current['max_output_tokens']):
            from .governed_store import stage_policy
            return stage_policy(identity['actor'],data)
        return workflows.update_policy(identity['actor'],data)
    except Exception as error: translate_error(error)
@app.get('/v1/audit')
def audit(identity=Depends(require('review'))): return workflows.audit_report()
@app.post('/v1/execute')
def execute(identity=Depends(principal)): raise HTTPException(403,'Generated code execution disabled; no admitted Linux executor')
@app.get('/v1/submission/evidence')
def submission(identity=Depends(require('read'))):
    path=ASSET_ROOT/'verification.json'
    return __import__('json').loads(path.read_text()) if path.exists() else dict(status='Pending current test evidence')

@app.post('/v1/assembly/{document_id}')
def assembly(document_id:str,identity=Depends(require('propose'))):
    from .governed_store import assemble
    try:return assemble(identity['actor'],document_id)
    except Exception as error:translate_error(error)

@app.post('/v1/sources/{document_id}/reparse')
async def reparse(document_id:str,identity=Depends(require('propose'))):
    """Versioned candidate extraction; originals and active chunks remain immutable."""
    from .governed_store import persist
    from .ingestion import validate_parsed_source
    from .inference import _bounded_json
    try:
        data,media=await asyncio.to_thread(workflows.original_source,document_id)
        token=store._secret(os.environ['NSAI_PARSER_TOKEN_FILE'])
        endpoint=os.environ['NSAI_PARSER_URL']
        if endpoint!='http://parser:8788':raise ValueError('Parser endpoint is not admitted')
        async with httpx.AsyncClient(timeout=25,follow_redirects=False,trust_env=False) as client:
            parsed=await _bounded_json(client,'POST',endpoint+'/parse',headers={'Authorization':'Bearer '+token},
                payload=dict(filename='source'+{'application/pdf':'.pdf','text/plain':'.txt','text/markdown':'.md','text/csv':'.csv','text/tab-separated-values':'.tsv','application/json':'.json','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':'.xlsx'}[media],data=base64.b64encode(data).decode()),maximum=16*1024*1024)
        parsed=validate_parsed_source(data,parsed)
        return await asyncio.to_thread(persist,'extraction',identity['actor'],document_id,dict(generation_sha256=__import__('nsai.contracts.evidence',fromlist=['canonical_hash']).canonical_hash(parsed),parsed=parsed,active=False,activation='independent validation and review required; no automatic index replacement'))
    except Exception as error:translate_error(error)

@app.post('/v1/issues/analyze')
def issue(payload:IssueInput,identity=Depends(require('propose'))):
    from .governed_store import analyze_issue
    try:return analyze_issue(identity['actor'],payload.document_id)
    except Exception as error:translate_error(error)

@app.post('/v1/governed/proposals')
def governed_proposal(payload:DataProposal,identity=Depends(require('propose'))):
    from .governed_store import propose
    try:return propose(identity['actor'],payload.document_id,payload.capability,payload.data)
    except Exception as error:translate_error(error)

@app.get('/v1/governed/records')
def governed_records(limit:int=Query(default=25,ge=1,le=100),offset:int=Query(default=0,ge=0,le=100000),cursor:str|None=Query(default=None,max_length=512),kind:str=Query(default='all',pattern=r'^(all|assembly|issues|proposal|extraction)$'),state:str=Query(default='all',pattern=r'^(all|candidate|reviewed|rejected)$'),identity=Depends(require('read'))):
    from .governed_pages import page
    try:return page(limit=limit,offset=offset,cursor=cursor,kind=kind,state=state)
    except Exception as error:translate_error(error)

@app.post('/v1/governed/records/{record_id}/review')
def governed_review(record_id:str,payload:GovernedReview,identity=Depends(require('review'))):
    from .governed_store import review
    try:return review(identity['actor'],record_id,payload.decision,payload.rationale)
    except Exception as error:translate_error(error)

@app.get('/v1/governed/records/{record_id}')
def governed_record(record_id:str,identity=Depends(require('read'))):
    from .governed_store import record
    try:return record(identity['actor'],record_id,reviewer='review' in identity['permissions'])
    except Exception as error:translate_error(error)

@app.get('/v1/admin/actions')
def pending_actions(identity=Depends(require('review'))):
    from .governed_store import pending_actions
    return dict(items=pending_actions())

@app.post('/v1/admin/actions/{action_id}/review')
def approve_action(action_id:str,payload:ActionApproval,identity=Depends(require('review'))):
    from .governed_store import approve_policy
    try:return approve_policy(identity['actor'],action_id,payload.approve)
    except Exception as error:translate_error(error)

@app.get('/v1/admin/retention')
def retention(identity=Depends(require('admin'))):
    from .governed_store import retention_dry_run
    return retention_dry_run()

@app.get('/v1/admin/costs')
def cost_status(identity=Depends(require('admin'))):
    from .cost_store import admin_overview
    try:return admin_overview()
    except Exception as error:translate_error(error)
