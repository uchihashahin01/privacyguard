"""Central redaction orchestrator."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

from privacyguard.engine import custom, location, pii, secrets

CATEGORY_PRIORITY = {"secrets": 0, "pii": 1, "location": 2, "custom": 3}
TOKEN_SAFE_RE = re.compile(r"[^A-Z0-9]+")


@dataclass(slots=True, frozen=True)
class Match:
    start: int
    end: int
    entity_type: str
    value: str
    category: str
    source: str

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(slots=True, frozen=True)
class Replacement:
    original_start: int
    original_end: int
    output_start: int
    output_end: int
    token: str
    original_value: str
    entity_type: str
    category: str


@dataclass(slots=True)
class RedactionResult:
    original_text: str
    redacted_text: str
    replacements: list[Replacement]
    token_to_original: dict[str, str]
    counts_by_type: dict[str, int]
    counts_by_category: dict[str, int]

    def restore_text(self, text: str | None = None) -> str:
        """Restore tokenized text back to original values."""

        restored = self.redacted_text if text is None else text
        for replacement in sorted(self.replacements, key=lambda item: len(item.token), reverse=True):
            restored = restored.replace(replacement.token, replacement.original_value)
        return restored


class Redactor:
    """Pipeline redactor for PII, location, secret, and custom matches."""

    def __init__(self, spacy_model: str = "en_core_web_sm") -> None:
        self.spacy_model = spacy_model

    def redact(
        self,
        text: str,
        enabled_categories: dict[str, bool] | None = None,
        custom_regex: list[str] | None = None,
        custom_keywords: list[str] | None = None,
    ) -> RedactionResult:
        normalized_text = self._normalize(text)
        options = self._merged_options(enabled_categories)

        candidates: list[Match] = []
        candidates.extend(self._to_matches(pii.detect(normalized_text, model_name=self.spacy_model)))
        candidates.extend(self._to_matches(secrets.detect(normalized_text)))
        candidates.extend(self._to_matches(location.detect(normalized_text, model_name=self.spacy_model)))

        if options["custom"] and (custom_regex or custom_keywords):
            custom_hits = custom.detect(normalized_text, regex_patterns=custom_regex, keywords=custom_keywords)
            candidates.extend(self._to_matches(custom_hits))

        filtered = [match for match in candidates if self._is_enabled(match, options)]
        selected = self._resolve_overlaps(filtered)
        return self._apply_replacements(normalized_text, selected)

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lstrip("\ufeff")
        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def _to_matches(raw_matches: list[dict[str, object]]) -> list[Match]:
        parsed: list[Match] = []
        for item in raw_matches:
            try:
                parsed.append(
                    Match(
                        start=int(item["start"]),
                        end=int(item["end"]),
                        entity_type=str(item["entity_type"]).upper(),
                        value=str(item["value"]),
                        category=str(item["category"]),
                        source=str(item.get("source", "unknown")),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return parsed

    @staticmethod
    def _merged_options(enabled_categories: dict[str, bool] | None) -> dict[str, bool]:
        defaults = {
            "names": True,
            "emails": True,
            "phones": True,
            "api_keys": True,
            "addresses": True,
            "custom": True,
            "birth_dates": True,
            "credit_cards": True,
            "national_ids": True,
            "ips": True,
        }
        if enabled_categories:
            defaults.update(enabled_categories)
        return defaults

    @staticmethod
    def _is_enabled(match: Match, options: dict[str, bool]) -> bool:
        if match.category == "secrets":
            return options.get("api_keys", True)
        if match.category == "custom":
            return options.get("custom", True)

        if match.entity_type == "PERSON":
            return options.get("names", True)
        if match.entity_type == "EMAIL":
            return options.get("emails", True)
        if match.entity_type == "PHONE":
            return options.get("phones", True)
        if match.entity_type in {"ADDRESS", "LOCATION"}:
            return options.get("addresses", True)
        if match.entity_type in {"IPV4", "IPV6"}:
            return options.get("ips", True) and options.get("addresses", True)
        if match.entity_type == "DOB":
            return options.get("birth_dates", True)
        if match.entity_type == "CREDIT_CARD":
            return options.get("credit_cards", True)
        if match.entity_type in {"SSN", "NID"}:
            return options.get("national_ids", True)

        return True

    @staticmethod
    def _overlaps(a: Match, b: Match) -> bool:
        return a.start < b.end and b.start < a.end

    def _resolve_overlaps(self, matches: list[Match]) -> list[Match]:
        quality_sorted = sorted(
            (match for match in matches if match.start < match.end),
            key=lambda match: (
                -match.length,
                CATEGORY_PRIORITY.get(match.category, 99),
                match.start,
            ),
        )

        selected: list[Match] = []
        for candidate in quality_sorted:
            if any(self._overlaps(candidate, current) for current in selected):
                continue
            selected.append(candidate)

        return sorted(selected, key=lambda match: match.start)

    def _apply_replacements(self, text: str, matches: list[Match]) -> RedactionResult:
        pieces: list[str] = []
        token_to_original: dict[str, str] = {}
        replacements: list[Replacement] = []
        counts_by_type: dict[str, int] = defaultdict(int)
        counts_by_category: dict[str, int] = defaultdict(int)

        cursor = 0
        output_cursor = 0

        for match in matches:
            if match.start < cursor:
                continue

            untouched = text[cursor:match.start]
            pieces.append(untouched)
            output_cursor += len(untouched)

            prefix = TOKEN_SAFE_RE.sub("_", match.entity_type.upper()).strip("_") or "REDACTED"
            counts_by_type[prefix] += 1
            counts_by_category[match.category] += 1
            token = f"[{prefix}_{counts_by_type[prefix]}]"

            output_start = output_cursor
            pieces.append(token)
            output_cursor += len(token)

            replacements.append(
                Replacement(
                    original_start=match.start,
                    original_end=match.end,
                    output_start=output_start,
                    output_end=output_cursor,
                    token=token,
                    original_value=match.value,
                    entity_type=match.entity_type,
                    category=match.category,
                )
            )
            token_to_original[token] = match.value
            cursor = match.end

        remainder = text[cursor:]
        pieces.append(remainder)
        redacted = "".join(pieces)

        return RedactionResult(
            original_text=text,
            redacted_text=redacted,
            replacements=replacements,
            token_to_original=token_to_original,
            counts_by_type=dict(counts_by_type),
            counts_by_category=dict(counts_by_category),
        )
