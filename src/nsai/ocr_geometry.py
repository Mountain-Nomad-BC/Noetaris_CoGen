"""Bounded 300-DPI crop/right-angle raster custody in original PDF coordinates."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PageGeometry:
    pixels: tuple[int,int]
    pixel_to_pdf: tuple[float,float,float,float,float,float]
    crop: tuple[float,float,float,float]


def page_geometry(page):
    crop=tuple(float(v) for v in page.cropbox)
    media=tuple(float(v) for v in page.mediabox)
    rotation=float(page.get('/Rotate',0))
    if not all(math.isfinite(v) for v in (*crop,*media,rotation)) or float(page.get('/UserUnit',1))!=1:
        raise ValueError('Unsupported OCR page geometry')
    left,bottom,right,top=crop
    if not (media[0]<=left<right<=media[2] and media[1]<=bottom<top<=media[3]) or rotation%90:
        raise ValueError('Unsupported OCR crop or rotation')
    width,height=right-left,top-bottom
    if width>20000 or height>20000:raise ValueError('OCR raster pixel budget exceeded')
    rotation=int(rotation)%360
    raster_width,raster_height=(height,width) if rotation in {90,270} else (width,height)
    pixels=(math.ceil(raster_width*300/72),math.ceil(raster_height*300/72))
    if pixels[0]*pixels[1]>12_000_000:raise ValueError('OCR raster pixel budget exceeded before rendering')
    scale=72/300
    matrix={0:(scale,0,0,-scale,left,top),
        90:(0,scale,scale,0,left,bottom),
        180:(-scale,0,0,scale,right,bottom),
        270:(0,-scale,-scale,0,right,top)}[rotation]
    return PageGeometry(pixels,matrix,crop)


def transform_box(matrix,box):
    a,b,c,d,e,f=matrix
    x0,y0,x1,y1=box
    points=[(a*x+c*y+e,b*x+d*y+f) for x,y in ((x0,y0),(x0,y1),(x1,y0),(x1,y1))]
    return [min(x for x,y in points),min(y for x,y in points),
            max(x for x,y in points),max(y for x,y in points)]
