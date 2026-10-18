"""Original bounded lexical-query alternatives, without semantic rewriting."""
from dataclasses import dataclass
import re
import unicodedata

# Only a terminal, punctuation-separated presentation clause is removable.
# Content-bearing words, negation, numbers, units and revision text remain.
_PRESENTATION=re.compile(r'(?:[.!?]\s+|\n\s*)(?:please\s+)?(?:answer|respond|reply)\s+'
    r'(?:briefly|concisely|in\s+(?:one|a)\s+sentence|in\s+one\s+paragraph|'
    r'(?:using|with)\s+(?:bullets|bullet\s+points))\s*[.!]?\s*$',re.I)
_WORDS=re.compile(r'[^\W_]+',re.UNICODE)
_COMPOUND=re.compile(r'\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b')
_CAMEL=re.compile(r'\b[A-Z][a-z0-9]+(?:[A-Z][A-Za-z0-9]*)+\b')
_SYNTAX={'what','is','the','a','an','of','for','please','tell','me','about','and','or',
    'does','do','can','you','give','how','which','with','are','to','in','on'}

@dataclass(frozen=True)
class RetrievalQuery:
    exact: str
    alternate: str
    entity_gate: str | None
    entities: tuple[str,...]
    presentation_removed: bool

def build_retrieval_query(question: str) -> RetrievalQuery:
    if not isinstance(question,str) or not 1<=len(question)<=1000 or '\x00' in question:
        raise ValueError('Question must be bounded nonempty text without NUL')
    normalized=unicodedata.normalize('NFC',question).strip()
    match=_PRESENTATION.search(normalized)
    removed=False
    if match:
        prefix=normalized[:match.start()]
        # A terminal instruction inside an open quoted excerpt is source text.
        if prefix.strip() and prefix.count('"')%2==0 and prefix.count('“')==prefix.count('”'):
            normalized=prefix.strip();removed=True
    normalized=' '.join(normalized.split())
    terms=list(dict.fromkeys(word.lower() for word in _WORDS.findall(normalized) if word.lower() not in _SYNTAX))
    # Never reinterpret user tokens as the websearch OR/minus/quote operators.
    alternate=' OR '.join('"'+term+'"' for term in terms)
    compounds=[match.group() for match in _COMPOUND.finditer(normalized)
        if match.group().split('-')[0].lower() not in {'revision','version','rev','page','line'}]
    compounds.extend(match.group() for match in _CAMEL.finditer(normalized))
    entities=tuple(dict.fromkeys(value.lower() for value in compounds))
    gate=' OR '.join('"'+entity+'"' for entity in entities) if entities else None
    return RetrievalQuery(exact=normalized,alternate=alternate,entity_gate=gate,entities=entities,presentation_removed=removed)
