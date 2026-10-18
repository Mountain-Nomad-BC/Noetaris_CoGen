"""Real JS arithmetic bounds backing allocations independently of CSS layout."""
import json
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]


def geometry(width,height,ratio):
    module=(ROOT/'assets/pdf-canvas.mjs').as_uri()
    program=f"import {{canvasGeometry}} from {json.dumps(module)};try{{console.log(JSON.stringify(canvasGeometry(...JSON.parse(process.argv[1]))))}}catch(e){{console.log(JSON.stringify({{error:e.message}}))}}"
    result=subprocess.run(['node','--input-type=module','-e',program,json.dumps([width,height,ratio])],capture_output=True,text=True,check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize('ratio',[1,2,3,20])
def test_density_changes_backing_pixels_without_changing_citation_space(ratio):
    result=geometry(200,300,ratio)
    assert (result['width'],result['height'])==(200,300)
    assert result['pixelWidth']==200*min(ratio,3)
    assert result['transform'][0]==result['transform'][3]==min(ratio,3)


def test_large_density_is_bounded_without_refusing_an_admitted_css_page():
    result=geometry(3000,3000,3)
    assert result['pixelWidth']*result['pixelHeight']<=16000000
    assert result['pixelWidth']>3000 and result['width']==3000


@pytest.mark.parametrize('width,height',[(0,300),(-1,300),(20000,1),(1,20000),(4001,4000),('not-a-number',300)])
def test_invalid_or_excessive_dimensions_refuse_before_canvas_allocation(width,height):
    assert 'pixel budget' in geometry(width,height,2)['error']
