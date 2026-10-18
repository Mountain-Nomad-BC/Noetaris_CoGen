"""Stage separate OCR/author-math evidence without replacing precise native PDF extraction."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ingest_arxiv_corpus import private_file,write,sha
from nsai.ingestion import validate_parsed_source
from nsai.knowledge import assemble_knowledge,attach_embeddings,memory_projection
from nsai.semantic_encoder import LocalSemanticEncoder
from nsai.source_admission import admit_source_path,read_source_bytes
from nsai.assembly import strict_json
OCR_IMAGE='sha256:4b89aa9d705ab684fb54f53748715cff25a5459c10e222883559498d29a7eee9'


def ocr(data,filename,image):
    import re
    if not re.fullmatch('sha256:[a-f0-9]{64}',image):raise ValueError('Exact OCR image digest required')
    name='nsai-arxiv-ocr-'+uuid4().hex[:12];owner=uuid4().hex
    try:
        result=subprocess.run(['docker','run','--name',name,'--label','nsai.owner='+owner,'--network','none','--read-only',
            '--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10001:10001','--cpus','1','--memory','768m',
            '--pids-limit','64','--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=256m,mode=1777','-i','--entrypoint','python',image,'-m','nsai.ocr_worker'],
            input=json.dumps(dict(filename=filename,data=base64.b64encode(data).decode())).encode(),capture_output=True,timeout=135)
        if result.returncode or len(result.stdout)>16*1024*1024:raise ValueError('Bounded OCR worker refused source')
        parsed=json.loads(result.stdout);validate_parsed_source(data,parsed);return parsed
    finally:
        inspected=subprocess.run(['docker','inspect',name],capture_output=True,timeout=15)
        if inspected.returncode==0:
            info=json.loads(inspected.stdout)[0]
            if info['Config'].get('Labels',{}).get('nsai.owner')!=owner:raise RuntimeError('Unowned OCR cleanup refused')
            subprocess.run(['docker','rm','-f',name],check=True,capture_output=True,timeout=20)


def enrich(manifest,author_manifest=None,do_ocr=False,ocr_image=OCR_IMAGE):
    admit_source_path(manifest)
    if author_manifest is not None:admit_source_path(author_manifest)
    raw=read_source_bytes(manifest,8*1024*1024);corpus=strict_json(raw,max_bytes=8*1024*1024,max_depth=32,max_items=100000);tag='enrichment-'+uuid4().hex[:12];folder=manifest.parent/tag;folder.mkdir()
    receipt=dict(run_id=tag,status='RUNNING',prepared_manifest_sha256=sha(raw),papers=[],errors=[],
        ocr_image=ocr_image,scope='Supplemental uncertain extraction; native originals/artifacts preserved. No rendered-equivalence, exhaustive math or correctness claim.')
    encoder=LocalSemanticEncoder(ROOT/'state/models/all-MiniLM-L6-v2');receipt['model_identity']=encoder.identity
    authors={}
    if author_manifest:
        author_raw=read_source_bytes(author_manifest,8*1024*1024)
        source=strict_json(author_raw,max_bytes=8*1024*1024,max_depth=32,max_items=100000);authors={p['id']:p for p in source['papers']}
        receipt['author_source_manifest_sha256']=sha(author_raw)
    def stage_graph(row,spans,kind,payload,output):
        if not spans:return None
        graph=assemble_knowledge(row['document_id'],row['revision'],row['source_sha256'],spans)
        if not graph['source_processing_complete']:raise ValueError('Supplement graph exceeded complete-processing budget')
        graph['extraction_kind']=kind;graph['extraction_evidence_sha256']=sha(json.dumps(payload,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode())
        graph['limitations'].append('Supplement locators refer to this extraction artifact, not native source_spans. OCR/TeX representations are not equivalent to PDF glyph truth.')
        memory=memory_projection(graph,max_bytes=4096,max_items=6)
        passages=[n for n in graph['nodes'] if n['kind']=='passage'];encoded=encoder.encode([n['text'] for n in passages])
        embeddings=dict(vectors={n['id']:v for n,v in zip(passages,encoded['vectors'])},coverage={n['id']:v for n,v in zip(passages,encoded['coverage'])},model_identity=encoder.identity)
        graph['graph_sha256']=sha(json.dumps({k:v for k,v in graph.items() if k!='graph_sha256'},sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
        attach_embeddings(graph,**embeddings)
        return {key:write(output/(key+'.json'),value) for key,value in dict(knowledge=graph,embeddings=embeddings,memory=memory).items()}
    try:
        for row in corpus['papers']:
            result=dict(document_id=row['document_id'],id=row['arxiv']['id'],source_sha256=row['source_sha256'],supplements=[])
            receipt['papers'].append(result);output=folder/row['document_id'];output.mkdir()
            if do_ocr and row['pages_requiring_ocr']:
                try:
                    original=read_source_bytes(private_file(manifest.parent/row['document_id'],row['files']['original']['path']),32*1024*1024)
                    if sha(original)!=row['source_sha256']:raise ValueError('OCR original integrity mismatch')
                    parsed=ocr(original,row['document_id']+'.pdf',ocr_image);ocr_out=output/'ocr';ocr_out.mkdir()
                    rawfile=write(ocr_out/'extraction.json',parsed)
                    spans=[dict(s,locator='ocr:'+s['locator']) for s in parsed['spans'] if s.get('extraction')=='ocr']
                    graphs=stage_graph(row,spans,'ocr_english_uncalibrated',parsed,ocr_out)
                    result['supplements'].append(dict(kind='ocr',folder='ocr',extraction=rawfile,files=graphs,recognized_spans=len(spans),
                        requested_pages=row['pages_requiring_ocr'],pages=parsed['pages'],processing_complete=parsed['complete'],quality_verified=False,math_recognition_supported=False))
                    if not parsed['complete']:
                        receipt['errors'].append(dict(document_id=row['document_id'],kind='ocr',error_type='IncompleteOcrCoverage',message='Some requested pages failed or are unsupported; native evidence retained'))
                except Exception as error:
                    receipt['errors'].append(dict(document_id=row['document_id'],kind='ocr',error_type=type(error).__name__,message=str(error)[:200]))
            source=authors.get(row['arxiv']['id'])
            if source and source.get('artifact_relative_path'):
                try:
                    data=read_source_bytes(private_file(author_manifest.parent,source['artifact_relative_path']),32*1024*1024)
                    if sha(data)!=source['artifact_sha256']:raise ValueError('Author formula artifact SHA mismatch')
                    artifact=json.loads(data)
                    if artifact['pdf_sha256']!=row['source_sha256'] or artifact['document_id']!=row['document_id']:raise ValueError('Author math source binding mismatch')
                    author_out=output/'author_math';author_out.mkdir();rawfile=write(author_out/'formulas-author-source.json',artifact)
                    spans=[dict(locator='author-tex:'+record['id'],text=record['latex']) for record in artifact['records']]
                    graphs=stage_graph(row,spans,'author_tex_math_not_pdf_aligned',artifact,author_out)
                    result['supplements'].append(dict(kind='author_math',folder='author_math',extraction=rawfile,files=graphs,formula_candidates=len(artifact['records']),
                        processing_complete=artifact['processing_complete'],pdf_alignment='not_verified',source_archive_sha256=artifact['source_archive_sha256']))
                    if not artifact['processing_complete']:
                        receipt['errors'].append(dict(document_id=row['document_id'],kind='author_math',error_type='IncompleteAuthorSource',message='Source has explicit unsupported or omitted content'))
                except Exception as error:
                    receipt['errors'].append(dict(document_id=row['document_id'],kind='author_math',error_type=type(error).__name__,message=str(error)[:200]))
            elif author_manifest:
                receipt['errors'].append(dict(document_id=row['document_id'],kind='author_math',error_type='UnavailableAuthorSource'))
            print(json.dumps(dict(document_id=row['document_id'],supplements=len(result['supplements']))),flush=True)
        receipt['status']='STAGED_SCOPED' if not receipt['errors'] else 'PARTIAL'
    finally:
        write(folder/'manifest.json',receipt);write(ROOT/'evidence/arxiv-ingestion'/(tag+'.json'),receipt)
        print(json.dumps(dict(status=receipt['status'],manifest=str((folder/'manifest.json').relative_to(ROOT)),errors=len(receipt['errors']))),flush=True)
    return 0 if receipt['status']=='STAGED_SCOPED' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--author-manifest',type=Path);p.add_argument('--ocr',action='store_true');p.add_argument('--ocr-image',default=OCR_IMAGE);a=p.parse_args()
    if not a.ocr and not a.author_manifest:p.error('Select explicit OCR and/or author-source enrichment')
    raise SystemExit(enrich(a.manifest.resolve(),a.author_manifest.resolve() if a.author_manifest else None,a.ocr,a.ocr_image))
