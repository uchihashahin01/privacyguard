"""Custom rule detector driven by user settings."""

from __future__ import annotations

import re


def _append_match(bucket: list[dict[str, object]], start: int, end: int, value: str) -> None:
    if start >= end:
        return
    bucket.append(
        {
            "start": start,
            "end": end,
            "entity_type": "CUSTOM",
            "value": value,
            "category": "custom",
            "source": "custom",
        }
    )


def detect(text: str, regex_patterns: list[str] | None = None, keywords: list[str] | None = None) -> list[dict[str, object]]:
    """Run user-defined regex and keyword-based redaction rules."""

    regex_patterns = regex_patterns or []
    keywords = keywords or []
    matches: list[dict[str, object]] = []

    for raw_pattern in regex_patterns:
        try:
            pattern = re.compile(raw_pattern, flags=re.IGNORECASE)
        except re.error:
            continue
        for hit in pattern.finditer(text):
            _append_match(matches, hit.start(), hit.end(), hit.group(0))

    for keyword in keywords:
        if not keyword:
            continue
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", flags=re.IGNORECASE)
        for hit in pattern.finditer(text):
            _append_match(matches, hit.start(), hit.end(), hit.group(0))

    seen: set[tuple[int, int]] = set()
    deduped: list[dict[str, object]] = []
    for match in matches:
        key = (int(match["start"]), int(match["end"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)

    return deduped
