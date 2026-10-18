"""Fresh function-entry observations from the unit suite; not branch or runtime qualification."""
from __future__ import annotations
import ast
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import threading
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]

def main():
    import pytest
    output_directory=ROOT/'evidence/release-validation/function-trace'/uuid4().hex
    output_directory.mkdir(parents=True,exist_ok=False)
    files=sorted((ROOT/'src/nsai').rglob('*.py'))+sorted((ROOT/'scripts').glob('*.py'))
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    inventory=[]
    class Inventory(ast.NodeVisitor):
        def __init__(self,path):self.path=path;self.scope=[]
        def visit_ClassDef(self,node):
            self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
        def visit_FunctionDef(self,node):
            inventory.append(dict(path=self.path,name='.'.join(self.scope+[node.name]),line=node.lineno,
                profile_line=min([node.lineno]+[d.lineno for d in node.decorator_list]),async_=isinstance(node,ast.AsyncFunctionDef)))
            self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
        visit_AsyncFunctionDef=visit_FunctionDef
    for path in files:Inventory(str(path.relative_to(ROOT)).replace('\\','/')).visit(ast.parse(path.read_text(encoding='utf-8-sig')))
    allowed={str(p.resolve()):str(p.relative_to(ROOT)).replace('\\','/') for p in files}
    calls=Counter()
    def observe(frame,event,arg):
        if event=='call':
            relative=allowed.get(frame.f_code.co_filename)
            if relative is not None:calls[(relative,frame.f_code.co_firstlineno,frame.f_code.co_name)]+=1
    previous=sys.getprofile();thread_previous=threading.getprofile()
    try:
        sys.setprofile(observe);threading.setprofile(observe)
        result=int(pytest.main(['-q','--tb=short','--junitxml='+str(output_directory/'unit-tests.xml')]))
    finally:
        sys.setprofile(previous);threading.setprofile(thread_previous)
    for item in inventory:
        item['observed_entries']=calls[(item['path'],item['profile_line'],item['name'].split('.')[-1])]
        item['status']='OBSERVED_IN_UNIT_SUITE' if item['observed_entries'] else 'NOT_OBSERVED_IN_UNIT_SUITE'
    current_files=sorted((ROOT/'src/nsai').rglob('*.py'))+sorted((ROOT/'scripts').glob('*.py'))
    after={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in current_files}
    report=dict(captured_at=datetime.now(timezone.utc).isoformat(),test_exit_code=result,
        source_unchanged=hashes==after,source_hashes=hashes,function_count=len(inventory),
        observed_function_count=sum(i['observed_entries']>0 for i in inventory),functions=inventory,
        limitations=['Entry observations are not branch coverage or correctness proof.',
            'Async resume events may count more than one entry; counts are not invocation or latency measurements.',
            'Dynamic wrappers, subprocess/container code and existing threads are outside this unit-suite observation.',
            'Unobserved operations require their own isolated runtime checks; they must not be exercised on live data automatically.'])
    output=output_directory/'function-trace.json'
    output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['test_exit_code','source_unchanged','function_count','observed_function_count']}))
    return result or (0 if report['source_unchanged'] else 1)

if __name__=='__main__':raise SystemExit(main())
