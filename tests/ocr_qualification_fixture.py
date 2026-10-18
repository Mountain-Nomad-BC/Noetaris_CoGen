"""Original synthetic raster PDF qualification inside the isolated OCR image."""
import base64
from io import BytesIO
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import os
import threading
import urllib.request
import urllib.error
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject,NumberObject
from nsai.ocr_worker import extract_ocr
from nsai.ingestion import parse_source

def native_pdf():
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    text=DecodedStreamObject();text.set_data(b'BT /F1 20 Tf 72 720 Td (Pump maximum temperature is 75 C.) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(text)
    output=BytesIO();writer.write(output);return output.getvalue()

def raster_pdf():
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder);(path/'native.pdf').write_bytes(native_pdf())
        subprocess.run(['pdftoppm','-singlefile','-gray','-r','100',str(path/'native.pdf'),str(path/'raster')],check=True,timeout=10)
        pgm=(path/'raster.pgm').read_bytes()
    header,data=pgm.split(b'\n255\n',1)
    lines=[line for line in header.splitlines()[1:] if not line.startswith(b'#')]
    width,height=map(int,b' '.join(lines).split())
    writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
    image=DecodedStreamObject();image.set_data(data)
    image.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(width),NameObject('/Height'):NumberObject(height),NameObject('/ColorSpace'):NameObject('/DeviceGray'),NameObject('/BitsPerComponent'):NumberObject(8)})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/XObject'):DictionaryObject({NameObject('/Im1'):writer._add_object(image.flate_encode())})})
    stream=DecodedStreamObject();stream.set_data(b'q 612 0 0 792 0 0 cm /Im1 Do Q')
    page[NameObject('/Contents')]=writer._add_object(stream)
    output=BytesIO();writer.write(output);return output.getvalue()

def main():
    cases=[];data=raster_pdf()
    parsed=parse_source(data,'scanned.pdf')
    cases.append(dict(case='scanned_page_detected',pass_=not parsed['spans'] and parsed['pages'][0]['status']=='ocr_required'))
    start=time.monotonic();result=extract_ocr(data,'scanned.pdf');duration=time.monotonic()-start
    observed=result['raw_text'];expected='Pump maximum temperature is 75 C.'
    cases.append(dict(case='real_printed_english_exact',pass_=observed==expected,expected=expected,actual=observed,seconds=duration))
    cases.append(dict(case='geometry_and_score_meaning',pass_=bool(result['ocr_words']) and all(not w['engine_score_is_probability'] and len(w['pdf_box'])==4 for w in result['ocr_words'])))
    cases.append(dict(case='original_custody',pass_=result['original_sha256']==hashlib.sha256(data).hexdigest()))
    try:extract_ocr(data,'scanned.pdf',language='fra')
    except ValueError:cases.append(dict(case='unsupported_language_refused',pass_=True))
    else:cases.append(dict(case='unsupported_language_refused',pass_=False))
    writer=PdfWriter();writer.add_blank_page(width=20000,height=20000);out=BytesIO();writer.write(out)
    # Add raster marker through original fixture mutation for before-render guard.
    from pypdf import PdfReader
    reader=PdfReader(BytesIO(data));writer=PdfWriter();writer.add_page(reader.pages[0]);writer.pages[0].mediabox.upper_right=(20000,20000);out=BytesIO();writer.write(out)
    try:extract_ocr(out.getvalue(),'giant.pdf')
    except ValueError as error:cases.append(dict(case='pixels_rejected_before_renderer',pass_='pixel budget' in str(error)))
    else:cases.append(dict(case='pixels_rejected_before_renderer',pass_=False))
    writer=PdfWriter();writer.add_page(reader.pages[0]);writer.pages[0][NameObject('/UserUnit')]=NumberObject(2);out=BytesIO();writer.write(out)
    scaled=extract_ocr(out.getvalue(),'scaled.pdf')
    cases.append(dict(case='unsupported_UserUnit_withheld',pass_=scaled['pages'][0]['status']=='unsupported' and not scaled['complete']))
    from nsai.ocr_server import Handler,ThreadingHTTPServer
    with tempfile.TemporaryDirectory() as folder:
        secret=Path(folder)/'token';secret.write_text('synthetic-qualification-token-0123456789abcdef')
        os.environ['NSAI_OCR_TOKEN_FILE']=str(secret)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        payload=json.dumps(dict(filename='scanned.pdf',data=base64.b64encode(data).decode(),language='eng')).encode()
        url=f'http://127.0.0.1:{server.server_port}/ocr'
        try:
            request=urllib.request.Request(url,data=payload,headers={'Content-Type':'application/json'})
            try:urllib.request.urlopen(request,timeout=10)
            except urllib.error.HTTPError as error:cases.append(dict(case='service_unauthorized',pass_=error.code==401 and error.headers['Cache-Control']=='no-store'))
            else:cases.append(dict(case='service_unauthorized',pass_=False))
            request=urllib.request.Request(url,data=payload,headers={'Content-Type':'application/json','Authorization':'Bearer '+secret.read_text()})
            with urllib.request.urlopen(request,timeout=15) as response:
                parsed=json.load(response)
                cases.append(dict(case='service_real_child_ocr',pass_=parsed['raw_text']==expected and parsed['pages'][0]['status']=='ocr'))
        finally:server.shutdown();server.server_close();thread.join()
    version=subprocess.run(['tesseract','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0]
    print(json.dumps(dict(cases=cases,all_pass=all(c['pass_'] for c in cases),tesseract=version,source_sha256=hashlib.sha256(data).hexdigest(),fixture='original synthetic Helvetica raster page; not heldout calibration',limits=['one clean synthetic page only','UserUnit transforms withheld; right-angle/crop acceptance requires its separate oracle','English printed only; handwriting/formula unsupported','quality thresholds not calibrated'])))
    return 0 if all(c['pass_'] for c in cases) else 1

if __name__=='__main__':raise SystemExit(main())
