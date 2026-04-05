"""Non-modal update banner for available releases."""

from __future__ import annotations

import platform
from dataclasses import dataclass

from gi.repository import Adw, Gio


@dataclass(slots=True, frozen=True)
class ReleaseInfo:
    version: str
    html_url: str
    body: str
    assets: list[dict[str, str]]


def pick_download_url(assets: list[dict[str, str]], fallback_url: str) -> str:
    """Select the best-matching release artifact for the current architecture."""

    if not assets:
        return fallback_url

    machine = platform.machine().lower()
    arch_tokens = {
        "x86_64": ["x86_64", "amd64"],
        "amd64": ["x86_64", "amd64"],
        "aarch64": ["aarch64", "arm64"],
        "arm64": ["aarch64", "arm64"],
    }
    expected = arch_tokens.get(machine, [machine])

    def _score(asset_name: str) -> int:
        name = asset_name.lower()
        score = 0
        if any(token in name for token in expected):
            score += 5
        if name.endswith(".appimage"):
            score += 4
        if name.endswith(".deb"):
            score += 3
        return score

    ranked = sorted(assets, key=lambda item: _score(item.get("name", "")), reverse=True)
    best = ranked[0] if ranked else None
    if best is None:
        return fallback_url

    return best.get("browser_download_url") or fallback_url


class UpdateBannerController:
    """Controller wrapper around Adw.Banner with update-specific behavior."""

    def __init__(self) -> None:
        self.widget = Adw.Banner()
        self._download_url = ""
        self.widget.set_revealed(False)
        self.widget.set_button_label("Download")
        self.widget.connect("button-clicked", self._on_download_clicked)

    def show_update(self, info: ReleaseInfo) -> None:
        summary = info.body.splitlines()[0].strip() if info.body.strip() else "A new release is available."
        self.widget.set_title(f"Version {info.version} available - {summary}")
        self._download_url = pick_download_url(info.assets, info.html_url)
        self.widget.set_revealed(True)

    def _on_download_clicked(self, _banner: Adw.Banner) -> None:
        if not self._download_url:
            return
        Gio.AppInfo.launch_default_for_uri(self._download_url, None)
