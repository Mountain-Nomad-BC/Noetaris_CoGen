import copy
import pytest
from nsai.scientific_math import extract_math,extract_latex_math,MAX_RECORDS

def parsed(*texts):
    return dict(original_sha256='a'*64,spans=[dict(locator=f'page:1:line:{i+1}',page=1,text=text) for i,text in enumerate(texts)])

def extract(value):return extract_math(value,'b'*32,'v1')

@pytest.mark.parametrize('text',['E = mc²','x + y = 3','α ≤ β','𝑥 = 𝑦','profit = revenue - cost','O(n log n)','∫ f(x) dx','(3) y = 2*x'])
def test_math_notation_is_source_quoted_without_reconstruction(text):
    record=extract(parsed(text))['records'][0]
    assert record['source']['text']==text and record['latex'] is None and record['evaluation']=='not_attempted'
    assert record['review_required'] and record['confidence']['probability'] is None and not record['generated_execution']

@pytest.mark.parametrize('text',['A paragraph about pumps and valves.','Do not start the pump.','5 C and 10 mm','well-known long-term results','Figure (3) shows the data.','https://example.org/?x=2','(3)','status = complete'])
def test_nonmath_controls_do_not_become_equations(text):
    result=extract(parsed(text));assert result['records']==[] and result['coverage']['exhaustive'] is False

def test_unicode_offsets_negation_conditions_and_context_remain_exact():
    value=parsed('Do not apply this outside the stated domain.','  If α > 0, x = α + 1.  ','Only when the boundary is fixed.')
    original=copy.deepcopy(value);record=extract(value)['records'][0];source=record['source'];text=value['spans'][1]['text']
    assert text[source['offset_start']:source['offset_end']]==source['text']=='If α > 0, x = α + 1.'
    assert [r['text'] for r in record['context']]==['Do not apply this outside the stated domain.','Only when the boundary is fixed.']
    assert value==original

def test_multiline_display_continuation_is_linked_not_reconstructed():
    result=extract(parsed('f(x) =','  a + b','  + c','(2)'))
    assert len(result['records'])==4
    assert len({r['continuation_group'] for r in result['records']})==1
    assert result['records'][1]['continuation_of']==result['records'][0]['id']

def test_stable_ids_change_with_source_revision_and_location():
    value=parsed('x = 1');first=extract(value)['records'][0]['id'];assert first==extract(value)['records'][0]['id']
    assert first!=extract_math(value,'b'*32,'v2')['records'][0]['id']
    moved=parsed('plain prose','x = 1');assert first!=extract(moved)['records'][0]['id']

def test_limits_are_explicit_and_do_not_silently_claim_complete_math():
    result=extract(dict(original_sha256='a'*64,spans=[dict(locator='page:1:line:1',page=1,text='\n'.join(['x = 1']*(MAX_RECORDS+1)))]))
    assert len(result['records'])==MAX_RECORDS and result['coverage']['omitted_records']==1 and result['coverage']['truncated'] and not result['processing_complete']
    result=extract(parsed('x = '+('1+'*2100)))
    assert not result['records'] and result['coverage']['oversize_candidates']==1

def test_page_disagreement_and_duplicate_locators_are_rejected():
    value=parsed('x = 1');value['spans'][0]['page']=2
    with pytest.raises(ValueError,match='disagree'):extract(value)
    value=parsed('x = 1');value['spans']*=2
    with pytest.raises(ValueError,match='Duplicate'):extract(value)

def test_exact_crlf_offsets_and_no_cross_page_continuation():
    value=dict(original_sha256='a'*64,spans=[dict(locator='page:1:line:1',page=1,text='  x = 1\r\n  y = 2\r\n'),dict(locator='page:2:line:1',page=2,text='+ z')])
    records=extract(value)['records'];assert len(records)==2
    for record in records:
        source=record['source'];original=value['spans'][0]['text']
        assert original[source['offset_start']:source['offset_end']]==source['text']
    assert records[1]['continuation_of'] is None

