"""PII-focused detection routines."""

from __future__ import annotations

import re
from functools import lru_cache

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}(?!\w)")
DOB_RE = re.compile(
    r"\b(?:dob|date\s+of\s+birth|born\s+on)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
    flags=re.IGNORECASE,
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
NID_RE = re.compile(r"\b(?:[A-Z]{1,3}\d{6,12}|\d{8,14})\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
NAME_FALLBACK_RE = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b")

COMMON_FIRST_NAMES = {
    "alice",
    "bob",
    "charlie",
    "david",
    "emma",
    "john",
    "jane",
    "michael",
    "olivia",
    "sarah",
}


@lru_cache(maxsize=2)
def _load_nlp(model_name: str):
    try:
        import spacy

        return spacy.load(model_name)
    except Exception:
        return None


def _luhn_valid(candidate: str) -> bool:
    digits = [int(ch) for ch in candidate if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False

    checksum = 0
    parity = len(digits) % 2
    for idx, digit in enumerate(digits):
        if idx % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _append_match(bucket: list[dict[str, object]], start: int, end: int, entity_type: str, value: str) -> None:
    if start >= end:
        return
    bucket.append(
        {
            "start": start,
            "end": end,
            "entity_type": entity_type,
            "value": value,
            "category": "pii",
            "source": "pii",
        }
    )


def _is_plausible_phone(value: str) -> bool:
    digits = [ch for ch in value if ch.isdigit()]
    return 7 <= len(digits) <= 15


def detect(text: str, model_name: str = "en_core_web_sm") -> list[dict[str, object]]:
    """Detect common personally identifying entities in text."""

    matches: list[dict[str, object]] = []

    for hit in EMAIL_RE.finditer(text):
        _append_match(matches, hit.start(), hit.end(), "EMAIL", hit.group(0))

    for hit in PHONE_RE.finditer(text):
        value = hit.group(0)
        if SSN_RE.fullmatch(value):
            continue
        if _is_plausible_phone(value):
            _append_match(matches, hit.start(), hit.end(), "PHONE", value)

    for regex, entity_type in ((SSN_RE, "SSN"), (NID_RE, "NID")):
        for hit in regex.finditer(text):
            _append_match(matches, hit.start(), hit.end(), entity_type, hit.group(0))

    for hit in DOB_RE.finditer(text):
        dob = hit.group(1)
        if dob:
            _append_match(matches, hit.start(1), hit.end(1), "DOB", dob)

    for hit in CREDIT_CARD_RE.finditer(text):
        value = hit.group(0)
        if _luhn_valid(value):
            _append_match(matches, hit.start(), hit.end(), "CREDIT_CARD", value)

    nlp = _load_nlp(model_name)
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                _append_match(matches, ent.start_char, ent.end_char, "PERSON", ent.text)
    else:
        for hit in NAME_FALLBACK_RE.finditer(text):
            first_token = hit.group(1).split()[0].lower()
            if first_token in COMMON_FIRST_NAMES or len(hit.group(1).split()) >= 2:
                _append_match(matches, hit.start(1), hit.end(1), "PERSON", hit.group(1))

    seen: set[tuple[int, int, str]] = set()
    unique_matches: list[dict[str, object]] = []
    for match in matches:
        key = (int(match["start"]), int(match["end"]), str(match["entity_type"]))
        if key in seen:
            continue
        seen.add(key)
        unique_matches.append(match)

    return unique_matches
