"""Code-point-safe source chunk boundaries with a bounded word-aware preference."""


def iter_text_chunks(text, max_chars=1200):
    if not isinstance(text,str) or type(max_chars) is not int or max_chars<1:
        raise ValueError('Invalid text chunk input')
    offset=0
    while offset<len(text):
        end=min(offset+max_chars,len(text))
        if end<len(text):
            boundary=max((index for index in range(offset+1,end) if text[index].isspace()),default=-1)
            if boundary>offset:
                end=boundary+1
        yield offset,text[offset:end]
        offset=end
