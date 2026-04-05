"""Application entrypoint for PrivacyGuard."""

from __future__ import annotations

import shutil
import sys

from privacyguard.config.settings import load_settings

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")

    from gi.repository import Adw
except Exception as exc:  # pragma: no cover - depends on runtime desktop libs
    sys.stderr.write(
        "PrivacyGuard requires GTK4/Libadwaita bindings (PyGObject).\n"
        f"Import error: {exc}\n"
    )
    sys.exit(1)

from privacyguard.ui.window import PrivacyGuardWindow
from privacyguard.ui.system_integration import ensure_user_desktop_entry


class PrivacyGuardApplication(Adw.Application):
    """Adwaita application shell."""

    def __init__(self) -> None:
        super().__init__(application_id="com.privacyguard.app")
        self._window: PrivacyGuardWindow | None = None
        self.connect("activate", self._on_activate)

    def _on_activate(self, app: Adw.Application) -> None:
        ensure_user_desktop_entry(exec_path=shutil.which("privacyguard"))

        if self._window is None:
            settings = load_settings()
            self._window = PrivacyGuardWindow(app=app, settings=settings)

        self._window.present_main_window()


def main() -> int:
    app = PrivacyGuardApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
