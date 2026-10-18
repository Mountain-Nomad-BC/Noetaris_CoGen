"""Sequential private arXiv sample from explicit bounded official metadata pools.

No application/database ingestion. Originals are never truncated or approved for
redistribution. Eligibility uses the pinned current native parser in an owned
network-disabled resource-limited container.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime,timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import random
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from uuid import uuid4

ROOT=Path(__file__).resolve().parent.parent
PARSER_IMAGE='sha256:0df1ace1c8c5ae9ec3aa8609a87bfb5ff1ff736da4bb5cb106f27271ae4236b1'
MAX_BYTES=2*1024*1024
TOPICS={
 'ai':('cs.AI','cs.LG'),
 'physics':('quant-ph','physics.class-ph'),
 'computing_systems':('cs.DC','cs.OS','cs.PF'),
 'economics_business':('econ.GN','econ.TH','q-fin.EC'),
 'biology':('q-bio.PE','q-bio.MN','q-bio.QM'),
 'mathematics':('math.CO','math.PR','math.NT'),
 'linguistics':('cs.CL',),
}
ATOM={'a':'http://www.w3.org/2005/Atom','arxiv':'http://arxiv.org/schemas/atom'}

def sha(data):return hashlib.sha256(data).hexdigest()
def bounded_cached_bytes(path,maximum):
    if path.is_symlink()or not path.is_file()or path.stat().st_size>maximum:raise ValueError('Cached official bytes failed digest/budget admission')
    with path.open('rb')as stream:data=stream.read(maximum+1)
    if len(data)>maximum:raise ValueError('Cached official bytes failed digest/budget admission')
    return data
def utc():return datetime.now(timezone.utc).isoformat()
def normalized(text):return ' '.join(text.split())

def official_url(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https'or p.hostname not in {'arxiv.org','export.arxiv.org'}or p.username or p.password or p.port not in {None,443}or p.fragment:
        raise ValueError('Only exact official HTTPS arXiv hosts are admitted')
    return url

def paper_id(value):
    value=value.removeprefix('https://arxiv.org/abs/').removeprefix('http://arxiv.org/abs/')
    if not re.fullmatch(r'(?:[0-9]{4}\.[0-9]{4,5}|[a-z-]+(?:\.[A-Z]{2})?/[0-9]{7})v[1-9][0-9]{0,2}',value):
        raise ValueError('Explicit versioned arXiv identifier required')
    return value

def parse_pool(raw,topic):
    if len(raw)>256000 or b'<!DOCTYPE'in raw.upper()or b'<!ENTITY'in raw.upper():raise ValueError('Invalid bounded metadata XML')
    tree=ET.fromstring(raw);records=[];seen=set()
    for entry in tree.findall('a:entry',ATOM):
        identity=paper_id(entry.findtext('a:id',namespaces=ATOM)or'')
        title=normalized(entry.findtext('a:title',namespaces=ATOM)or'')
        category=entry.find('arxiv:primary_category',ATOM)
        categories=[x.attrib['term']for x in entry.findall('a:category',ATOM)]
        if not title or category is None or category.attrib.get('term')not in categories or not set(categories).intersection(TOPICS[topic]):
            raise ValueError('Metadata category/title does not bind requested pool')
        if identity in seen:raise ValueError('Duplicate paper in pool')
        seen.add(identity);base,version=identity.rsplit('v',1)
        records.append(dict(id=identity,base_id=base,version=int(version),title=title,
            primary_category=category.attrib['term'],categories=categories,
            authors=[normalized(x.findtext('a:name',namespaces=ATOM)or'')for x in entry.findall('a:author',ATOM)],
            updated=entry.findtext('a:updated',namespaces=ATOM),published=entry.findtext('a:published',namespaces=ATOM),
            abstract_url='https://arxiv.org/abs/'+identity,pdf_url='https://arxiv.org/pdf/'+identity))
    if not 2<=len(records)<=20:raise ValueError('Metadata pool must contain2..20 actual papers')
    return records

class AbsMetadata(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.meta={};self.licenses=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='meta'and attrs.get('name','').startswith('citation_'):self.meta[attrs['name']]=attrs.get('content','')
        if tag=='a':
            p=urllib.parse.urlsplit(attrs.get('href',''))
            if p.hostname in {'arxiv.org','creativecommons.org'}and p.path.startswith('/licenses/'):
                self.licenses.append(attrs['href'])

def validate_abs(raw,record):
    if len(raw)>256000:raise ValueError('Oversized abstract metadata')
    text=raw.decode('utf-8',errors='strict');parser=AbsMetadata();parser.feed(text)
    if normalized(parser.meta.get('citation_title',''))!=record['title']or parser.meta.get('citation_arxiv_id')!=record['base_id']:
        raise ValueError('Abstract/API paper identity or title mismatch')
    if f'[v{record["version"]}]'not in text:raise ValueError('Requested version absent from submission history')
    if not re.search(r'\('+re.escape(record['primary_category'])+r'\)',text):raise ValueError('Abstract/API primary category mismatch')
    licenses=sorted(set(parser.licenses))
    if len(licenses)!=1:raise ValueError('Missing or ambiguous paper license metadata')
    return dict(license_url=licenses[0],metadata_title_verified=True,category_verified=True,version_in_history_verified=True)

def sample_order(records,seed,topic):
    result=sorted(records,key=lambda r:r['id']);random.Random(str(seed)+':'+topic).shuffle(result);return result

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

class Fetcher:
    def __init__(self,events,delay=3.1,cache=None):
        if delay<3:raise ValueError('Minimum polite delay is3seconds')
        self.events=events;self.delay=delay;self.last_end=None;self.opener=urllib.request.build_opener(NoRedirect);self.cache=cache or{}
    def fetch(self,url,maximum):
        official_url(url)
        if url in self.cache:
            item=self.cache[url];path=Path(item['path']);data=bounded_cached_bytes(path,maximum)
            if path.is_symlink()or len(data)>maximum or sha(data)!=item['sha256']:raise ValueError('Cached official bytes failed digest/budget admission')
            self.events.append(dict(url=url,cached_official_bytes=True,reused_from=item['run_id'],sha256=sha(data),bytes=len(data),gap_after_previous_end_seconds=None))
            return data,url
        for hop in range(4):
            if self.last_end is not None:time.sleep(max(0,self.last_end+self.delay-time.monotonic()))
            started=time.monotonic();event=dict(url=url,started_at=utc(),gap_after_previous_end_seconds=None if self.last_end is None else started-self.last_end);self.events.append(event)
            response=None
            try:
                request=urllib.request.Request(url,headers={'User-Agent':'NSAI-local-corpus/1.0 (personal research; sequential bounded requests)','Accept-Encoding':'identity'})
                try:response=self.opener.open(request,timeout=30)
                except urllib.error.HTTPError as error:
                    event['http_status']=error.code
                    if error.code in {301,302,303,307,308}:
                        location=error.headers.get('Location');error.close()
                        if not location or hop==3:raise ValueError('Missing/excessive official redirect')
                        url=official_url(urllib.parse.urljoin(url,location));event['redirect_to']=url;continue
                    error.close();raise
                event.update(http_status=response.status,content_type=response.headers.get('Content-Type'),content_encoding=response.headers.get('Content-Encoding','identity'))
                if response.headers.get('Content-Encoding','identity').lower()!='identity':raise ValueError('Compressed transport refused')
                declared=response.headers.get('Content-Length')
                if declared is not None and (not declared.isdigit()or int(declared)>maximum):raise ValueError('Declared response exceeds acquisition cap')
                data=bytearray()
                while True:
                    if time.monotonic()-started>60:raise TimeoutError('Body-loop acquisition deadline')
                    block=response.read1(min(65536,maximum-len(data)+1))
                    if not block:break
                    if len(data)+len(block)>maximum:raise ValueError('Streaming response exceeds acquisition cap')
                    data.extend(block)
                event.update(bytes=len(data),sha256=sha(data),completed_at=utc())
                return bytes(data),url
            except Exception as error:
                event.update(error_type=type(error).__name__,http_status=getattr(error,'code',event.get('http_status')));raise
            finally:
                if response is not None:response.close()
                self.last_end=time.monotonic();event['elapsed_seconds']=self.last_end-started
        raise ValueError('Redirect budget exhausted')

def preflight_pdf(data,identity,image=PARSER_IMAGE):
    if not 1<=len(data)<=MAX_BYTES or not data.startswith(b'%PDF-'):raise ValueError('Original PDF magic/size invalid')
    name='nsai-arxiv-preflight-'+uuid4().hex[:12];owner=uuid4().hex
    args=['docker','run','--name',name,'--label','nsai.owner='+owner,'--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges:true','--user','10001:10001','--cpus','1','--memory','384m','--pids-limit','32',
        '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=16m,mode=1777','-i','--entrypoint','python',image,'-m','nsai.parser_child']
    try:
        result=subprocess.run(args,input=json.dumps(dict(filename=identity.replace('/','_')+'.pdf',data=base64.b64encode(data).decode())).encode(),capture_output=True,timeout=25)
        if result.returncode:raise ValueError('Pinned native parser refused original PDF')
        if len(result.stdout)>16*1024*1024:raise ValueError('Parser response exceeds cap')
        parsed=json.loads(result.stdout)
        if parsed.get('original_sha256')!=sha(data)or type(parsed.get('page_count'))is not int or not 1<=parsed['page_count']<=100:
            raise ValueError('Parser page/hash custody mismatch')
        chars=len(parsed.get('raw_text',''))
        if not 0<chars<=200000:raise ValueError('Empty/oversized native extraction; original not truncated')
        return dict(status='PASS_CAPS_ONLY',page_count=parsed['page_count'],native_text_characters=chars,complete=parsed.get('complete'),
            native_gap_pages=[p['page']for p in parsed.get('pages',[])if not p.get('complete')],warnings=parsed.get('warnings',[]),
            parser_image=image,scope='actual pinned native parser size/page/character/hash preflight only; incomplete visual coverage retained honestly; no DB ingestion or semantic/math quality claim')
    finally:
        inspect=subprocess.run(['docker','inspect',name],capture_output=True,timeout=15)
        if inspect.returncode==0:
            info=json.loads(inspect.stdout)[0]
            if info['Config'].get('Labels',{}).get('nsai.owner')!=owner:raise RuntimeError('Unowned preflight cleanup refused')
            subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15,check=True)

def reuse_cache(run_id):
    if not re.fullmatch('download-[a-f0-9]{12}',run_id):raise ValueError('Invalid owned download cache identity')
    directory=ROOT/'data/arxiv-corpus'/run_id;manifest=json.loads((directory/'manifest.json').read_text());cache={}
    def put(url,path,digest):
        if path.is_file()and not path.is_symlink()and sha(bounded_cached_bytes(path,MAX_BYTES))==digest:cache[url]=dict(path=str(path),sha256=digest,run_id=run_id)
    for topic,pool in manifest.get('pools',{}).items():put(pool['query_url'],directory/(topic+'-pool.xml'),pool['sha256'])
    for attempt in manifest['attempts']:
        identity=attempt.get('id')
        if not identity:continue
        url='https://arxiv.org/abs/'+paper_id(identity)
        events=[x for x in manifest['fetches']if x['url']==url and x.get('sha256')]
        if events:put(url,directory/(identity.replace('/','_')+'-abs.html'),events[-1]['sha256'])
        path=attempt.get('complete_download_relative_path')
        if path and attempt.get('pdf_sha256'):
            resolved=(directory/path).resolve()
            if resolved.is_relative_to(directory.resolve()):put('https://arxiv.org/pdf/'+identity,resolved,attempt['pdf_sha256'])
    return cache

def run(seed,reuse_run=None):
    tag='download-'+uuid4().hex[:12];out=ROOT/'data/arxiv-corpus'/tag;out.mkdir(parents=True)
    evidence=ROOT/'evidence/arxiv-ingestion';evidence.mkdir(parents=True,exist_ok=True)
    events=[];fetcher=Fetcher(events,cache=reuse_cache(reuse_run)if reuse_run else None);manifest=dict(run_id=tag,seed=seed,status='RUNNING',sampling='seeded shuffled bounded official category/date metadata pools; not uniform whole-arXiv random',
        query_date_window='2018-01-01 through2024-12-31',pool_size_requested_per_topic=20,target_per_topic=2,topics=list(TOPICS),
        rights='Private local qualification only. Licenses recorded; no redistribution/publication approval.',papers=[],pools={},attempts=[],fetches=events,
        source_sha256=sha(Path(__file__).read_bytes()),parser_image=PARSER_IMAGE,application_db_ingested=False)
    def save():
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        (evidence/(tag+'.json')).write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    used=set();stop=False
    try:
        for topic,categories in TOPICS.items():
            query='('+' OR '.join('cat:'+c for c in categories)+') AND submittedDate:[201801010000 TO 202412312359]'
            url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode(dict(search_query=query,start=0,max_results=20,sortBy='submittedDate',sortOrder='descending'))
            try:
                raw,final=fetcher.fetch(url,256000);(out/(topic+'-pool.xml')).write_bytes(raw);pool=parse_pool(raw,topic)
                order=sample_order(pool,seed,topic);manifest['pools'][topic]=dict(query_url=url,final_url=final,sha256=sha(raw),records=pool,sampled_order=[x['id']for x in order]);save()
            except Exception as error:
                manifest['attempts'].append(dict(topic=topic,stage='metadata_pool',error_type=type(error).__name__,http_status=getattr(error,'code',None)));save()
                if getattr(error,'code',None)in {403,429}:stop=True;break
                continue
            accepted=0
            for record in order:
                if record['base_id']in used:continue
                attempt=dict(topic=topic,id=record['id'],status='ATTEMPTED');manifest['attempts'].append(attempt)
                try:
                    metadata,_=fetcher.fetch(record['abstract_url'],256000);(out/(record['id'].replace('/','_')+'-abs.html')).write_bytes(metadata)
                    license_info=validate_abs(metadata,record)
                    data,final=fetcher.fetch(record['pdf_url'],MAX_BYTES)
                    if final!=record['pdf_url']:raise ValueError('PDF redirect changed pinned version URL')
                    if not data.startswith(b'%PDF-'):raise ValueError('Official response is not original PDF bytes')
                    quarantine=out/'refused-or-pending';quarantine.mkdir(exist_ok=True)
                    stored=quarantine/(topic+'-'+record['id'].replace('/','_')+'.pdf');stored.write_bytes(data)
                    attempt.update(complete_download_relative_path=stored.relative_to(out).as_posix(),pdf_sha256=sha(data),pdf_bytes=len(data))
                    inspected=preflight_pdf(data,record['id']);filename=topic+'-'+record['id'].replace('/','_')+'.pdf';stored.rename(out/filename)
                    attempt['complete_download_relative_path']=filename
                    manifest['papers'].append(dict(record,topic=topic,**license_info,metadata_sha256=sha(metadata),pdf_final_url=final,
                        pdf_relative_path=filename,pdf_sha256=sha(data),pdf_bytes=len(data),fetched_at=utc(),ingestion_preflight=inspected,redistribution_approved=False))
                    used.add(record['base_id']);accepted+=1;attempt.update(status='ACQUIRED',pdf_sha256=sha(data));save()
                    print(json.dumps(dict(topic=topic,acquired=accepted,id=record['id'])),flush=True)
                    if accepted==2:break
                except Exception as error:
                    attempt.update(status='REFUSED_OR_FETCH_FAILED',error_type=type(error).__name__,reason=str(error)[:240],http_status=getattr(error,'code',None));save()
                    if getattr(error,'code',None)in {403,429}:stop=True;break
            if stop:break
        counts={topic:sum(p['topic']==topic for p in manifest['papers'])for topic in TOPICS}
        manifest.update(status='ACQUIRED_PRIVATE'if all(n==2 for n in counts.values())else'PARTIAL',topic_counts=counts,completed_at=utc(),polite_fetch_spacing_verified=all(e['gap_after_previous_end_seconds']is None or e['gap_after_previous_end_seconds']>=3 for e in events),source_unchanged=manifest['source_sha256']==sha(Path(__file__).read_bytes()))
    except Exception as error:manifest.update(status='PARTIAL',error_type=type(error).__name__)
    finally:save()
    print(json.dumps(dict(run_id=tag,status=manifest['status'],papers=len(manifest['papers']),topic_counts=manifest.get('topic_counts'))),flush=True)
    return 0 if manifest['status']=='ACQUIRED_PRIVATE'else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=20261014);parser.add_argument('--reuse-run');args=parser.parse_args();raise SystemExit(run(args.seed,args.reuse_run))
