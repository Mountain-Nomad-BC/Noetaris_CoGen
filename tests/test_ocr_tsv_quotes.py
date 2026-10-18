from pathlib import Path
import pytest
from nsai.ocr_worker import _read_tsv

HEADER='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'

def table(tmp_path,words):
    p=tmp_path/'words.tsv'
    p.write_text(HEADER+''.join(f'5\t1\t1\t1\t1\t{i}\t0\t0\t10\t10\t95\t{text}\n' for i,text in enumerate(words,1)),encoding='utf-8')
    return p

def test_tesseract_literal_quotes_never_merge_rows(tmp_path):
    result,words=_read_tsv(table(tmp_path,['"hello','world"','x=1']),1,100,100)
    assert [word['text'] for word in words]==['"hello','world"','x=1']
    assert result=='"hello world" x=1'

@pytest.mark.parametrize('word',['x'*201,'a\x01b'])
def test_invalid_word_fails_inside_page_boundary(tmp_path,word):
    with pytest.raises(ValueError):_read_tsv(table(tmp_path,[word]),1,100,100)

def test_zero_area_word_fails_inside_page_boundary(tmp_path):
    p=table(tmp_path,['word']);p.write_text(p.read_text(encoding='utf-8').replace('\t10\t10\t95','\t0\t10\t95'),encoding='utf-8')
    with pytest.raises(ValueError):_read_tsv(p,1,100,100)
