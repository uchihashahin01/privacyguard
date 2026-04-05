"""Location and network identifier detectors."""

from __future__ import annotations

import re
from functools import lru_cache

ADDRESS_RE = re.compile(
    r"(?<![\d.])\b\d{1,6}\s+(?!and\b)(?:[A-Za-z0-9.\-]+\s){0,4}"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct)\b",
    flags=re.IGNORECASE,
)
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_RE = re.compile(r"\b(?:[A-F0-9]{1,4}:){2,7}[A-F0-9]{1,4}\b", flags=re.IGNORECASE)


@lru_cache(maxsize=2)
def _load_nlp(model_name: str):
    try:
        import spacy

        return spacy.load(model_name)
    except Exception:
        return None


def _valid_ipv4(value: str) -> bool:
    try:
        return all(0 <= int(chunk) <= 255 for chunk in value.split("."))
    except ValueError:
        return False


def _append_match(bucket: list[dict[str, object]], start: int, end: int, entity_type: str, value: str) -> None:
    if start >= end:
        return
    bucket.append(
        {
            "start": start,
            "end": end,
            "entity_type": entity_type,
            "value": value,
            "category": "location",
            "source": "location",
        }
    )


def detect(text: str, model_name: str = "en_core_web_sm") -> list[dict[str, object]]:
    """Detect address-like entities and IP addresses."""

    matches: list[dict[str, object]] = []

    for hit in ADDRESS_RE.finditer(text):
        _append_match(matches, hit.start(), hit.end(), "ADDRESS", hit.group(0))

    for hit in IPV4_RE.finditer(text):
        value = hit.group(0)
        if _valid_ipv4(value):
            _append_match(matches, hit.start(), hit.end(), "IPV4", value)

    for hit in IPV6_RE.finditer(text):
        _append_match(matches, hit.start(), hit.end(), "IPV6", hit.group(0))

    nlp = _load_nlp(model_name)
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in {"GPE", "LOC"}:
                _append_match(matches, ent.start_char, ent.end_char, "LOCATION", ent.text)

    seen: set[tuple[int, int, str]] = set()
    unique_matches: list[dict[str, object]] = []
    for match in matches:
        key = (int(match["start"]), int(match["end"]), str(match["entity_type"]))
        if key in seen:
            continue
        seen.add(key)
        unique_matches.append(match)

    return unique_matches
