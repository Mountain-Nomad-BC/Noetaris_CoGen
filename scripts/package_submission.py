"""Build an unapproved documentation candidate from an exact reviewed allowlist."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import os
from zipfile import ZipFile, ZIP_DEFLATED
from release_audit import MANIFEST,audit_payloads,audit_archive,member_name
ROOT=Path(__file__).resolve().parents[1]
DOCUMENT_ALLOWLIST=('NOTICE','docs/implementation-provenance.md','datasets/synthetic/README.md','assets/pdfjs/LICENSE','assets/pdfjs/provenance.json')

def local_secret_values(root):
    directory=Path(root)/'secrets';values=[]
    if directory.is_dir():
        for path in directory.glob('*.txt'):
            if path.is_symlink() or path.stat().st_size>4096:raise ValueError('Secret hygiene input must be bounded regular files')
            values.append(path.read_bytes().strip())
    return values

def build_candidate(root,destination,allowlist,*,review):
    root=Path(root).resolve();destination=Path(destination)
    if not isinstance(review,dict) or not isinstance(review.get('review_id'),str) or not review['review_id'].strip() or not isinstance(review.get('reviewer'),str) or not review['reviewer'].strip() or review.get('disposition')!='reviewed-candidate' or review.get('publication_approved') is not False:raise ValueError('Candidate provenance/privacy review receipt is required; publication is never admitted')
    payloads=[]
    for name in allowlist:
        name=member_name(name);path=root.joinpath(*name.split('/'))
        for component in [path,*path.parents]:
            if component==root.parent:break
            if component.is_symlink() or (hasattr(component,'is_junction') and component.is_junction()):raise ValueError('Candidate members and parents must not be symlinks or junctions')
        if not path.resolve(strict=True).is_relative_to(root) or not path.is_file():raise ValueError('Candidate source must be a regular file within staging root')
        if path.stat().st_size>15*1024*1024:raise ValueError('Candidate member exceeds budget')
        payloads.append((name,path.read_bytes()))
    records=audit_payloads(payloads,forbidden_values=local_secret_values(root))
    by_name=dict(payloads)
    if 'assets/pdfjs/provenance.json' in by_name:
        dependency=json.loads(by_name['assets/pdfjs/provenance.json'])
        if dependency.get('license')!='Apache-2.0' or not isinstance(dependency.get('files'),dict):raise ValueError('Renderer license/provenance contract invalid')
        for dependency_name,digest in dependency['files'].items():
            archive_name='assets/pdfjs/'+member_name(dependency_name)
            if archive_name in by_name and hashlib.sha256(by_name[archive_name]).hexdigest()!=digest:raise ValueError('Renderer dependency integrity mismatch')
    if review.get('members')!=records:raise ValueError('Review receipt is stale or does not cover exact members')
    if any(name.startswith('assets/pdfjs/') and name not in {'assets/pdfjs/LICENSE','assets/pdfjs/provenance.json'} for name,_ in payloads):
        if not {'assets/pdfjs/LICENSE','assets/pdfjs/provenance.json'}<=set(name for name,_ in payloads):raise ValueError('Bundled renderer requires upstream license and integrity provenance')
    manifest={'members':records,'privacy_qualification':'offline-limited','license_qualification':'not-certified','publication_approved':False,'review':{'disposition':review['disposition'],'review_id':review.get('review_id'),'reviewer':review.get('reviewer')}}
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():raise ValueError('Candidate output already exists; preserve prior archive and choose a unique destination')
    with tempfile.NamedTemporaryFile(prefix='candidate-',suffix='.zip',dir=destination.parent,delete=False) as temporary:tmp=Path(temporary.name)
    try:
        with ZipFile(tmp,'w',ZIP_DEFLATED) as archive:
            for name,data in payloads:archive.writestr(name,data)
            archive.writestr(MANIFEST,json.dumps(manifest,indent=2,allow_nan=False).encode())
        report=audit_archive(tmp,expected_allowlist=allowlist,forbidden_values=local_secret_values(root))
        # Exclusive creation prevents concurrent outputs from being overwritten.
        os.link(tmp,destination)
        report['source_code_included']=any(name.startswith(('src/','scripts/')) for name in allowlist)
        report['review_id']=review.get('review_id');return report
    finally:tmp.unlink(missing_ok=True)

def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--review-receipt',required=True,type=Path);parser.add_argument('--destination',required=True,type=Path);args=parser.parse_args(argv)
    try:report=build_candidate(ROOT,args.destination,DOCUMENT_ALLOWLIST,review=json.loads(args.review_receipt.read_text()))
    except (ValueError,OSError) as error:print('FAIL:',error);return 1
    print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
