"""Original, additive quote selectors. A selector is not a verified visual match."""
import hashlib
import re


def citation_from_hit(hit):
    result=dict(chunk_id=hit['id'],document_id=hit['document_id'],locator=hit['locator'],
        title=hit['title'],revision=hit['revision'],original_sha256=hit['original_sha256'],
        excerpt=hit['text'],extraction_complete=hit.get('extraction_complete'),page_coverage=hit.get('page_coverage'))
    anchor=quote_anchor(hit)
    if anchor is not None:result['anchor']=anchor
    return result


def quote_anchor(hit):
    """Bind a bounded exact extraction quote to immutable source identity.

    Offsets within a retrieval excerpt are deliberately not represented as PDF
    positions. Browser/native extraction alignment requires separate evidence.
    """
    document_id = hit.get('document_id')
    digest = hit.get('original_sha256')
    revision = hit.get('revision')
    quote = hit.get('text')
    locator = hit.get('locator')
    if not isinstance(document_id, str) or not re.fullmatch('[a-f0-9]{32}', document_id):
        return None
    if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
        return None
    if not isinstance(revision, str) or not 1 <= len(revision) <= 50:
        return None
    if not isinstance(quote, str) or not quote.strip() or len(quote.encode('utf-8')) > 64000:
        return None
    if not isinstance(locator, str) or len(locator) > 200:
        return None
    match = re.fullmatch(r'page:([1-9][0-9]*):line:([1-9][0-9]*)', locator)
    return dict(schema='nsai.citation-anchor/1', document_id=document_id,
                original_sha256=digest, revision=revision, locator=locator,
                page=int(match[1]) if match else None,
                selector=dict(type='TextQuoteSelector', exact=quote),
                quote_sha256=hashlib.sha256(quote.encode('utf-8')).hexdigest(),
                status='page-only' if match else 'unavailable',
                visual_match_verified=False, normalization='none',
                authority_granted=False)
