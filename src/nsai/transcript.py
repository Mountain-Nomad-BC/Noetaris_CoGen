"""Original conservative transcript evidence contracts; no enterprise dictionaries or corpora."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import re
from .assembly import canonical_hash


@dataclass(frozen=True)
class Turn:
    id: str
    session_id: str
    speaker: str
    start: int
    end: int
    text: str
    source_sha256: str
    timestamp_ms: int | None = None


def bind_turns(source: str, *, session_id: str, spans: list[dict], max_turns: int = 512) -> tuple[Turn, ...]:
    if not isinstance(source, str) or len(source.encode('utf-8')) > 1024 * 1024:
        raise ValueError('Transcript source budget exceeded')
    if not session_id or len(session_id) > 128 or not spans or len(spans) > max_turns:
        raise ValueError('Transcript session/turn budget invalid')
    source_hash = hashlib.sha256(source.encode('utf-8')).hexdigest()
    turns, prior_end = [], 0
    for span in spans:
        start, end = span.get('start'), span.get('end')
        speaker = span.get('speaker')
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source) or start < prior_end:
            raise ValueError('Turn offset invalid or overlapping')
        if not isinstance(speaker, str) or not speaker.strip() or len(speaker) > 128:
            raise ValueError('Missing/invalid speaker')
        stamp = span.get('timestamp_ms')
        if stamp is not None and (type(stamp) is not int or stamp < 0):
            raise ValueError('Invalid turn time')
        text = source[start:end]
        if 'text' in span and span['text'] != text:
            raise ValueError('Turn text differs from original source slice')
        identity = canonical_hash({'source': source_hash, 'session': session_id, 'speaker': speaker, 'start': start, 'end': end})
        turns.append(Turn(identity, session_id, speaker, start, end, text, source_hash, stamp))
        prior_end = end
    return tuple(turns)


def classify_turn(turn: Turn) -> dict:
    text = turn.text.strip()
    lower = text.casefold()
    flags = {
        'question': text.endswith('?') or bool(re.match(r'^(what|when|where|who|why|how|is|are|can|could|does|do)\b', lower)),
        'request': bool(re.match(r'^(please|could you|can you|would you)\b', lower)),
        'conditional': bool(re.search(r'\b(if|unless|provided that)\b', lower)),
        'negated': bool(re.search(r"\b(no|not|never|cannot|without)\b|n['’]t\b", lower)),
        'historical': bool(re.search(r'\b(previously|yesterday|formerly|last week|used to)\b', lower)),
        'proposed_action': bool(re.search(r'\b(will|plan to|going to|should)\b', lower)),
        'reported_outcome': bool(re.search(r'\b(completed|resolved|failed|succeeded)\b', lower)),
    }
    kind = next((key for key in ('question', 'request', 'conditional', 'historical', 'proposed_action', 'reported_outcome') if flags[key]), 'assertion')
    return {'turn_id': turn.id, 'kind': kind, 'flags': flags, 'confidence_kind': 'deterministic-pattern-coverage',
            'confidence_probability': None, 'verified': False, 'locator': {'start': turn.start, 'end': turn.end},
            'source_sha256': turn.source_sha256}


def request_answer_links(turns: tuple[Turn, ...]) -> tuple[dict, ...]:
    """Adjacent scoped evidence links are candidates, never a manual specification or verified answer."""
    links = []
    for question, answer in zip(turns, turns[1:]):
        if question.session_id != answer.session_id or question.source_sha256 != answer.source_sha256:
            continue
        if question.speaker == answer.speaker or classify_turn(question)['kind'] not in {'question', 'request'}:
            continue
        answer_class = classify_turn(answer)
        if answer_class['kind'] != 'assertion' or answer_class['flags']['negated']:
            continue
        quantities = []
        for match in re.finditer(r'(?<![\w.])([+-]?\d{1,28}(?:\.\d{1,18})?)\s*(%|[A-Za-z°][A-Za-z°/]{0,15})(?!\w)', answer.text):
            quantity = Decimal(match.group(1))
            if quantity.is_finite():
                quantities.append({'value': str(quantity), 'unit': match.group(2),
                                   'start': answer.start + match.start(), 'end': answer.start + match.end()})
        if quantities:
            links.append({'question_turn': question.id, 'answer_turn': answer.id, 'session_id': answer.session_id,
                          'source_sha256': answer.source_sha256, 'quantities': quantities, 'state': 'candidate',
                          'support_kind': 'adjacent-turn-candidate', 'verified': False})
    return tuple(links)
