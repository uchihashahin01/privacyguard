"""Secret and token detection routines."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

DEFAULT_PATTERNS: list[dict[str, str]] = [
    {"name": "OPENAI_KEY", "regex": r"\bsk-[A-Za-z0-9]{20,}\b"},
    {"name": "GITHUB_TOKEN", "regex": r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"},
    {"name": "AWS_ACCESS_KEY", "regex": r"\bAKIA[0-9A-Z]{16}\b"},
    {"name": "STRIPE_KEY", "regex": r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{16,}\b"},
    {"name": "GOOGLE_API_KEY", "regex": r"\bAIza[0-9A-Za-z\-_]{35}\b"},
    {"name": "GENERIC_SECRET", "regex": r"\b[A-Za-z0-9_\-]{32,}\b"},
]

PATTERN_PATH = Path(__file__).resolve().parents[2] / "data" / "patterns.json"


@lru_cache(maxsize=1)
def _load_patterns() -> list[dict[str, str]]:
    if PATTERN_PATH.exists():
        try:
            payload = json.loads(PATTERN_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                loaded: list[dict[str, str]] = []
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "SECRET"))
                    regex = str(item.get("regex", ""))
                    if regex:
                        loaded.append({"name": name, "regex": regex})
                if loaded:
                    return loaded
        except (OSError, json.JSONDecodeError):
            pass
    return DEFAULT_PATTERNS


def _append_match(bucket: list[dict[str, object]], start: int, end: int, entity_type: str, value: str) -> None:
    if start >= end:
        return
    bucket.append(
        {
            "start": start,
            "end": end,
            "entity_type": entity_type,
            "value": value,
            "category": "secrets",
            "source": "secrets",
        }
    )


def _detect_regex_secrets(text: str) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for pattern in _load_patterns():
        entity_type = str(pattern["name"])
        regex = re.compile(pattern["regex"])
        for hit in regex.finditer(text):
            _append_match(matches, hit.start(), hit.end(), entity_type, hit.group(0))
    return matches


def _detect_with_detect_secrets(text: str) -> list[dict[str, object]]:
    """Use detect-secrets line scanners when available."""

    try:
        from detect_secrets.core.scan import scan_line
    except Exception:
        return []

    matches: list[dict[str, object]] = []
    offset = 0
    for line_number, line in enumerate(text.splitlines(keepends=True), start=1):
        potentials = []
        try:
            potentials = list(scan_line(line, filename="<memory>"))
        except TypeError:
            try:
                potentials = list(scan_line(line))
            except Exception:
                potentials = []
        except Exception:
            potentials = []

        for potential in potentials:
            secret_value = getattr(potential, "secret_value", None)
            if not secret_value:
                continue
            index = line.find(secret_value)
            if index < 0:
                continue
            plugin_name = getattr(potential, "type", "DETECT_SECRET")
            start = offset + index
            end = start + len(secret_value)
            _append_match(matches, start, end, str(plugin_name).upper(), secret_value)

        offset += len(line)

    return matches


def detect(text: str) -> list[dict[str, object]]:
    """Detect secrets from regex bank and detect-secrets plugins."""

    matches = _detect_regex_secrets(text)
    matches.extend(_detect_with_detect_secrets(text))

    seen: set[tuple[int, int, str]] = set()
    deduped: list[dict[str, object]] = []
    for match in matches:
        key = (int(match["start"]), int(match["end"]), str(match["entity_type"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)

    return deduped