def test_aggregate_json_guard_fails_instead_of_silently_dropping_records():
    value=dict(original_sha256='a'*64,spans=[dict(locator=('source:'+str(i)+':').ljust(200,'x'),text='x = 1') for i in range(5000)])
    with pytest.raises(ValueError,match='8 MiB'):extract(value)

@pytest.mark.parametrize('document_id',[None,12,False,'../unsafe','a'*31])
def test_invalid_source_identity_is_rejected(document_id):
    with pytest.raises(ValueError,match='identity'):extract_math(parsed('x = 1'),document_id,'v1')

def tex(text,filename='source.tex'):
    return extract_latex_math(text.encode(),filename,pdf_sha256='a'*64,source_archive_sha256='c'*64,document_id='b'*32,revision='v1')

@pytest.mark.parametrize('source',[r'$x=1$',r'$$E=mc^2$$',r'\(x+y\)',r'\[\frac{x}{y}\]',r'\begin{equation}x=1\end{equation}',r'\begin{align*}a&=b\\c&=d\end{align*}'])
def test_author_tex_is_quoted_not_reconstructed_or_pdf_page_claimed(source):
    record=tex('Introduction '+source+' conclusion')['records'][0]
    assert record['latex']==source and record['source']['text']==source and record['source']['page'] is None
    assert record['source_kind']=='author_source_tex_not_pdf' and record['pdf_alignment']=='not_verified' and not record['generated_execution']
    text='Introduction '+source+' conclusion';assert text[record['source']['offset_start']:record['source']['offset_end']]==source

def test_tex_comments_escaped_delimiters_verbatim_and_code_are_excluded():
    source=r'''% $comment$ is excluded
Cost is \$5. \verb|$code$| \verb*+$other$+
\begin{verbatim}$opaque$\end{verbatim}
\begin{lstlisting}$listing$\end{lstlisting}
\begin{minted}{python}$python$\end{minted}
Actual $x=1$ and \(y=2\).
'''
    result=tex(source);assert [r['latex'] for r in result['records']]==['$x=1$',r'\(y=2\)']
    assert result['coverage']['skipped_comment_or_code_regions']==6

def test_comment_cannot_close_author_equation_and_percent_escape_is_literal():
    source='\\begin{equation}x=1 % \\end{equation}\n+y=2\\end{equation}'
    assert tex(source)['records'][0]['latex']==source
    assert tex(r'$x=1\%$')['records'][0]['latex']==r'$x=1\%$'

def test_unclosed_tex_reports_partial_not_complete_extraction():
    result=tex('Good $x=1$ then $unfinished')
    assert len(result['records'])==1 and not result['processing_complete'] and result['status']=='partial_candidate'
    assert result['coverage']['unsupported_regions'][0]['reason']=='unclosed_math_delimiter'

def test_unclosed_opaque_code_reports_unknown_remaining_content():
    result=tex(r'\begin{verbatim}$not admitted as math$')
    assert not result['records'] and not result['processing_complete']
    assert result['coverage']['unsupported_regions'][0]['reason']=='unclosed_opaque_code_region'

def test_tex_utf8_offsets_and_separate_file_identity_are_stable():
    source='α context $x=1$';first=tex(source)['records'][0]
    assert source[first['source']['offset_start']:first['source']['offset_end']]=='$x=1$'
    assert first['id']==tex(source)['records'][0]['id'] and first['id']!=tex(source,'other.tex')['records'][0]['id']

def test_tex_never_opens_includes_or_evaluates_macros():
    source=r'\input{/no/such/file}\newcommand{\danger}{\write18{anything}} $\danger+x$'
    assert tex(source)['records'][0]['latex']==r'$\danger+x$'

def test_tex_oversize_candidate_is_reported_as_omitted():
    result=tex('$'+('x'*4097)+'$')
    assert result['records']==[] and result['coverage']['omitted_records']==1 and not result['processing_complete']

@pytest.mark.parametrize('filename',['../source.tex','source.pdf','C:\\source.tex','source\n.tex'])
def test_tex_source_path_escape_is_rejected(filename):
    with pytest.raises(ValueError,match='basename'):tex('$x$',filename)
