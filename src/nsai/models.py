from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from fractions import Fraction

# Deliberately narrow, deterministic demo extractor. NOT a general LLM/TurnBurn implementation.
PATTERN = re.compile(
    r"(?im)^\s*(?P<subject>[A-Za-z][A-Za-z0-9 _./-]{1,79}?)\s+"
    r"(?P<predicate>maximum operating temperature|operating limit)\s+"
    r"(?:is|=|:)\s*(?P<value>[+-]?\d+(?:\.\d+)?\s*°?\s*[CF])\s*[.]?\s*$"
)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExtractedClaim:
    subject: str
    predicate: str
    value: str
    locator: str


def extract_claims(text: str) -> list[ExtractedClaim]:
    claims = []
    for match in PATTERN.finditer(text):
        if re.search(r'\b(if|unless|when|provided|not|never|previously|formerly|was|were)\b',match.group(),re.I):
            continue
        line = text.count("\n", 0, match.start()) + 1
        claims.append(ExtractedClaim(
            subject=" ".join(match.group("subject").lower().split()),
            predicate=match.group("predicate").lower(),
            value=match.group("value").replace(" ", "").replace("°", "").upper(),
            locator=f"line:{line}",
        ))
    return claims


def conflict_groups(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], dict[str, list]] = {}
    identities = {}
    for row in rows:
        key = (row["subject"], row["predicate"],row.get('conditions',''),row.get('valid_from'),row.get('valid_until'))
        identity = quantity_identity(row['value'])
        label = identities.setdefault((key,identity),row['value'])
        groups.setdefault(key, {}).setdefault(label, []).append({
            "claim_id": row["id"], "document_id": row["document_id"], "locator": row["locator"]
        })
    return [
        {"subject": subject, "predicate": predicate, "alternatives": values}
        for (subject, predicate,conditions,valid_from,valid_until), values in groups.items() if len(values) > 1
    ]

def quantity_identity(value):
    """Exact rational Celsius identity; no tolerance that can hide a real conflict."""
    match=re.fullmatch(r'\s*([+-]?\d+(?:\.\d+)?)\s*°?\s*([CF])\s*',value,re.I)
    if not match:return ('unsupported',value)
    number=Fraction(Decimal(match[1]))
    if match[2].upper()=='F':number=(number-32)*Fraction(5,9)
    return ('temperature-celsius',number.numerator,number.denominator)

def observe_statements(text):
    """Conservative source observations, separate from unconditional fact extraction."""
    observations=[]
    for line_number,line in enumerate(text.splitlines(),1):
        value=line.strip()
        if not value:continue
        lower=value.casefold()
        if value.endswith('?'):state='question'
        elif re.search(r'\b(if|unless|when|provided|under)\b',lower):state='conditional'
        elif re.search(r'\b(was|were|previously|formerly|historical)\b',lower):state='historical'
        elif re.search(r'\b(not|never|no)\b',lower):state='negated'
        elif re.search(r'\b(will|should|must)\b',lower):state='proposed-action'
        elif PATTERN.fullmatch(value):state='assertion-supported-form'
        else:state='unsupported'
        observations.append(dict(locator=f'line:{line_number}',raw_text=value,epistemic_state=state,authority='observation-only'))
    return observations
