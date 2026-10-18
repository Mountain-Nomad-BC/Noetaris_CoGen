import pytest
from pypdf import PageObject
from pypdf.generic import NameObject, NumberObject, RectangleObject

from nsai.ocr_geometry import page_geometry, transform_box


@pytest.mark.parametrize('rotation,origin,x_step,y_step,pixels', [
    (0, (10, 220), (34, 220), (10, 196), (1000, 750)),
    (90, (10, 40), (10, 64), (34, 40), (750, 1000)),
    (180, (250, 40), (226, 40), (250, 64), (1000, 750)),
    (270, (250, 220), (250, 196), (226, 220), (750, 1000)),
])
def test_known_cropped_page_corner_oracle(rotation, origin, x_step, y_step, pixels):
    page=PageObject.create_blank_page(width=300,height=300)
    page.cropbox=RectangleObject([10,40,250,220]);page.rotate(rotation)
    geometry=page_geometry(page)
    assert geometry.pixels==pixels
    a,b,c,d,e,f=geometry.pixel_to_pdf
    assert (e,f)==origin
    assert (a*100+e,b*100+f)==pytest.approx(x_step)
    assert (c*100+e,d*100+f)==pytest.approx(y_step)
    assert transform_box(geometry.pixel_to_pdf,[0,0,*pixels])==pytest.approx([10,40,250,220])


@pytest.mark.parametrize('crop,rotation,unit', [
    ([-1,0,100,100],0,1), ([0,0,301,100],0,1),
    ([0,0,0,100],0,1), ([0,0,100,100],45,1),
    ([0,0,100,100],0,2),
])
def test_unsupported_geometry_refused(crop,rotation,unit):
    page=PageObject.create_blank_page(width=300,height=300)
    page.cropbox=RectangleObject(crop)
    page[NameObject('/Rotate')]=NumberObject(rotation)
    page[NameObject('/UserUnit')]=NumberObject(unit)
    with pytest.raises(ValueError):page_geometry(page)
