from __future__ import annotations

import json
from pathlib import Path

import pytest

from privacyguard.engine.redactor import Redactor

CORPUS_PATH = Path(__file__).with_name("corpus_samples.json")


def _load_corpus() -> list[dict[str, object]]:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def _token_present(redacted_text: str, matcher: str) -> bool:
    options = matcher.split("|")
    return any(f"[{item}_" in redacted_text for item in options)


@pytest.mark.parametrize("sample", _load_corpus(), ids=lambda row: str(row["name"]))
def test_corpus_redaction_cases(sample: dict[str, object]) -> None:
    engine = Redactor()
    text = str(sample["text"])
    custom_keywords = [str(item) for item in sample.get("custom_keywords", [])]
    custom_regex = [str(item) for item in sample.get("custom_regex", [])]

    result = engine.redact(text, custom_keywords=custom_keywords, custom_regex=custom_regex)

    expected_any = [str(item) for item in sample.get("expected_any", [])]
    for matcher in expected_any:
        assert _token_present(result.redacted_text, matcher), (
            f"Expected one of {matcher} in redacted output for sample {sample['name']}"
        )

    # Each case should be reversible using in-memory token mapping.
    assert result.restore_text() == text


def test_corpus_toggle_respects_disabled_category() -> None:
    engine = Redactor()
    text = "Contact via jane@example.com and +1 202-555-0102"

    result = engine.redact(text, enabled_categories={"emails": False, "phones": True})

    assert "jane@example.com" in result.redacted_text
    assert "[PHONE_" in result.redacted_text
