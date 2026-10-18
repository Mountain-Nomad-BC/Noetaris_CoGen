"""Compact, verifiable mappings from normalized text to immutable source offsets."""
from __future__ import annotations

from io import StringIO
import re
import unicodedata


def identity_offset_map(text):
    if not isinstance(text,str):
        raise ValueError('Offset map text must be a string')
    return [] if not text else [dict(normalized=[0,len(text)],raw=[0,len(text)],mode='linear')]


def _hangul_composes(cluster,char):
    last=ord(cluster[-1])
    current=ord(char)
    leading=(0x1100<=last<=0x115f or 0xa960<=last<=0xa97c)
    vowel=(0x1160<=current<=0x11a7 or 0xd7b0<=current<=0xd7c6)
    if leading and vowel:
        return True
    final=(0x11a8<=current<=0x11ff or 0xd7cb<=current<=0xd7fb)
    if not final:
        return False
    composed=unicodedata.normalize('NFC',cluster)
    trailing=(0xac00<=ord(composed[-1])<=0xd7a3 and (ord(composed[-1])-0xac00)%28==0)
    return trailing and final


def line_offset_map(raw_text):
    if not isinstance(raw_text,str):
        raise ValueError('Raw line must be a string')
    source=raw_text.rstrip('\r\n')
    if '\x00' in source:
        raise ValueError('NUL bytes are not allowed')
    output=StringIO()
    segments=[]
    normalized_offset=0
    pending_start=None
    pending_end=None

    def emit(value,start,end,mode):
        nonlocal normalized_offset
        if not value:
            return
        next_offset=normalized_offset+len(value)
        raw_length=end-start
        if mode=='cover' and raw_length%len(value)==0:
            mode='partition'
        previous=segments[-1] if segments else None
        same_partition=(mode=='partition' and previous is not None and previous['mode']=='partition'
            and (previous['raw'][1]-previous['raw'][0])//(previous['normalized'][1]-previous['normalized'][0])==raw_length//len(value))
        if mode=='linear' and previous is not None and previous['mode']=='linear' and previous['normalized'][1]==normalized_offset and previous['raw'][1]==start:
            previous['normalized'][1]=next_offset
            previous['raw'][1]=end
        elif same_partition and previous['normalized'][1]==normalized_offset and previous['raw'][1]==start:
            previous['normalized'][1]=next_offset
            previous['raw'][1]=end
        else:
            segments.append(dict(normalized=[normalized_offset,next_offset],raw=[start,end],mode=mode))
        output.write(value)
        normalized_offset=next_offset

    cluster=''
    cluster_start=0

    def flush_cluster(end):
        nonlocal cluster,pending_start,pending_end
        if not cluster:
            return
        value=unicodedata.normalize('NFC',cluster)
        if value not in {' ','\t'} and ' ' not in value and '\t' not in value:
            if pending_start is not None:
                if normalized_offset:
                    mode='linear' if pending_end-pending_start==1 else 'partition'
                    emit(' ',pending_start,pending_end,mode)
                pending_start=pending_end=None
            mode='linear' if value==cluster else 'partition' if (end-cluster_start)%len(value)==0 else 'cover'
            emit(value,cluster_start,end,mode)
            cluster=''
            return
        for match in re.finditer(r'[\t ]+|[^\t ]+',value):
            part=match.group()
            start,end_offset=match.span()
            if part[0] in {' ','\t'}:
                raw_start,raw_end=(cluster_start+start,cluster_start+end_offset) if value==cluster else (cluster_start,end)
                if pending_start is None:
                    pending_start=raw_start
                pending_end=raw_end
                continue
            if pending_start is not None:
                if normalized_offset:
                    mode='linear' if pending_end-pending_start==1 else 'partition'
                    emit(' ',pending_start,pending_end,mode)
                pending_start=pending_end=None
            if value==cluster:
                raw_start,raw_end=cluster_start+start,cluster_start+end_offset
                mode='linear'
            else:
                raw_start,raw_end=cluster_start,end
                mode='partition' if (raw_end-raw_start)%len(part)==0 else 'cover'
            emit(part,raw_start,raw_end,mode)
        cluster=''

    for index,char in enumerate(source):
        continues=bool(cluster) and (
            unicodedata.combining(char)!=0 or _hangul_composes(cluster,char)
        )
        if cluster and not continues:
            flush_cluster(index)
        if not cluster:
            cluster_start=index
        cluster+=char
    flush_cluster(len(source))
    normalized=output.getvalue()
    expected=unicodedata.normalize('NFC',source)
    expected='\n'.join(re.sub(r'[\t ]+',' ',part).strip() for part in expected.split('\n'))
    if normalized!=expected:
        raise ValueError('Normalization offset map construction failed')
    return normalized,segments


def validate_line_offset_map(raw_text,normalized_text,offset_map):
    expected_text,expected_map=line_offset_map(raw_text)
    if normalized_text!=expected_text or offset_map!=expected_map:
        raise ValueError('Normalization offset map does not bind source text')
    return True


def raw_ranges_for_normalized_range(offset_map,start,end):
    if (type(start) is not int or type(end) is not int or start<0 or end<=start
            or not isinstance(offset_map,list)):
        raise ValueError('Invalid normalized text range')
    mapped=[]
    cursor=start
    for segment in offset_map:
        if not isinstance(segment,dict):
            raise ValueError('Invalid normalization offset segment')
        normalized,raw,mode=segment.get('normalized'),segment.get('raw'),segment.get('mode')
        if (not isinstance(normalized,list) or len(normalized)!=2
                or not all(type(value) is int for value in normalized)
                or not isinstance(raw,list) or len(raw)!=2
                or not all(type(value) is int for value in raw)
                or normalized[0]<0 or normalized[1]<=normalized[0]
                or raw[0]<0 or raw[1]<=raw[0] or mode not in {'linear','partition','cover'}):
            raise ValueError('Invalid normalization offset segment')
        left=max(start,normalized[0])
        right=min(end,normalized[1])
        if left>=right:
            continue
        if left>cursor:
            raise ValueError('Normalized range is not covered by source offsets')
        if mode=='linear':
            source=(raw[0]+left-normalized[0],raw[0]+right-normalized[0])
        elif mode=='partition':
            ratio=(raw[1]-raw[0])//(normalized[1]-normalized[0])
            if ratio<1 or (raw[1]-raw[0])% (normalized[1]-normalized[0]):
                raise ValueError('Invalid partition offset ratio')
            source=(raw[0]+(left-normalized[0])*ratio,raw[0]+(right-normalized[0])*ratio)
        else:
            source=(raw[0],raw[1])
        if mapped and mapped[-1][1]==source[0]:
            mapped[-1]=(mapped[-1][0],source[1])
        else:
            mapped.append(source)
        cursor=right
        if cursor==end:
            break
    if cursor!=end or not mapped:
        raise ValueError('Normalized range is not covered by source offsets')
    return mapped
