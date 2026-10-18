"""Original, model-free OCR measurement contracts; no OCR activation."""
from __future__ import annotations
from dataclasses import dataclass
import math
import unicodedata

def percentile(values,percent):
    """Nearest-rank percentile: small cohorts expose max instead of interpolation."""
    if not values:
        return None
    if not 0<=percent<=100 or any(not math.isfinite(v) or v<0 for v in values):
        raise ValueError('Invalid percentile input')
    ordered=sorted(values)
    return ordered[max(0,math.ceil(percent/100*len(ordered))-1)]

def aggregate_error_rates(records):
    """Micro rates weight reference lengths, never average incompatible ratios."""
    chars=sum(record['reference_characters'] for record in records)
    words=sum(record['reference_words'] for record in records)
    return dict(pages=len(records),cer=sum(r['char_edits'] for r in records)/chars if chars else None,
        wer=sum(r['word_edits'] for r in records)/words if words else None,
        reference_characters=chars,reference_words=words,
        empty_reference_false_positive_pages=sum(r['empty_reference_false_positive'] for r in records))

def edit_distance(reference, observed):
    if max(len(reference),len(observed))>4096:
        raise ValueError('Metric input exceeds bounded comparison size')
    if len(reference)<len(observed):
        reference,observed=observed,reference
    previous=list(range(len(observed)+1))
    for i,left in enumerate(reference,1):
        current=[i]
        for j,right in enumerate(observed,1):
            current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(left!=right)))
        previous=current
    return previous[-1]

def error_rates(reference: str, observed: str, *, normalized=False):
    """CER/WER may exceed one. Empty reference has no defined denominator."""
    if normalized:
        reference=' '.join(unicodedata.normalize('NFC',reference).split())
        observed=' '.join(unicodedata.normalize('NFC',observed).split())
    words,actual=reference.split(),observed.split()
    char_edits=edit_distance(reference,observed)
    word_edits=edit_distance(words,actual)
    return dict(cer=char_edits/len(reference) if reference else None,
        wer=word_edits/len(words) if words else None,char_edits=char_edits,
        word_edits=word_edits,reference_characters=len(reference),reference_words=len(words),
        empty_reference_false_positive=bool(not reference and observed),normalization='NFC/whitespace' if normalized else 'raw')

@dataclass(frozen=True)
class AffineTransform:
    """PDF user coordinates to raster pixels. Crop/rotation/deskew are explicit."""
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float
    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.a,self.b,self.c,self.d,self.e,self.f)) or abs(self.a*self.d-self.b*self.c)<1e-12:
            raise ValueError('Transform must be finite and invertible')
    def point(self,x,y):
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError('Coordinates must be finite')
        return self.a*x+self.c*y+self.e,self.b*x+self.d*y+self.f
    def inverse(self):
        det=self.a*self.d-self.b*self.c
        return AffineTransform(self.d/det,-self.b/det,-self.c/det,self.a/det,
            (self.c*self.f-self.d*self.e)/det,(self.b*self.e-self.a*self.f)/det)
    def rectangle(self,box):
        x0,y0,x1,y1=box
        points=[self.point(x,y) for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1))]
        return min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)

def box_iou(left,right):
    if any(not math.isfinite(v) for v in (*left,*right)) or left[2]<left[0] or left[3]<left[1] or right[2]<right[0] or right[3]<right[1]:
        raise ValueError('Invalid rectangle')
    overlap=max(0,min(left[2],right[2])-max(left[0],right[0]))*max(0,min(left[3],right[3])-max(left[1],right[1]))
    union=(left[2]-left[0])*(left[3]-left[1])+(right[2]-right[0])*(right[3]-right[1])-overlap
    return overlap/union if union else None
