import json
import pytest
from nsai.memory import materialize_projection


@pytest.mark.parametrize('text',['a','x'*200,'x'*1800,'\U0001f600'*150,'\u00e9'*500],ids=['short','ascii','large','supplementary','accented'])
def test_reported_projection_bytes_equal_exact_wire_serialization(text):
    result=materialize_projection([dict(role='user',text=text)],[],[],[],max_bytes=4096)
    encoded=json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False).encode('utf-8')
    assert result['serialized_bytes']==len(encoded)
    assert len(encoded)<=result['max_bytes']
