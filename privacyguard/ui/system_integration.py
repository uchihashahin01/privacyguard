"""Desktop integration helpers for Linux launchers and tray behavior."""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

from gi.repository import GLib, Gtk

DESKTOP_ENTRY_PATH = Path.home() / ".local" / "share" / "applications" / "privacyguard.desktop"


def ensure_user_desktop_entry(exec_path: str | None = None) -> None:
    """Create a user-level desktop entry on first launch and refresh menu cache."""

    if DESKTOP_ENTRY_PATH.exists():
        return

    command_path = exec_path or shutil.which("privacyguard") or "/usr/local/bin/privacyguard"
    DESKTOP_ENTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP_ENTRY_PATH.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Name=PrivacyGuard",
                "Comment=Redact sensitive info before pasting to AI",
                f"Exec={command_path}",
                "Icon=security-high",
                "Terminal=false",
                "Type=Application",
                "Categories=Utility;Security;",
                "StartupWMClass=privacyguard",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        subprocess.run(
            ["update-desktop-database", str(DESKTOP_ENTRY_PATH.parent)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        # The menu entry still works on many desktops even without the cache command.
        return


class TrayController:
    """Handles minimize-to-tray behavior with pystray in a daemon thread."""

    def __init__(self, window: Gtk.Window, app: Gtk.Application) -> None:
        self._window = window
        self._app = app
        self._tray_icon: Any | None = None
        self._tray_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._allow_close = False
        self._app_is_held = False
        self._pystray_module: Any | None = None

    def _ensure_app_hold(self) -> None:
        if self._app_is_held:
            return
        self._app.hold()
        self._app_is_held = True

    def _release_app_hold(self) -> None:
        if not self._app_is_held:
            return
        self._app.release()
        self._app_is_held = False

    def handle_close_request(self) -> bool:
        """Hide window and move app to tray unless an explicit quit was requested."""

        if self._allow_close:
            return False

        self._ensure_app_hold()
        self._window.hide()
        started = self._start_tray_icon()
        if not started:
            self._release_app_hold()
            self._window.present()
        return True

    def _start_tray_icon(self) -> bool:
        """Start tray icon using backend-appropriate lifecycle."""

        with self._lock:
            if self._tray_icon is not None:
                return True
            if self._tray_thread is not None and self._tray_thread.is_alive():
                return True

        try:
            # Gtk4 apps cannot load pystray's AppIndicator backend (Gtk3-only).
            # Force xorg backend to avoid GTK namespace conflicts on Linux.
            os.environ["PYSTRAY_BACKEND"] = "xorg"
            import pystray
            from PIL import Image, ImageDraw
            self._pystray_module = pystray
        except Exception:
            return False

        try:
            image = self._build_tray_icon(Image, ImageDraw)
            
            # Create menu with default action for left-click
            menu = pystray.Menu(
                pystray.MenuItem("Show PrivacyGuard", self._on_menu_show, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._on_menu_quit),
            )
            icon = pystray.Icon("privacyguard", image, "PrivacyGuard - Click to restore", menu)

            with self._lock:
                self._tray_icon = icon

            self._tray_thread = threading.Thread(
                target=self._run_tray_loop,
                args=(icon,),
                name="privacyguard-tray",
                daemon=True,
            )
            self._tray_thread.start()
            return True
        except Exception as e:
            print(f"Tray icon error: {e}")
            with self._lock:
                self._tray_icon = None
                self._tray_thread = None
            return False

    def _run_tray_loop(self, icon: Any) -> None:
        """Run the tray icon event loop with click handling."""
        try:
            # For xorg backend, we need to set up click handling after run_detached
            if hasattr(icon, 'run_detached'):
                icon.run_detached()
                # Set up a polling mechanism for the xorg backend
                self._setup_xorg_click_handler(icon)
            else:
                icon.run()
        except Exception as e:
            print(f"Tray loop error: {e}")
            GLib.idle_add(self.show_window)
        finally:
            with self._lock:
                self._tray_icon = None
                self._tray_thread = None

    def _setup_xorg_click_handler(self, icon: Any) -> None:
        """Set up click handling for the xorg backend."""
        try:
            from Xlib import X, display
            from Xlib.ext import record
            from Xlib.protocol import rq
        except ImportError:
            # If Xlib is not available, fall back to regular run
            icon.run()
            return
        
        # Just run the icon normally - the default menu item handles clicks
        icon.run()

    @staticmethod
    def _build_tray_icon(image_mod, draw_mod):
        """Build a modern, vibrant tray icon matching the new UI theme."""
        image = image_mod.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = draw_mod.Draw(image)

        # Background circle with gradient-like effect (purple theme)
        draw.ellipse((4, 4, 60, 60), fill=(139, 92, 246, 255))  # Purple
        draw.ellipse((8, 8, 56, 56), fill=(168, 85, 247, 255))  # Lighter purple
        
        # Shield shape
        draw.polygon(
            [(32, 12), (50, 20), (50, 36), (44, 46), (32, 52), (20, 46), (14, 36), (14, 20)],
            fill=(255, 255, 255, 255),
        )
        
        # Lock icon inside shield
        draw.rounded_rectangle((24, 30, 40, 44), radius=3, fill=(139, 92, 246, 255))
        draw.rectangle((28, 24, 36, 32), fill=(139, 92, 246, 255))
        draw.ellipse((26, 20, 38, 32), outline=(139, 92, 246, 255), width=3)
        
        return image

    def _on_menu_show(self, _icon: Any = None, _item: Any = None) -> None:
        """Handle show menu item click."""
        GLib.idle_add(self.show_window)

    def _on_menu_quit(self, _icon: Any = None, _item: Any = None) -> None:
        """Handle quit menu item click."""
        GLib.idle_add(self.quit_application)

    def show_window(self) -> bool:
        """Show the main application window and stop the tray icon."""
        self._stop_tray_icon_sync()
        self._release_app_hold()
        self._window.set_visible(True)
        self._window.show()
        self._window.present()
        return False

    def quit_application(self) -> bool:
        """Quit the application completely."""
        self._allow_close = True
        self._stop_tray_icon_sync()
        self._release_app_hold()
        self._app.quit()
        return False

    def _stop_tray_icon_async(self) -> None:
        """Stop the tray icon in a separate thread."""
        thread = threading.Thread(target=self._stop_tray_icon_sync, name="privacyguard-tray-stop", daemon=True)
        thread.start()

    def _stop_tray_icon_sync(self) -> None:
        """Stop the tray icon synchronously."""
        with self._lock:
            icon = self._tray_icon
            self._tray_icon = None
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                pass
