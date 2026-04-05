"""GitHub release-based update checker."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

import requests
from packaging.version import Version

from privacyguard import __version__

LATEST_ENDPOINT = "https://api.github.com/repos/{repo}/releases/latest"


@dataclass(slots=True, frozen=True)
class UpdateInfo:
    version: str
    html_url: str
    body: str
    assets: list[dict[str, str]]


class UpdateChecker:
    """Checks GitHub Releases in a non-blocking background thread."""

    def __init__(self, repo: str, timeout: float = 5.0) -> None:
        self.repo = repo
        self.timeout = timeout

    def check_in_background(
        self,
        on_update: Callable[[UpdateInfo], None],
        on_error: Callable[[str], None] | None = None,
    ) -> threading.Thread:
        thread = threading.Thread(
            target=self._run_check,
            args=(on_update, on_error),
            daemon=True,
            name="privacyguard-update-check",
        )
        thread.start()
        return thread

    def _run_check(
        self,
        on_update: Callable[[UpdateInfo], None],
        on_error: Callable[[str], None],
    ) -> None:
        try:
            response = requests.get(
                LATEST_ENDPOINT.format(repo=self.repo),
                timeout=self.timeout,
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
            payload = response.json()

            tag_name = str(payload.get("tag_name", "")).lstrip("v")
            if not tag_name:
                return

            remote = Version(tag_name)
            local = Version(__version__)
            if remote <= local:
                return

            info = UpdateInfo(
                version=f"v{remote}",
                html_url=str(payload.get("html_url", "")),
                body=str(payload.get("body", "")),
                assets=[
                    {
                        "name": str(asset.get("name", "")),
                        "browser_download_url": str(asset.get("browser_download_url", "")),
                    }
                    for asset in payload.get("assets", [])
                    if isinstance(asset, dict)
                ],
            )
            on_update(info)
        except Exception as exc:
            if on_error is not None:
                on_error(str(exc))
