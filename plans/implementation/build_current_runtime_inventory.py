"""Refresh static owned-code inventory; never infer executed coverage or acceptance."""
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_release_readiness import source_snapshot


def digest(value):return hashlib.sha256(value).hexdigest()


def main():
    before=source_snapshot(ROOT);functions=[];routes=[];javascript=[];handlers=[]
    owned_python=[*(ROOT/'src/nsai').rglob('*.py'),*(ROOT/'scripts').rglob('*.py'),*(ROOT/'deploy').rglob('*.py')]
    for path in sorted(owned_python):
        relative=path.relative_to(ROOT).as_posix();tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        prefixes={'app':''}
        for assignment in tree.body:
            if (isinstance(assignment,ast.Assign) and isinstance(assignment.value,ast.Call)
                    and isinstance(assignment.value.func,ast.Name) and assignment.value.func.id=='APIRouter'):
                prefix=next((ast.literal_eval(item.value) for item in assignment.value.keywords if item.arg=='prefix'),'')
                if not isinstance(prefix,str):raise ValueError('Router prefix is not a literal string')
                for target in assignment.targets:
                    if isinstance(target,ast.Name):prefixes[target.id]=prefix
        class Definitions(ast.NodeVisitor):
            def __init__(self):self.names=[]
            def visit_ClassDef(self,node):
                self.names.append(node.name);self.generic_visit(node);self.names.pop()
            def record(self,node):
                name='.'.join([*self.names,node.name])
                functions.append(dict(path=relative,name=name,line=node.lineno,end_line=node.end_lineno,
                    asynchronous=isinstance(node,ast.AsyncFunctionDef),
                    definition_sha256=digest(ast.dump(node,include_attributes=False).encode()),
                    evidence_status='NOT_ASSIGNED_BY_STATIC_INVENTORY'))
                for decorator in node.decorator_list:
                    if not isinstance(decorator,ast.Call) or not isinstance(decorator.func,ast.Attribute):continue
                    if not isinstance(decorator.func.value,ast.Name) or decorator.func.value.id not in prefixes:continue
                    if decorator.func.attr not in {'get','post','put','patch','delete','head','options','api_route'}:continue
                    if not decorator.args or not isinstance(decorator.args[0],ast.Constant):continue
                    methods=[decorator.func.attr.upper()]
                    if decorator.func.attr=='api_route':
                        methods=next((ast.literal_eval(item.value) for item in decorator.keywords if item.arg=='methods'),[])
                    routes.append(dict(path=relative,function=name,url=prefixes[decorator.func.value.id]+decorator.args[0].value,methods=methods,line=node.lineno))
                self.names.append(node.name);self.generic_visit(node);self.names.pop()
            visit_FunctionDef=record
            visit_AsyncFunctionDef=record
        Definitions().visit(tree)
    for path in sorted([*(ROOT/'assets').glob('*.js'),*(ROOT/'assets').glob('*.mjs')]):
        text=path.read_text(encoding='utf-8');relative=path.relative_to(ROOT).as_posix()
        for match in re.finditer(r'\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(',text):
            javascript.append(dict(path=relative,name=match.group(1),line=text.count('\n',0,match.start())+1))
        for match in re.finditer(r"\$\('([^']+)'\)\.(on[a-z]+)\s*=",text):
            handlers.append(dict(path=relative,element_id=match.group(1),event=match.group(2),line=text.count('\n',0,match.start())+1))
    contract=json.loads((ROOT/'database/access-contract.json').read_text(encoding='utf-8'))
    sql_functions=[]
    for definition in contract['definitions']['functions']:
        header=definition.splitlines()[0]
        sql_functions.append(dict(header=header,definition_sha256=digest(definition.encode())))
    after=source_snapshot(ROOT)
    if before!=after:raise RuntimeError('Source changed during static inventory')
    result=dict(schema_version='nsai.current-runtime-inventory/1',recorded_at=datetime.now(timezone.utc).isoformat(),
        scope=__doc__,certified=False,release_approved=False,runtime_coverage_claimed=False,
        script_sha256=digest(Path(__file__).read_bytes()),source_sha256=before,
        counts=dict(python_definitions=len(functions),python_application_definitions=sum(row['path'].startswith('src/') for row in functions),
            python_operations_definitions=sum(not row['path'].startswith('src/') for row in functions),application_routes=len(routes),
            named_javascript_declarations=len(javascript),explicit_ui_event_assignments=len(handlers),
            sealed_postgresql_functions=len(sql_functions)),
        python=functions,routes=routes,javascript_declarations=javascript,explicit_ui_handlers=handlers,
        postgresql_functions=sql_functions,
        limitations=['Static inventory does not establish execution, branch coverage or correctness.',
            'JavaScript entries are lexical declarations/explicit ID handlers, not a complete AST or dynamic-control inventory.',
            'Vendored PDF.js internals are outside this owned-code symbol inventory and remain part of package review.',
            'Historical 507-function trace/allocation artifacts remain unchanged; their observed numerator cannot be reused here.',
            'Per-definition requirement, test, evidence and independent acceptance assignments remain open.'])
    (HERE/'current-runtime-inventory.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS_STATIC_INVENTORY',counts=result['counts'],runtime_coverage_claimed=False)))


if __name__=='__main__':main()
