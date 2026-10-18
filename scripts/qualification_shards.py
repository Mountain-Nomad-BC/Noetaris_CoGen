"""Bounded regression scheduling; complete file groups and exact JUnit coverage."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def case_key(node):
    path,remainder=node.split('::',1)
    if not path.startswith('tests/') or not path.endswith('.py') or '..' in PurePosixPath(path).parts:
        raise ValueError('Unexpected collected test path')
    head,bracket,parameters=remainder.partition('[')
    parts=head.split('::')
    return (path[:-3].replace('/','.')+('.'+'.'.join(parts[:-1]) if len(parts)>1 else ''),
            parts[-1]+('['+parameters if bracket else ''))


def partition(nodes,workers,weights=None):
    if type(workers) is not int or workers not in (1,2) or not nodes or len(nodes)!=len(set(nodes)):
        raise ValueError('Nonempty unique collection and bounded worker count required')
    files={}
    for node in nodes:
        case_key(node);files.setdefault(node.split('::',1)[0],[]).append(node)
    weights=weights or {};groups=[[] for _ in range(workers)];loads=[0.0]*workers
    order={name:index for index,name in enumerate(files)}
    for name in sorted(files,key=lambda name:(-weights.get(name,len(files[name])),order[name])):
        target=min(range(workers),key=lambda index:(loads[index],index))
        groups[target].append(name);loads[target]+=weights.get(name,len(files[name]))
    for group in groups:group.sort(key=order.get)
    if any(not group for group in groups):raise ValueError('Worker group is empty')
    return groups


def timing_weights(path,files):
    if path is None:return {}
    path=Path(path)
    if path.stat().st_size>8*1024*1024:raise ValueError('Timing inventory exceeds bound')
    weights={name:0.0 for name in files}
    for case in ET.parse(path).iter('testcase'):
        classname=case.get('classname','')
        for name in files:
            module=name[:-3].replace('/','.')
            if classname==module or classname.startswith(module+'.'):
                elapsed=float(case.get('time','0'))
                if not math.isfinite(elapsed) or elapsed<0:raise ValueError('Invalid historical test timing')
                weights[name]+=elapsed;break
    return {name:value for name,value in weights.items() if value>0}


def coverage(nodes,xml_paths):
    expected=Counter(case_key(node) for node in nodes);actual=Counter();counts=dict(tests=0,failures=0,errors=0,skipped=0)
    if len(expected)!=len(nodes):raise ValueError('Collected JUnit identities are ambiguous')
    observed_counts=dict(counts)
    combined=ET.Element('testsuites')
    for path in xml_paths:
        if not Path(path).exists():continue
        root=ET.parse(path).getroot()
        for suite in ([root] if root.tag=='testsuite' else root.findall('testsuite')):
            combined.append(suite)
            for key in counts:counts[key]+=int(suite.get(key,'0'))
            for case in suite.iter('testcase'):
                actual[(case.get('classname',''),case.get('name',''))]+=1
                observed_counts['tests']+=1
                for key,tag in [('failures','failure'),('errors','error'),('skipped','skipped')]:
                    observed_counts[key]+=int(case.find(tag) is not None)
    missing=list((expected-actual).elements());extra=list((actual-expected).elements())
    verdict=dict(exact=not missing and not extra and counts['tests']==len(nodes) and counts==observed_counts,
        expected=len(nodes),observed=sum(actual.values()),missing=missing,extra=extra,counts=counts)
    verdict['reported_counts_match_cases']=counts==observed_counts
    return verdict,combined


def execute(root,folder,environment,workers=2,timings=None,budget=1800):
    if workers!=2 or budget!=1800:raise ValueError('Only the explicit two-worker, 1800-second profile is admitted')
    deadline=time.monotonic()+budget
    collect=[sys.executable,'-m','pytest','--collect-only','-q','-o','addopts=']
    result=subprocess.run(collect,cwd=root,env=environment,capture_output=True,text=True,encoding='utf-8',
        errors='replace',timeout=min(120,max(.01,deadline-time.monotonic())))
    (folder/'collection.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Explicit test collection failed')
    nodes=[line.strip() for line in result.stdout.splitlines() if line.startswith('tests/') and '.py::' in line]
    files=list(dict.fromkeys(node.split('::',1)[0] for node in nodes))
    weights=timing_weights(timings,files);groups=partition(nodes,workers,weights)
    (folder/'collection.json').write_text(json.dumps(nodes,indent=2)+'\n',encoding='utf-8')
    (folder/'worker-groups.json').write_text(json.dumps(dict(groups=groups,timing_weights=weights),indent=2)+'\n',encoding='utf-8')
    def run(index):
        command=[sys.executable,'-m','pytest','-q','--maxfail=1','--junitxml='+str(folder/f'tests-worker-{index}.xml'),*groups[index]]
        timed_out=False
        with (folder/f'pytest-worker-{index}.txt').open('x',encoding='utf-8') as output:
            try:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise subprocess.TimeoutExpired(command,0)
                completed=subprocess.run(command,cwd=root,env=environment,stdout=output,stderr=subprocess.STDOUT,timeout=remaining)
                exit_code=completed.returncode
            except subprocess.TimeoutExpired:exit_code=124;timed_out=True
        return dict(worker=index,exit_code=exit_code,timed_out=timed_out,command=command)
    with ThreadPoolExecutor(max_workers=workers) as executor:results=list(executor.map(run,range(workers)))
    verdict,combined=coverage(nodes,[folder/f'tests-worker-{index}.xml' for index in range(workers)])
    (folder/'coverage.json').write_text(json.dumps(verdict,indent=2)+'\n',encoding='utf-8')
    ET.ElementTree(combined).write(folder/'tests.xml',encoding='utf-8',xml_declaration=True)
    passed=(verdict['exact'] and not any(verdict['counts'][key] for key in ('failures','errors','skipped'))
        and all(result['exit_code']==0 for result in results))
    return dict(exit_code=0 if passed else 124 if any(result['timed_out'] for result in results) else 1,
        timed_out=any(result['timed_out'] for result in results),workers=results,coverage_exact=verdict['exact'],
        collected=len(nodes),budget_seconds=budget)


def cleanup_owned(owner,run=subprocess.run):
    if len(owner)!=32 or any(c not in '0123456789abcdef' for c in owner):raise ValueError('Exact qualification owner required')
    removed=[]
    for kind in ('container','network'):
        list_args=['docker','ps','-a'] if kind=='container' else ['docker','network','ls']
        names=run([*list_args,'--filter','label=nsai.owner='+owner,'--format','{{.Names}}' if kind=='container' else '{{.Name}}'],capture_output=True,timeout=30)
        if names.returncode:raise RuntimeError('Owned cleanup inventory unavailable')
        for name in names.stdout.decode().splitlines():
            args=['docker','inspect',name] if kind=='container' else ['docker','network','inspect',name]
            found=run(args,capture_output=True,check=True,timeout=30);data=json.loads(found.stdout)[0]
            labels=(data.get('Config',{}).get('Labels') if kind=='container' else data.get('Labels')) or {}
            if labels.get('nsai.owner')!=owner:raise RuntimeError('Refused foreign qualification cleanup')
            args=['docker','rm','--force',name] if kind=='container' else ['docker','network','rm',name]
            run(args,capture_output=True,check=True,timeout=30);removed.append(dict(kind=kind,name=name))
    for args in (['docker','ps','-a'],['docker','network','ls']):
        remaining=run([*args,'--filter','label=nsai.owner='+owner,'--format','{{.ID}}'],capture_output=True,timeout=30)
        if remaining.returncode or remaining.stdout.strip():raise RuntimeError('Owned qualification cleanup incomplete')
    return dict(complete=True,removed=removed)
