"""Bounded read-only data inventory; private findings, no ingestion or acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nsai.source_health import inspect_file,audit_bytes
from check_release_readiness import source_snapshot


def collect_paths(roots,deadline,*,max_directories=10000,max_names=100000):
    selected=set();blocked=[];pending=list(roots);visited=set();names=0
    while pending:
        if time.monotonic()>deadline:raise ValueError('inventory_walk_time_budget')
        directory=Path(pending.pop())
        if directory in visited:continue
        visited.add(directory)
        if len(visited)>max_directories:raise ValueError('inventory_directory_budget')
        info=directory.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            blocked.append(dict(path=str(directory),code='directory_link_refused'));continue
        with os.scandir(directory) as entries:
            for entry in entries:
                names+=1
                if names>max_names:raise ValueError('inventory_name_budget')
                if time.monotonic()>deadline:raise ValueError('inventory_walk_time_budget')
                path=Path(entry.path);info=entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
                    blocked.append(dict(path=str(path),code='filesystem_link_refused'));continue
                if stat.S_ISDIR(info.st_mode):
                    if len(pending)+len(visited)>=max_directories:raise ValueError('inventory_directory_budget')
                    pending.append(path)
                elif path.suffix.casefold() in {'.json','.jsonl'}:
                    selected.add(path)
                    if len(selected)>2000:raise ValueError('inventory_file_budget')
    return selected,blocked


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root',type=Path,action='append',required=True)
    args=cli.parse_args();roots=[]
    if len(args.root)>16:cli.error('At most 16 explicit audit roots are admitted')
    for value in args.root:
        root=value.absolute()
        for part in (root,*root.parents):
            info=part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
                cli.error('Audit roots cannot use filesystem links')
        root=root.resolve()
        if not root.is_dir() or not any(root.is_relative_to(ROOT/area) for area in ('data','datasets','evaluations')):
            cli.error('Select explicit existing data, datasets or evaluations roots in this workspace')
        roots.append(root)
    run=uuid4().hex;private=ROOT/'state/source-health'/run;private.mkdir(parents=True,exist_ok=False)
    if os.name=='nt':
        subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts/protect-secrets.ps1'),'-PrivatePaths',str(private)],
                       check=True,capture_output=True,timeout=30)
    else:private.chmod(0o700)
    folder=ROOT/'evidence/source-health'/run;folder.mkdir(parents=True,exist_ok=False)
    (folder/'fixture.py').write_bytes(Path(__file__).read_bytes())
    before=source_snapshot(ROOT);start=time.monotonic();details=[];selected=set();blocked=[];total=0;complete=True
    report=dict(status='FAIL',run_id=run,scope=[root.relative_to(ROOT).as_posix() for root in roots],
                source_before=before,release_approved=False,originals_modified=False,
                semantic_truth_qualified=False,canonical_family_schemas_qualified=False)
    try:
        selected,blocked=collect_paths(roots,start+120)
        for item in blocked:item['path']=Path(item['path']).relative_to(ROOT).as_posix()
        for path in sorted(selected):
            if time.monotonic()-start>120:raise ValueError('inventory_time_budget')
            size=path.lstat().st_size;total+=size
            if total>512*1024*1024:raise ValueError('inventory_byte_budget')
            entry=dict(path=path.relative_to(ROOT).as_posix())
            try:entry.update(inspect_file(path))
            except (ValueError,OSError) as error:
                # Keep filenames/identifiers and diagnostics in the private
                # report; public receipt contains only aggregate counts/hash.
                entry.update(audit_complete=False,error_type=type(error).__name__,error=str(error)[:200])
            details.append(entry)
        unchanged=True
        for entry in details:
            if 'sha256' not in entry:continue
            if time.monotonic()-start>120:raise ValueError('inventory_recheck_budget')
            try:same=hashlib.sha256(audit_bytes(ROOT/entry['path'])).hexdigest()==entry['sha256']
            except (ValueError,OSError):same=False
            unchanged=unchanged and same
        complete=not blocked and all(entry.get('audit_complete') is True for entry in details)
        issue_count=sum(len(entry.get('issues',[])) for entry in details)
        report.update(status='PASS_INVENTORY_WITH_FINDINGS' if complete and unchanged else 'INCOMPLETE',
            selected_files=len(selected),inspected_files=len(details),inspected_bytes=total,
            findings=issue_count,parse_or_read_failures=sum('error' in entry for entry in details),
            link_exclusions=len(blocked),inventory_complete=complete,selected_originals_unchanged=unchanged,
            unclassified_files=sum(entry.get('schema_status','').startswith('unclassified') for entry in details))
    except (ValueError,OSError) as error:report.update(status='INCOMPLETE',failure_type=type(error).__name__,
        failure=str(error)[:200] if isinstance(error,ValueError) else 'Filesystem inventory failed; details remain private')
    raw=json.dumps(dict(files=details,excluded_paths=blocked),indent=2,ensure_ascii=True,allow_nan=False).encode('utf-8')
    if len(raw)>32*1024*1024:raise ValueError('Private findings envelope exceeds budget')
    with (private/'findings.json').open('xb') as output:output.write(raw)
    if os.name!='nt':(private/'findings.json').chmod(0o600)
    report.update(private_report_sha256=hashlib.sha256(raw).hexdigest(),private_report=str((private/'findings.json').relative_to(ROOT)),
        source_after=source_snapshot(ROOT),elapsed_seconds=round(time.monotonic()-start,3),
        limitations=['Explicit selected roots only; filesystem arrival/removal races and unselected data not qualified.',
                    'Generic JSON/JSONL/graph shapes only; source reference closure, factual support, semantic completeness and canonical-family schemas remain separate checks.',
                    'Known excluded names may be inspected here for failure analysis; no files are admitted, indexed, rewritten, deleted or promoted.'])
    report['tool_sources_unchanged']=before==report['source_after']
    if not report['tool_sources_unchanged']:report['status']='FAIL'
    (folder/'receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report.get(key) for key in ('status','run_id','inspected_files','findings','parse_or_read_failures','inventory_complete','selected_originals_unchanged')}))
    return 0 if report['status']=='PASS_INVENTORY_WITH_FINDINGS' else 1


if __name__=='__main__':raise SystemExit(main())
