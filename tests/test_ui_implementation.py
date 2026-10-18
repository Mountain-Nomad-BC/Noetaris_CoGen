"""Supply-chain and deployment packaging contracts for private renderer assets."""
from pathlib import Path
import hashlib
import json
import re
ROOT=Path(__file__).resolve().parents[1]
def test_pinned_renderer_assets_have_matching_digests_and_license():
    directory=ROOT/"assets/pdfjs"
    receipt=json.loads((directory/"provenance.json").read_text())
    assert receipt["version"]=="6.4.299"
    assert receipt["source"]=="https://registry.npmjs.org/pdfjs-dist/-/pdfjs-dist-6.4.299.tgz"
    assert receipt["license"]=="Apache-2.0"
    assert set(receipt["files"])=={"pdf.mjs","pdf.worker.mjs","LICENSE"}
    for name,digest in receipt["files"].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest()==digest


def test_pinned_standard_fonts_keep_separate_licenses_and_public_delivery():
    from fastapi.testclient import TestClient
    from nsai.api import app
    directory=ROOT/'assets/pdfjs';base=json.loads((directory/'provenance.json').read_text())
    raw=(directory/'standard_fonts/provenance.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==base['additional_components']['standard_fonts/provenance.json']
    fonts=json.loads(raw)
    declared=re.search(r'PDF_FONT_SHA256=Object.freeze\((\{[^\n]+\})\);',(ROOT/'assets/app.js').read_text(encoding='utf-8')).group(1)
    assert json.loads(declared)=={name:digest for name,digest in fonts['files'].items() if name.endswith(('.ttf','.pfb'))}
    assert fonts['npm_integrity']==base['npm_integrity'] and fonts['source']==base['source']
    assert {'LICENSE_FOXIT','LICENSE_LIBERATION'}<=set(fonts['files'])
    with TestClient(app) as client:
        for name,digest in fonts['files'].items():
            response=client.get('/assets/pdfjs/standard_fonts/'+name)
            assert response.status_code==200
            assert hashlib.sha256(response.content).hexdigest()==digest
        assert client.get('/assets/pdfjs/standard_fonts/unlisted.ttf').status_code==404
