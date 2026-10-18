"""Frozen synthetic crop/right-angle ink oracle against the real isolated OCR image."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
SEED=ROOT/'evidence/ocr-geometry-requalification/6115e87c2baf4737b6f639bac749ae55'
sys.path.insert(0,str(ROOT/'scripts'))
from check_release_readiness import source_snapshot
from qualify_ocr_geometry import evaluate,overlap


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(folder):
    from PIL import Image
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject,NumberObject,RectangleObject
    manifest=json.loads((SEED/'frozen-manifest.json').read_bytes())
    expected=next(item['sha256'] for item in manifest['images'] if item['file']=='page-4.png')
    assert sha(SEED/'page-4.png')==expected
    image=Image.open(SEED/'page-4.png').convert('L');assert image.size==(1200,1500)
    folder.mkdir(parents=True,exist_ok=False)
    writer=PdfWriter();labels=[];cases=[]
    for number,angle in enumerate((0,90,180,270),1):
        width,height=(360,288) if angle in {90,270} else (288,360)
        left,bottom=20,30;right,top=left+width,bottom+height
        page=writer.add_blank_page(width=width+80,height=height+80)
        page.cropbox=RectangleObject([left,bottom,right,top]);page.rotate(angle)
        stream=DecodedStreamObject();stream.set_data(image.tobytes())
        stream.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),
            NameObject('/Width'):NumberObject(1200),NameObject('/Height'):NumberObject(1500),
            NameObject('/ColorSpace'):NameObject('/DeviceGray'),NameObject('/BitsPerComponent'):NumberObject(8)})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im1'):writer._add_object(stream.flate_encode())})})
        # Independently specified image placements keep the known raster upright
        # after intrinsic page rotation. PDF and raster axes must still agree.
        placement={0:(288,0,0,360,left,bottom),90:(0,288,-360,0,right,bottom),
            180:(-288,0,0,-360,right,top),270:(0,-288,360,0,left,top)}[angle]
        content=DecodedStreamObject();content.set_data(('q '+' '.join(map(str,placement))+' cm /Im1 Do Q').encode())
        page[NameObject('/Contents')]=writer._add_object(content)
        cases.append(dict(page=number,rotation=angle,crop=[left,bottom,right,top],expected_raster_size=[1200,1500]))
        for original in (item for item in manifest['labels'] if item['page']==4):
            x0,y0,x1,y1=[value*.24 for value in original['ink_box']]
            box={0:[left+x0,top-y1,left+x1,top-y0],
                 90:[left+y0,bottom+x0,left+y1,bottom+x1],
                 180:[right-x1,bottom+y0,right-x0,bottom+y1],
                 270:[right-y1,top-x1,right-y0,top-x0]}[angle]
            labels.append(dict(page=number,text=original['text'],ink_box=original['ink_box'],expected_pdf_ink_box=box))
    buffer=BytesIO();writer.write(buffer);(folder/'original-raster.pdf').write_bytes(buffer.getvalue())
    frozen=dict(schema='nsai.ocr-right-angle-oracle/1',cases=cases,labels=labels,
        pdf_sha256=sha(folder/'original-raster.pdf'),seed_manifest_sha256=sha(SEED/'frozen-manifest.json'),
        seed_image_sha256=expected,script_sha256=sha(Path(__file__)),
        policy=dict(dpi=300,iou_threshold=.80,required_text_geometry_fraction=1.0,unmatched_predictions=0,
            oracle='Prior frozen independent per-word raster ink; original PDF corner coordinates specified before worker results',
            scope='Synthetic upright raster under intrinsic right-angle page rotation and offset crop; not arbitrary skew, UserUnit, sideways recognition or general OCR quality'))
    (folder/'frozen-manifest.json').write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
    return frozen


def run(folder):
    if (folder/'receipt.json').exists():raise RuntimeError('Existing evidence must not be overwritten; prepare a new owned fixture directory')
    manifest=json.loads((folder/'frozen-manifest.json').read_bytes())
    assert manifest['schema']=='nsai.ocr-right-angle-oracle/1' and sha(folder/'original-raster.pdf')==manifest['pdf_sha256']
    owner=uuid4().hex;name='nsai-ocr-right-angle-'+owner[:12]
    identity=subprocess.run(['docker','image','inspect','nsai-ocr-hardened-candidate:local','--format','{{.Id}}'],capture_output=True,check=True,timeout=30).stdout.decode().strip()
    report=dict(status='FAIL',image=identity,source_before=source_snapshot(ROOT),fixture_sha256=sha(folder/'frozen-manifest.json'),
        script_sha256=sha(Path(__file__)),private_http_admitted=False,live_services_accessed=False,release_approved=False)
    program="import json;from pathlib import Path;from nsai.ocr_worker import extract_ocr;print(json.dumps(extract_ocr(Path('/fixtures/original-raster.pdf').read_bytes(),'original-raster.pdf')))"
    created=False;started=time.monotonic()
    try:
        command=['docker','run','-d','--name',name,'--label','nsai.owner='+owner,'--network','none','--read-only',
            '--cap-drop','ALL','--security-opt','no-new-privileges:true','--user','10002:10002','--cpus','1','--memory','768m',
            '--pids-limit','64','--tmpfs','/tmp:rw,noexec,nosuid,size=128m',
            '--mount','type=bind,source='+str(folder)+',target=/fixtures,readonly','--entrypoint','python',identity,'-c',program]
        subprocess.run(command,capture_output=True,check=True,timeout=30);created=True
        waited=subprocess.run(['docker','wait',name],capture_output=True,check=True,timeout=160)
        logs=subprocess.run(['docker','logs',name],capture_output=True,check=True,timeout=15)
        (folder/'worker-output.json').write_bytes(logs.stdout);(folder/'worker-errors.txt').write_bytes(logs.stderr)
        assert waited.stdout.strip()==b'0','Actual OCR worker failed; diagnostics retained'
        parsed=json.loads(logs.stdout);assert parsed['complete'] and all(p['status']=='ocr' for p in parsed['pages'])
        result=evaluate(manifest['labels'],parsed['ocr_words'],manifest['policy']['iou_threshold'])
        for pair in result['pairs']:
            pair['original_pdf_ink_iou']=overlap(pair['label']['expected_pdf_ink_box'],pair['prediction']['pdf_box'])
        result['original_pdf_geometry_pass']=all(p['original_pdf_ink_iou']>=.8 for p in result['pairs'])
        (folder/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        assert result['joint_recall']==1 and not result['unmatched_predictions'] and result['original_pdf_geometry_pass']
        report.update(status='PASS_SCOPED',pages=4,words=48,all_right_angles=True,offset_crops=True,
            raster_ink_and_original_pdf_geometry=True,scope=manifest['policy']['scope'])
    except Exception as error:report.update(failure_type=type(error).__name__,failure=str(error)[:300])
    finally:
        if created:
            info=json.loads(subprocess.run(['docker','inspect',name],capture_output=True,check=True,timeout=15).stdout)[0]
            assert info['Config']['Labels'].get('nsai.owner')==owner
            report['cleanup_complete']=subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=30).returncode==0
        else:report['cleanup_complete']=True
        report['source_after']=source_snapshot(ROOT);report['elapsed_seconds']=time.monotonic()-started
        if report['source_before']!=report['source_after'] or not report['cleanup_complete']:report['status']='FAIL'
        report['artifacts_sha256']={p.name:sha(p) for p in folder.iterdir() if p.is_file() and p.name!='receipt.json'}
        (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report.get(k) for k in ('status','image','failure','cleanup_complete')}))
    return 0 if report['status']=='PASS_SCOPED' else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');parser.add_argument('--folder',type=Path,required=True)
    args=parser.parse_args();folder=args.folder.resolve()
    assert folder.is_relative_to((ROOT/'evidence/ocr-right-angles').resolve()) and not folder.is_symlink()
    if args.prepare:prepare(folder);print(str(folder))
    if args.run:raise SystemExit(run(folder))
