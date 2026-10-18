"""Bounded complete source sets for server-produced prompts and stored outputs.

Identifiers in client metadata never grant authority: every collected dependency
is checked against current database policy before it is persisted or returned.
"""
SINGLE_KEYS=frozenset({'document_id'})
MULTI_KEYS=frozenset({'document_ids','source_ids','source_dependencies'})
RESEARCH_VISIT_BUDGET=1000000


def collect_sources(*values, required=(),conn=None,traversal_budget=100000):
    # The larger contract is used only for already size-checked research
    # artifacts (16 MiB). Ordinary prompts/receipts retain their existing bound.
    if type(traversal_budget) is not int or traversal_budget not in (100000,RESEARCH_VISIT_BUDGET):
        raise ValueError('Invalid source dependency traversal budget')
    sources=set()
    manifests={}
    def add(source):
        if not isinstance(source,str) or not 1<=len(source)<=128:
            raise ValueError('Invalid source dependency')
        sources.add(source)
        if len(sources)>1000:raise ValueError('Source dependency budget exceeded')
    for source in required:add(source)
    remaining=traversal_budget
    def visit(value,depth=0):
        nonlocal remaining
        remaining-=1
        if remaining<0 or depth>32:raise ValueError('Source dependency traversal budget exceeded')
        if isinstance(value,dict):
            for key,item in value.items():
                if key=='source_manifest_id':
                    if not isinstance(item,str):raise ValueError('Invalid source manifest reference')
                    if item not in manifests:
                        if len(manifests)>=16:raise ValueError('Source manifest traversal budget exceeded')
                        from .provenance_manifests import get_sources
                        manifests[item]=get_sources(item,conn=conn)
                    for source in manifests[item]:add(source)
                elif key in SINGLE_KEYS and item is not None:add(item)
                elif key in MULTI_KEYS:
                    if not isinstance(item,(tuple,list,set,frozenset)):
                        raise ValueError('Invalid source dependency set')
                    for source in item:add(source)
                else:visit(item,depth+1)
        elif isinstance(value,(tuple,list)):
            for item in value:visit(item,depth+1)
    for value in values:visit(value)
    return sorted(sources)


def validate_sources(conn,sources,*,complete=True):
    if not conn.execute('SELECT nsai_sources_visible(%s,%s)',(sources,complete)).fetchone()[0]:
        raise LookupError('Source unavailable')


def stamp_result(result,hits,memory):
    """Include every prompt input, even when the model omits its citation."""
    from .store import request_source_dependencies
    result['source_dependencies']=collect_sources(result,hits,memory,required=request_source_dependencies())
    result['provenance_complete']=True
    return result


def stored_provenance(value,*,conn=None):
    """Never infer that an old cached output has complete provenance."""
    complete=value.get('provenance_complete') is True
    return collect_sources(value,conn=conn) if complete else [],complete
