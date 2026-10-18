"""Independent synthetic ink-box oracle; never enables an OCR service."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time,uuid

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'evidence/implementation/ocr-geometry'
IMAGE='sha256:4b89aa9d705ab684fb54f53748715cff25a5459c10e222883559498d29a7eee9'
POLICY=dict(pages=4,words_per_page=12,font_sizes=[32,40,48,56],image_size=[1200,1500],dpi=300,iou_threshold=.80,minimum_joint_fraction=.95,maximum_unmatched_predictions=0,text_match='Unicode casefold exact; no edit-distance correction',pairing='per-page exact-text maximum-IoU one-to-one; labels unique per page',oracle='independently rendered per-word raster ink below gray128',tuning='no post-result tuning; cohort frozen before actual OCR')
LINES=['Pump Valve Inlet Rotor','Inspect Clean Tighten Replace','before after maximum minimum']

def overlap(a,b):
    left=max(a[0],b[0]);top=max(a[1],b[1]);right=min(a[2],b[2]);bottom=min(a[3],b[3])
    shared=max(0,right-left)*max(0,bottom-top)
    area_a=max(0,a[2]-a[0])*max(0,a[3]-a[1]);area_b=max(0,b[2]-b[0])*max(0,b[3]-b[1])
    return shared/(area_a+area_b-shared) if area_a+area_b>shared else 0

def evaluate(labels,predictions,threshold=.8):
    remaining=set(range(len(predictions)));pairs=[];missing=[]
    for label in labels:
        candidates=[i for i in remaining if predictions[i]['page']==label['page'] and predictions[i]['text'].casefold()==label['text'].casefold()]
        if not candidates:missing.append(label);continue
        selected=max(candidates,key=lambda i:overlap(label['ink_box'],predictions[i]['pixel_box']))
        remaining.remove(selected);score=overlap(label['ink_box'],predictions[selected]['pixel_box'])
        pairs.append(dict(label=label,prediction=predictions[selected],iou=score,geometry_pass=score>=threshold))
    extras=[predictions[i] for i in sorted(remaining)];joint=sum(p['geometry_pass'] for p in pairs)
    return dict(labels=len(labels),predictions=len(predictions),text_matches=len(pairs),joint_text_geometry_matches=joint,unmatched_truth=missing,unmatched_predictions=extras,pairs=pairs,text_recall=len(pairs)/len(labels) if labels else None,joint_recall=joint/len(labels) if labels else None,text_precision=len(pairs)/len(predictions) if predictions else None)

def prepare():
    from PIL import Image,ImageDraw,ImageFont,ImageChops,__version__ as pillow_version
    from pypdf import PdfWriter,__version__ as pypdf_version
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject,NumberObject
    OUTPUT.mkdir(parents=True,exist_ok=True)
    if (OUTPUT/'frozen-manifest.json').exists():raise RuntimeError('Frozen cohort already exists; refuse regeneration')
    writer=PdfWriter();labels=[];images=[]
    for number,size in enumerate(POLICY['font_sizes'],1):
        font=ImageFont.load_default(size=size);image=Image.new('L',(1200,1500),255)
        for line_index,line in enumerate(LINES):
            x=75+number*3;y=100+line_index*150
            for word in line.split():
                mask=Image.new('L',image.size,255);draw=ImageDraw.Draw(mask);draw.text((x,y),word,font=font,fill=0)
                ink=ImageChops.invert(mask).point(lambda value:255 if value>127 else 0).getbbox()
                if ink is None or ink[2]>=1200:raise ValueError('Fixture ink outside fixed raster')
                labels.append(dict(page=number,text=word,ink_box=list(ink),font_size=size))
                image=ImageChops.darker(image,mask);x+=int(font.getlength(word))+32
        name=f'page-{number}.png';image.save(OUTPUT/name);images.append(dict(file=name,sha256=hashlib.sha256((OUTPUT/name).read_bytes()).hexdigest()))
        page=writer.add_blank_page(width=288,height=360);stream=DecodedStreamObject();stream.set_data(image.tobytes())
        stream.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(1200),NameObject('/Height'):NumberObject(1500),NameObject('/ColorSpace'):NameObject('/DeviceGray'),NameObject('/BitsPerComponent'):NumberObject(8)})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/OriginalRaster'):writer._add_object(stream.flate_encode())})})
        content=DecodedStreamObject();content.set_data(b'q 288 0 0 360 0 0 cm /OriginalRaster Do Q');page[NameObject('/Contents')]=writer._add_object(content)
    with (OUTPUT/'original-raster.pdf').open('wb') as destination:writer.write(destination)
    manifest=dict(policy=POLICY,labels=labels,images=images,pdf_sha256=hashlib.sha256((OUTPUT/'original-raster.pdf').read_bytes()).hexdigest(),host_pillow=pillow_version,host_pypdf=pypdf_version,font='Pillow bundled Aileron Regular, No Rights Reserved per original creator',font_source='https://dotcolon.net/fonts/aileron/',font_loader_source='https://pillow.readthedocs.io/en/stable/reference/ImageFont.html',script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUTPUT/'frozen-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'prepared_pages':4,'labels':len(labels),'pdf_sha256':manifest['pdf_sha256']}))

def run():
    manifest=json.loads((OUTPUT/'frozen-manifest.json').read_text());assert manifest['policy']==POLICY
    assert hashlib.sha256((OUTPUT/'original-raster.pdf').read_bytes()).hexdigest()==manifest['pdf_sha256']
    name='nsai-ocr-geometry-'+uuid.uuid4().hex[:12];owner=uuid.uuid4().hex
    program="from pathlib import Path;import json;from nsai.ocr_worker import extract_ocr;print(json.dumps(extract_ocr(Path('/fixtures/original-raster.pdf').read_bytes(),'original-raster.pdf')))"
    args=['docker','run','-d','--name',name,'--label','nsai.geometry.owner='+owner,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10002:10002','--cpus','1','--memory','768m','--pids-limit','64','--tmpfs','/tmp:rw,noexec,nosuid,size=128m','--mount',f'type=bind,source={OUTPUT},target=/fixtures,readonly','--entrypoint','python',IMAGE,'-c',program]
    receipt=dict(image_id=IMAGE,policy=POLICY,owned_name=name,status='RUNNING',manifest_sha256=hashlib.sha256((OUTPUT/'frozen-manifest.json').read_bytes()).hexdigest());start=time.monotonic();created=False
    try:
        subprocess.run(args,check=True,capture_output=True,timeout=30);created=True
        waited=subprocess.run(['docker','wait',name],check=True,capture_output=True,timeout=120)
        logs=subprocess.run(['docker','logs',name],check=True,capture_output=True,timeout=15);(OUTPUT/'worker-output.json').write_bytes(logs.stdout);(OUTPUT/'worker-stderr.txt').write_bytes(logs.stderr)
        receipt['exit_code']=int(waited.stdout);receipt['elapsed_seconds']=time.monotonic()-start
        if receipt['exit_code']:raise RuntimeError('Actual OCR worker failed; diagnostics retained')
        parsed=json.loads(logs.stdout);result=evaluate(manifest['labels'],parsed['ocr_words'],POLICY['iou_threshold'])
        result['cohort_gate_pass']=result['joint_recall']>=POLICY['minimum_joint_fraction'] and len(result['unmatched_predictions'])<=POLICY['maximum_unmatched_predictions']
        result['generalization']='Only four synthetic English Aileron raster pages at identity300DPI; no real-domain, other-font, crop, rotation, handwriting, formula or general OCR accuracy qualification'
        (OUTPUT/'results.json').write_text(json.dumps(result,indent=2));receipt.update(status='PASS' if result['cohort_gate_pass'] else 'THRESHOLD_NOT_MET',result_summary={k:result[k] for k in ('labels','predictions','text_matches','joint_text_geometry_matches','joint_recall','text_precision','text_recall','cohort_gate_pass')})
        info=json.loads(subprocess.run(['docker','inspect',name],check=True,capture_output=True,timeout=15).stdout)[0];h=info['HostConfig'];assert h['NetworkMode']=='none' and not h['PortBindings'] and h['ReadonlyRootfs'] and h['NanoCpus']==1000000000 and h['Memory']==768*1024*1024
        receipt['resource_policy']=dict(nano_cpus=h['NanoCpus'],memory_bytes=h['Memory'],readonly=True,no_ports=True,network='none')
    except Exception as error:receipt.update(status='EXECUTION_FAILED',failure_type=type(error).__name__);raise
    finally:
        if created:
            info=json.loads(subprocess.run(['docker','inspect',name],check=True,capture_output=True,timeout=15).stdout)[0]
            if info['Config']['Labels'].get('nsai.geometry.owner')!=owner:raise RuntimeError('Refused cleanup of unowned resource')
            removed=subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=30);receipt['cleanup_complete']=removed.returncode==0
        (OUTPUT/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt));return 0 if receipt['status']=='PASS' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if args.prepare:prepare()
    if args.run:raise SystemExit(run())
