"""Read-only JSON/JSONL structure inventory; no ingestion or truth promotion."""
import hashlib
import os
from pathlib import Path
import stat
from .assembly import strict_json

MAX_BYTES=32*1024*1024


class Issues(list):
    def __init__(self):super().__init__();self.omitted=0
    def append(self,value):
        if len(self)<1000:super().append(value)
        else:self.omitted+=1
    def extend(self,values):
        for value in values:self.append(value)
        self.omitted+=getattr(values,'omitted',0)


def audit_bytes(path):
    """Audits may inspect excluded names, but never follow filesystem links."""
    path=Path(path).absolute()
    for part in (path,*path.parents):
        info=part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024):
            raise ValueError('audit_link_refused')
    before=path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size>MAX_BYTES:raise ValueError('audit_size_refused')
    with path.open('rb') as source:raw=source.read(MAX_BYTES+1)
    after=path.stat()
    same=lambda item:(item.st_dev,item.st_ino,item.st_size,item.st_mtime_ns)
    if len(raw)!=before.st_size or len(raw)>MAX_BYTES or same(before)!=same(after):raise ValueError('audit_source_changed')
    return raw


def inspect_json(value):
    """Only explicit generic graph contracts; unclassified schemas stay unknown."""
    issues=Issues()
    if isinstance(value,dict) and isinstance(value.get('nodes'),list) and isinstance(value.get('edges'),list):
        ids=[]
        for index,node in enumerate(value['nodes']):
            if not isinstance(node,dict) or not isinstance(node.get('id'),str):
                issues.append(dict(code='graph_node_without_id',record=index));continue
            ids.append(node['id'])
        seen=set()
        for identity in ids:
            if identity in seen:issues.append(dict(code='duplicate_graph_node',identity=identity))
            seen.add(identity)
        edge_ids=set()
        for index,edge in enumerate(value['edges']):
            if not isinstance(edge,dict):issues.append(dict(code='invalid_graph_edge',record=index));continue
            identity=edge.get('id')
            if isinstance(identity,str):
                if identity in edge_ids:issues.append(dict(code='duplicate_graph_edge',identity=identity))
                edge_ids.add(identity)
            for endpoint in ('source_id','target_id'):
                target=edge.get(endpoint)
                if not isinstance(target,str) or target not in seen:
                    issues.append(dict(code='unresolved_graph_endpoint',record=index,endpoint=endpoint,identity=target))
        return issues,dict(graph_nodes=len(ids),graph_edges=len(value['edges']),schema_status='generic-graph-shape-only')
    return issues,dict(schema_status='unclassified; canonical/family validity not established')


def inspect_file(path):
    raw=audit_bytes(path);report=dict(size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),issues=Issues())
    if Path(path).suffix.casefold()=='.jsonl':
        families=set();ids=set();records=0;heads=set()
        lines=raw.split(b'\n')
        if lines and lines[-1]==b'':lines.pop()
        if not lines:report['issues'].append(dict(code='empty_jsonl'))
        for line_number,line in enumerate(lines,1):
            if line_number>100000:raise ValueError('jsonl_record_budget')
            if len(line)>1024*1024:
                report['issues'].append(dict(code='jsonl_line_budget',line=line_number));continue
            try:value=strict_json(line,max_bytes=1024*1024,max_depth=32,max_items=100000)
            except ValueError:
                report['issues'].append(dict(code='invalid_jsonl_record',line=line_number));continue
            records+=1
            if not isinstance(value,dict):report['issues'].append(dict(code='jsonl_record_not_object',line=line_number));continue
            family=value.get('record_family',value.get('schema'))
            if not isinstance(family,str):family=None
            else:families.add(family)
            identity=value.get('canonical_id',value.get('id'))
            if type(identity) in {str,int}:
                key=(family,type(identity).__name__,identity)
                if key in ids:report['issues'].append(dict(code='duplicate_record_id',line=line_number,identity=identity,family=family))
                ids.add(key)
                if value.get('active_head') is True:
                    scope=value.get('scope_id')
                    if not isinstance(scope,str):report['issues'].append(dict(code='active_head_without_scope',line=line_number))
                    else:
                        head=(family,scope,identity)
                        if head in heads:report['issues'].append(dict(code='duplicate_active_head',line=line_number,identity=identity,scope=scope))
                        heads.add(head)
        if len(families)>1:report['issues'].append(dict(code='mixed_record_families',families=sorted(families)))
        report.update(records=records,physical_lines=len(lines),families=sorted(families),
            schema_status='annotations-only; family schemas not yet qualified')
        if not families:report['schema_status']='unclassified; family schemas not yet qualified'
    else:
        value=strict_json(raw,max_bytes=MAX_BYTES,max_depth=32,max_items=1000000)
        issues,summary=inspect_json(value);report['issues'].extend(issues);report.update(summary)
    # Detect modifications during interpretation as well as during the read.
    if hashlib.sha256(audit_bytes(path)).hexdigest()!=report['sha256']:raise ValueError('audit_source_changed')
    report['original_unchanged']=True
    report['omitted_issues']=report['issues'].omitted
    report['audit_complete']=not report['omitted_issues']
    return report
