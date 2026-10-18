"""Seed the local authenticated demo. Reads local API token; never prints it."""
from pathlib import Path
from urllib.request import Request, urlopen
import json


def main():

    root=Path(__file__).resolve().parents[1]
    token=(root/'secrets/api_token.txt').read_text(encoding='utf-8').strip()
    for label,version,path in (
        ('Supplier revision 1','1',root/'datasets/demo/supplier-rev1.txt'),
        ('Supplier revision 2','2',root/'datasets/demo/supplier-rev2.txt'),
    ):
        body=json.dumps({'title':label,'version':version,'text':path.read_text()}).encode()
        req=Request('http://127.0.0.1:8787/v1/documents',body,headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=10) as r:
            print(label,json.loads(r.read())['document_id'])
    req=Request('http://127.0.0.1:8787/v1/claims',headers={'Authorization':f'Bearer {token}'})
    with urlopen(req,timeout=10) as r:
        evidence=json.loads(r.read())
    print('candidate claims:',len(evidence['items']),'conflict groups:',len(evidence['conflicts']))


if __name__ == "__main__":
    main()
