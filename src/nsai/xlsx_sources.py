"""Bounded worksheet evidence using raw OOXML literals; no workbook execution."""
import hashlib
from io import BytesIO
import json
import posixpath
import re
import stat
from urllib.parse import quote
from zipfile import ZipFile,BadZipFile,ZIP_STORED,ZIP_DEFLATED
from defusedxml.ElementTree import fromstring
from xml.etree.ElementTree import tostring,canonicalize
from .upload_limits import ACTIVE
from .text_chunks import iter_text_chunks
from .normalization import identity_offset_map

MEDIA='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
DOCREL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
TAG=lambda name:'{'+NS+'}'+name


def _markup(item):return canonicalize(tostring(item,encoding='unicode'),rewrite_prefixes=True)


def _attributes(item):return [dict(name=name,value=value) for name,value in sorted(item.attrib.items())]


def _xml(raw):
    try:root=fromstring(raw,forbid_dtd=True,forbid_entities=True,forbid_external=True)
    except Exception as error:raise ValueError('Unsafe or malformed workbook XML') from error
    pending=[(root,0)];count=0
    while pending:
        item,depth=pending.pop();count+=1
        if count>50000 or depth>32:raise ValueError('Workbook XML structural budget exceeded')
        pending.extend((child,depth+1) for child in item)
    return root


def _text(item):
    if item is None:return None
    # Retain complete rich text/phonetic/formatting markup separately; do not
    # accidentally append phonetic annotations to the actual displayed string.
    texts=[]
    for child in item:
        if child.tag==TAG('t'):texts.append(child.text or '')
        elif child.tag==TAG('r'):texts.extend(text.text or '' for text in child if text.tag==TAG('t'))
    return ''.join(texts)


def parse_xlsx(data):
    if not isinstance(data,bytes) or not data or len(data)>ACTIVE.max_bytes or not data.startswith(b'PK\x03\x04'):
        raise ValueError('Workbook signature or original-byte budget rejected')
    try:
        with ZipFile(BytesIO(data)) as archive:return _parse_archive(data,archive)
    except (BadZipFile,RuntimeError,KeyError,UnicodeError) as error:raise ValueError('Invalid or unsupported workbook archive') from error


