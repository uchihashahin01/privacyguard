"""Application settings persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

APP_NAME = "privacyguard"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
SETTINGS_PATH = CONFIG_DIR / "settings.json"


@dataclass(slots=True)
class AppSettings:
    """Runtime configuration persisted as JSON under XDG config paths."""

    enabled_categories: dict[str, bool] = field(
        default_factory=lambda: {
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
    )
    custom_regex: list[str] = field(default_factory=list)
    custom_keywords: list[str] = field(default_factory=list)
    spacy_model: str = "en_core_web_sm"
    check_updates: bool = True
    github_repo: str = "USERNAME/privacyguard"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AppSettings":
        defaults = cls()
        return cls(
            enabled_categories={**defaults.enabled_categories, **payload.get("enabled_categories", {})},
            custom_regex=list(payload.get("custom_regex", [])),
            custom_keywords=list(payload.get("custom_keywords", [])),
            spacy_model=str(payload.get("spacy_model", defaults.spacy_model)),
            check_updates=bool(payload.get("check_updates", defaults.check_updates)),
            github_repo=str(payload.get("github_repo", defaults.github_repo)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled_categories": self.enabled_categories,
            "custom_regex": self.custom_regex,
            "custom_keywords": self.custom_keywords,
            "spacy_model": self.spacy_model,
            "check_updates": self.check_updates,
            "github_repo": self.github_repo,
        }


def load_settings() -> AppSettings:
    """Load settings from disk or return defaults when not present."""

    if not SETTINGS_PATH.exists():
        return AppSettings()

    try:
        payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppSettings()

    if not isinstance(payload, dict):
        return AppSettings()

    return AppSettings.from_dict(payload)


def save_settings(settings: AppSettings) -> None:
    """Persist settings under the user config directory."""

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
