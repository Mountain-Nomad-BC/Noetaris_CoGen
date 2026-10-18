"""Typed deterministic calculations over authorized immutable table evidence."""
from decimal import Decimal,localcontext,ROUND_HALF_EVEN
import hashlib
import json
import re
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field


class TableAnalysisInput(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    value_column:int=Field(ge=1,le=100)
    operation:Literal['count','sum','mean','min','max']='sum'
    group_column:int|None=Field(default=None,ge=1,le=100)
    skip_rows:int=Field(default=0,ge=0,le=10)
    unit:str=Field(default='',max_length=60,pattern=r'^[^\x00-\x1f\x7f]*$')
    sheet:str|None=Field(default=None,min_length=1,max_length=100)


def calculate(table,request):
    if table.get('schema')!='nsai.delimited-evidence/1':raise ValueError('Supported table evidence required')
    groups={};excluded=[];included=[];selected=table['rows'][request.skip_rows:]
    if not selected:raise ValueError('No records remain after the explicit header skip')
    with localcontext() as context:
        context.prec=80
        for row in selected:
            cells=row['cells'];index=request.value_column-1
            cell=cells[index] if index<len(cells) else None
            if cell is not None and request.operation!='count' and cell.get('formula_present'):
                raise ValueError('Formula results are not verified numeric evidence at '+cell['locator'])
            if cell is None or cell['value'] in ('',None):
                excluded.append(dict(locator=row['locator'],reason='missing-column' if cell is None else 'blank-cell' if cell['value'] is None else 'empty-cell'))
                continue
            if request.group_column is None:group='All included records'
            else:
                position=request.group_column-1
                if position>=len(cells) or cells[position] is None:raise ValueError('Grouping column is absent at '+row['locator'])
                group=cells[position].get('group_label',cells[position]['value'])
            if len(group)>200:raise ValueError('Grouping label exceeds chart budget')
            if group not in groups and len(groups)>=100:raise ValueError('Analysis exceeds 100 groups; select a narrower dataset')
            value=cell['value']
            if request.operation=='count':number=Decimal(1)
            else:
                if cell.get('value_type') in {'b','d','e'}:raise ValueError('Boolean, date or error cell requires separate typed interpretation at '+cell['locator'])
                # Explicit column selection authorizes decimal interpretation;
                # whitespace, currencies, separators, dates and formula text
                # are not guessed or silently dropped as nonnumeric values.
                if re.fullmatch(r'[+-]?[0-9]{1,30}(?:\.[0-9]{1,18})?',value) is None:
                    raise ValueError('Expected an explicit decimal value at '+cell['locator'])
                number=Decimal(value)
            groups.setdefault(group,[]).append(number)
            included.append(cell['locator'])
        output=[]
        for label,values in groups.items():
            count=len(values);total=sum(values,Decimal(0))
            if request.operation=='count':value=Decimal(count)
            elif request.operation=='sum':value=total
            elif request.operation=='min':value=min(values)
            elif request.operation=='max':value=max(values)
            else:
                with localcontext() as mean_context:
                    mean_context.prec=34;mean_context.rounding=ROUND_HALF_EVEN
                    value=total/Decimal(count)
            output.append(dict(label=label,value=format(value,'f'),included_records=count))
    return dict(schema='nsai.table-analysis/1',method='deterministic-decimal',request=request.model_dump(),
        groups=output,coverage=dict(total_records=len(table['rows']),skipped_records=request.skip_rows,
            selected_records=len(selected),included_records=len(included),excluded_records=len(excluded),
            exclusions=excluded),included_cell_locators=included,
        unit=dict(label='records' if request.operation=='count' else request.unit,
                  authority='record count' if request.operation=='count' else 'user-declared; not inferred or verified'),
        numeric_policy='Explicit decimal column; no currency/date/locale/formula inference. Empty cells and absent columns excluded and counted.',
        arithmetic=dict(aggregate_precision=80,mean_significant_digits=34,mean_rounding='ROUND_HALF_EVEN'),
        interpretation='Computation over cited cells; no causal or factual promotion.',authority_granted=False)


def analyze_source(document_id,request):
    from . import workflow_store as workflows
    from .ingestion import parse_source
    from .structured_sources import MEDIA
    source=workflows.source(document_id)
    extensions={media:suffix for suffix,media in MEDIA.items()}
    from .xlsx_sources import MEDIA as XLSX_MEDIA
    extensions[XLSX_MEDIA]='.xlsx'
    if source['media_type'] not in extensions:raise ValueError('This source has no supported delimited table')
    original,media=workflows.original_source(document_id)
    parsed=parse_source(original,'source'+extensions[media])
    stored=source['manifest']['documents'][0]['metadata'].get('structured_data')
    encode=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    if encode(stored)!=encode(parsed['structured_data']):raise ValueError('Stored table differs from original evidence')
    evidence=parsed['structured_data']
    if media==XLSX_MEDIA:
        sheets=evidence['sheets']
        selected=next((sheet for sheet in sheets if sheet['name']==request.sheet),None)
        if request.sheet is None and len(sheets)==1:selected=sheets[0]
        if selected is None:raise ValueError('Select one exact worksheet name explicitly, including hidden sheets if intended')
        rows=[]
        from urllib.parse import quote
        for row in selected['rows']:
            cells=[None]*min(100,max((cell['column'] for cell in row['cells']),default=0))
            for cell in row['cells']:
                if cell['column']>100:continue
                value=cell['text'];formula=cell['formula']
                if formula is not None:value=formula['text'] or '[formula declaration]'
                label=('blank' if value is None else value)+(' [formula]' if formula is not None else ' ['+cell['cell_type']+']')
                cells[cell['column']-1]=dict(locator=cell['locator'],value=value,value_type=cell['cell_type'],
                    formula_present=formula is not None,group_label=label)
            rows.append(dict(locator='sheet:'+quote(selected['name'],safe='')+':row:'+str(row['row']),cells=cells))
        result=calculate(dict(schema='nsai.delimited-evidence/1',rows=rows),request)
        result['worksheet']=dict(name=selected['name'],sheet_id=selected['sheet_id'],state=selected['state'],selection='explicit' if request.sheet is not None else 'only worksheet')
        result['numeric_policy']+=' Workbook formulas/caches, booleans, typed dates and errors are never automatically numeric inputs. Group labels preserve source type.'
    else:
        if request.sheet is not None:raise ValueError('Worksheet selection requires an XLSX source')
        result=calculate(evidence,request)
    result.update(document_id=document_id,revision=source['revision'],original_sha256=source['original_sha256'],
        source_dependencies=[document_id],provenance_complete=True)
    result['analysis_sha256']=hashlib.sha256(encode(result).encode('utf-8')).hexdigest()
    return result