def _parse_archive(data,archive):
    infos=archive.infolist()
    if not 1<=len(infos)<=128:raise ValueError('Workbook member count exceeded')
    parts={};total=0;folded=set()
    fixed={'[Content_Types].xml','_rels/.rels','xl/workbook.xml','xl/_rels/workbook.xml.rels',
           'xl/sharedStrings.xml','xl/styles.xml','xl/theme/theme1.xml','docProps/core.xml','docProps/app.xml'}
    for info in infos:
        name=info.filename
        if (name.casefold() in folded or '\\' in name or name.startswith('/') or ':' in name
                or any(part in {'','..','.'} for part in name.rstrip('/').split('/'))):
            raise ValueError('Workbook duplicate or unsafe member path')
        folded.add(name.casefold())
        if info.flag_bits&1 or stat.S_ISLNK(info.external_attr>>16) or info.compress_type not in {ZIP_STORED,ZIP_DEFLATED}:
            raise ValueError('Workbook encrypted, linked or unsupported compressed member')
        if info.is_dir():continue
        if name not in fixed and re.fullmatch(r'xl/worksheets/sheet[1-9][0-9]*\.xml',name) is None:
            raise ValueError('Workbook contains unsupported parts; macros, external links, drawings, comments and embedded objects are not admitted')
        total+=info.file_size
        if info.file_size>2*1024*1024 or total>8*1024*1024 or info.file_size>max(1,info.compress_size)*200:
            raise ValueError('Workbook expanded-byte or compression budget exceeded')
        with archive.open(info) as member:raw=member.read(2*1024*1024+1)
        if len(raw)!=info.file_size:raise ValueError('Workbook member size mismatch')
        parts[name]=dict(raw=raw,xml=_xml(raw),sha256=hashlib.sha256(raw).hexdigest())
    required={'[Content_Types].xml','_rels/.rels','xl/workbook.xml','xl/_rels/workbook.xml.rels'}
    if not required<=parts.keys():raise ValueError('Workbook package is incomplete')
    types=parts['[Content_Types].xml']['xml']
    if types.tag!='{http://schemas.openxmlformats.org/package/2006/content-types}Types':raise ValueError('Invalid package content types')
    type_labels=' '.join(value for item in types for value in item.attrib.values()).casefold()
    if any(value in type_labels for value in ('macroenabled','vbaproject','activex','externallink')):
        raise ValueError('Active workbook content rejected')
    root_relations=_relations(parts['_rels/.rels']['xml'],'')
    if sum(kind==DOCREL+'/officeDocument' and target=='xl/workbook.xml' for kind,target in root_relations.values())!=1 or any(target not in parts for kind,target in root_relations.values()):
        raise ValueError('Workbook root relationship is missing')
    relations=_relations(parts['xl/_rels/workbook.xml.rels']['xml'],'xl')
    for kind,target in relations.values():
        if target not in parts:raise ValueError('Workbook relationship has no retained part')
        if kind not in {DOCREL+'/'+name for name in ('worksheet','sharedStrings','styles','theme')}:
            raise ValueError('Unsupported workbook relationship')
    shared=[]
    if 'xl/sharedStrings.xml' in parts:
        root=parts['xl/sharedStrings.xml']['xml']
        if root.tag!=TAG('sst'):raise ValueError('Invalid shared string table')
        for item in root:
            if item.tag!=TAG('si') or len(shared)>=5000:raise ValueError('Invalid or excessive shared strings')
            shared.append(dict(text=_text(item),xml=_markup(item)))
    workbook=parts['xl/workbook.xml']['xml']
    if workbook.tag!=TAG('workbook'):raise ValueError('Invalid workbook namespace')
    sheets=workbook.find(TAG('sheets'))
    if sheets is None or not 1<=len(sheets)<=10:raise ValueError('Workbook sheet budget rejected')
    records=[];sheet_records=[];seen_names=set();seen_ids=set();used=set();cell_count=0
    allowed_sections={TAG(name) for name in ('sheetPr','dimension','sheetViews','sheetFormatPr','cols','sheetData','mergeCells','pageMargins','pageSetup','printOptions','sheetProtection','autoFilter')}
    for sheet in sheets:
        name=sheet.get('name');sheet_id=sheet.get('sheetId');relid=sheet.get('{'+DOCREL+'}id');state=sheet.get('state','visible')
        if sheet.tag!=TAG('sheet') or not name or len(name)>100 or name.casefold() in seen_names or not sheet_id or re.fullmatch('[1-9][0-9]{0,9}',sheet_id) is None or int(sheet_id)>4294967295 or sheet_id in seen_ids or state not in {'visible','hidden','veryHidden'}:
            raise ValueError('Invalid or duplicate workbook sheet')
        seen_names.add(name.casefold());seen_ids.add(sheet_id)
        relation=relations.get(relid)
        if relation is None or relation[0]!=DOCREL+'/worksheet' or relation[1] in used:raise ValueError('Invalid worksheet relationship')
        target=relation[1];used.add(target);root=parts[target]['xml']
        if root.tag!=TAG('worksheet') or any(child.tag not in allowed_sections for child in root):
            raise ValueError('Unsupported worksheet sections; no content is silently omitted')
        table=root.find(TAG('sheetData'))
        if table is None or len(table)>2000:raise ValueError('Worksheet row budget rejected')
        sheet_record=dict(name=name,sheet_id=sheet_id,state=state,part=target,rows=[],
            sections=[_markup(child) for child in root if child.tag!=TAG('sheetData')])
        seen_rows=set();seen_cells=set()
        for row in table:
            row_id=row.get('r')
            if row.tag!=TAG('row') or not row_id or re.fullmatch('[1-9][0-9]{0,6}',row_id) is None or int(row_id)>1048576 or row_id in seen_rows:
                raise ValueError('Invalid or duplicate worksheet row')
            seen_rows.add(row_id);row_record=dict(row=int(row_id),attributes=_attributes(row),cells=[])
            for cell in row:
                reference=cell.get('r');match=re.fullmatch(r'([A-Z]{1,3})([1-9][0-9]{0,6})',reference or '')
                if cell.tag!=TAG('c') or match is None or match[2]!=row_id or reference in seen_cells:raise ValueError('Invalid or duplicate workbook cell')
                column=0
                for letter in match[1]:column=column*26+ord(letter)-64
                if column>16384:raise ValueError('Cell column outside worksheet range')
                seen_cells.add(reference);cell_count+=1
                if cell_count>5000:raise ValueError('Workbook cell budget exceeded')
                kind=cell.get('t','n')
                if kind not in {'n','s','str','inlineStr','b','e','d'}:raise ValueError('Unsupported cell type')
                if any(child.tag not in {TAG('v'),TAG('f'),TAG('is')} for child in cell) or any(len(cell.findall(TAG(tag)))>1 for tag in ('v','f','is')):
                    raise ValueError('Unsupported or duplicated cell content')
                value=cell.find(TAG('v'));formula=cell.find(TAG('f'));inline=cell.find(TAG('is'))
                if (value is not None and len(value)) or (formula is not None and len(formula)):
                    raise ValueError('Invalid nested cell value or formula')
                literal=value.text if value is not None else None
                if kind=='n' and literal is not None and (len(literal)>128 or re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?',literal) is None):
                    raise ValueError('Invalid declared numeric cell literal')
                if kind=='b' and literal not in {'0','1',None}:raise ValueError('Invalid declared boolean cell literal')
                shared_value=None;text=literal
                if kind=='s':
                    if literal is None or not literal.isascii() or not literal.isdigit() or int(literal)>=len(shared):raise ValueError('Shared string reference is invalid')
                    shared_value=shared[int(literal)];text=shared_value['text']
                elif kind=='inlineStr':text=_text(inline)
                locator='sheet:'+quote(name,safe='')+':cell:'+reference
                if len(locator)>200:raise ValueError('Workbook cell locator exceeds budget')
                record=dict(locator=locator,sheet_id=sheet_id,coordinate=reference,column=column,row=int(row_id),
                    cell_type=kind,attributes=_attributes(cell),raw_value=literal,text=text,
                    formula=None if formula is None else dict(text=formula.text,attributes=_attributes(formula)),
                    inline_xml=None if inline is None else _markup(inline),shared_string=shared_value)
                row_record['cells'].append(record);records.append(record)
            sheet_record['rows'].append(row_record)
        sheet_records.append(sheet_record)
    if {name for name in parts if name.startswith('xl/worksheets/')}!=used:raise ValueError('Unreferenced worksheet part is not admitted')
    # Empty sheets and blank explicit rows remain evidence too.
    evidence=[dict(locator='sheet:'+quote(sheet['name'],safe='')+':structure',value={key:value for key,value in sheet.items() if key!='rows'}) for sheet in sheet_records]
    evidence.extend(dict(locator='sheet:'+quote(sheet['name'],safe='')+':row:'+str(row['row']),value=dict(attributes=row['attributes'],cell_count=len(row['cells']))) for sheet in sheet_records for row in sheet['rows'])
    evidence.extend(dict(locator=record['locator'],value=record) for record in records)
    spans=[];chunks=[];mapping=[];chars=0
    for item in evidence:
        text=json.dumps(item['value'],ensure_ascii=True,separators=(',',':'));chars+=len(text)+(1 if spans else 0)
        if chars>ACTIVE.max_chars or len(spans)>=5000:raise ValueError('Workbook evidence text budget exceeded')
        locator=item['locator'];spans.append(dict(locator=locator,text=text,page=None,global_line=len(spans)+1))
        mapping.append(dict(locator=locator,raw_text=text,normalized_text=text,offset_unit='unicode_codepoint',normalization='raw-ooxml-record-json/1',offset_map=identity_offset_map(text)))
        for offset,part in iter_text_chunks(text):
            chunks.append(dict(locator=locator,text=part,offset=offset,end_offset=offset+len(part),sha256=hashlib.sha256(part.encode()).hexdigest()))
            if len(chunks)>5000:raise ValueError('Workbook chunk budget exceeded')
    digest=hashlib.sha256(data).hexdigest()
    return dict(original_sha256=digest,media_type=MEDIA,raw_text='\n'.join(span['text'] for span in spans),spans=spans,chunks=chunks,
        page_count=1,pages=[dict(page=None,status='native',complete=True,native_text_present=True)],normalization_map=mapping,
        parser_version='nsai-xlsx/1',complete=True,warnings=['Worksheet cell evidence only; formulas and cached values are distinct and never executed or verified.','Layout/styles/properties are retained in the original package; no date, unit, header or numeric conversion is inferred.'],
        structured_data=dict(schema='nsai.xlsx-evidence/1',original_sha256=digest,sheets=sheet_records,cell_count=cell_count,
            parts=[dict(path=name,sha256=part['sha256'],size_bytes=len(part['raw'])) for name,part in parts.items()]))


def _relations(root,base):
    if root.tag!='{'+REL+'}Relationships':raise ValueError('Invalid package relationships')
    result={}
    for relation in root:
        identity=relation.get('Id');target=relation.get('Target','');kind=relation.get('Type','')
        if not identity or identity in result or relation.tag!='{'+REL+'}Relationship' or relation.get('TargetMode','Internal')!='Internal':
            raise ValueError('Duplicate or external workbook relationship')
        if not target or any(c in target for c in ('\\',':','?','#','%')) or '..' in target.split('/'):
            raise ValueError('Unsafe workbook relationship target')
        target=target.lstrip('/') if target.startswith('/') else posixpath.join(base,target)
        if posixpath.normpath(target)!=target:raise ValueError('Noncanonical workbook relationship target')
        result[identity]=(kind,target)
    return result


def validate_xlsx(data,parsed):
    expected=parse_xlsx(data)
    encode=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    if encode(parsed)!=encode(expected):raise ValueError('Workbook evidence does not match original source')
    return parsed
