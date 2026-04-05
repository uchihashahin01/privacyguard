"""Main application window and UI wiring."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from privacyguard.config.settings import AppSettings, save_settings
from privacyguard.engine.redactor import RedactionResult, Redactor
from privacyguard.ui.preferences import PreferencesWindow
from privacyguard.ui.system_integration import TrayController
from privacyguard.ui.update_dialog import ReleaseInfo, UpdateBannerController
from privacyguard.updater.checker import UpdateChecker


# Icons for category labels (emoji-based for universal support)
CATEGORY_ICONS = {
    "names": "👤",
    "emails": "📧",
    "phones": "📱",
    "api_keys": "🔑",
    "addresses": "📍",
    "custom": "⚙️",
}

WINDOW_CSS = """
/* ═══════════════════════════════════════════════════════════════════════════
   PRIVACYGUARD - MODERN VIBRANT UI THEME
   A beautiful gradient-based design with glassmorphism effects
   ═══════════════════════════════════════════════════════════════════════════ */

/* ─────────────────────────────────────────────────────────────────────────────
   ROOT & BACKGROUND
   ───────────────────────────────────────────────────────────────────────────── */
.pg-root {
    background: linear-gradient(135deg, #0F0A1F 0%, #1A1033 50%, #0D1525 100%);
}

/* ─────────────────────────────────────────────────────────────────────────────
   HEADER BAR
   ───────────────────────────────────────────────────────────────────────────── */
.pg-headerbar {
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.15) 0%, rgba(15, 10, 31, 0.95) 100%);
    border-bottom: 1px solid rgba(139, 92, 246, 0.3);
    padding: 8px 12px;
    box-shadow: 0 4px 24px rgba(139, 92, 246, 0.15);
}

.pg-header-title-box {
    color: #F3E8FF;
}

.pg-header-title {
    color: #E9D5FF;
    letter-spacing: 0.05em;
    font-size: 15px;
    font-weight: 700;
    text-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
}

/* ─────────────────────────────────────────────────────────────────────────────
   MAIN BODY
   ───────────────────────────────────────────────────────────────────────────── */
.pg-body {
    background: linear-gradient(180deg, #1A1033 0%, #0F172A 100%);
}

/* ─────────────────────────────────────────────────────────────────────────────
   SIDEBAR - Glassmorphism Panel
   ───────────────────────────────────────────────────────────────────────────── */
.pg-sidebar-shell {
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.08) 0%, rgba(6, 182, 212, 0.05) 100%);
    border-right: 1px solid rgba(139, 92, 246, 0.2);
    border-left: 3px solid transparent;
    background-clip: padding-box;
    box-shadow: inset 3px 0 0 0 #8B5CF6, 4px 0 20px rgba(139, 92, 246, 0.1);
}

.pg-section-heading {
    color: #C4B5FD;
    font-size: 10px;
    letter-spacing: 0.15em;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.pg-detection-row {
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 8px 10px;
    margin: 2px 0;
    transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
    background: transparent;
}

.pg-detection-row.hover {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%);
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
    transform: translateX(2px);
}

.pg-detection-label {
    color: #E2E8F0;
    font-size: 13px;
    font-weight: 500;
}

.pg-detection-icon {
    color: #A78BFA;
    margin-right: 8px;
}

separator {
    background: linear-gradient(90deg, transparent 0%, rgba(139, 92, 246, 0.3) 50%, transparent 100%);
    min-height: 1px;
}

/* ─────────────────────────────────────────────────────────────────────────────
   SWITCHES
   ───────────────────────────────────────────────────────────────────────────── */
switch {
    transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    background: rgba(100, 116, 139, 0.3);
    border-radius: 14px;
}

switch:hover {
    background: rgba(139, 92, 246, 0.2);
}

switch slider {
    background: linear-gradient(135deg, #94A3B8 0%, #64748B 100%);
    border-radius: 50%;
    transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

switch:checked {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.4) 0%, rgba(168, 85, 247, 0.3) 100%);
}

switch:checked slider {
    background: linear-gradient(135deg, #A855F7 0%, #8B5CF6 100%);
    box-shadow: 0 0 12px rgba(168, 85, 247, 0.6);
}

/* ─────────────────────────────────────────────────────────────────────────────
   TOOLBAR BUTTONS
   ───────────────────────────────────────────────────────────────────────────── */
.pg-toolbar-button {
    transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 12px;
    min-height: 38px;
    padding: 0 16px;
    background: rgba(139, 92, 246, 0.1);
    color: #E2E8F0;
    border: 1px solid rgba(139, 92, 246, 0.25);
    font-weight: 500;
}

.pg-toolbar-button:hover {
    background: rgba(139, 92, 246, 0.2);
    border-color: rgba(139, 92, 246, 0.4);
    box-shadow: 0 4px 16px rgba(139, 92, 246, 0.2);
    transform: translateY(-1px);
}

.pg-toolbar-button:active {
    transform: translateY(0);
}

/* Primary Redact Button - Eye-catching gradient with glow */
.pg-redact-button {
    background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 50%, #EC4899 100%);
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.5), 0 0 60px rgba(236, 72, 153, 0.3);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.pg-redact-button:hover {
    background: linear-gradient(135deg, #9D6FFF 0%, #B96CFF 50%, #F472B6 100%);
    box-shadow: 0 0 40px rgba(139, 92, 246, 0.7), 0 0 80px rgba(236, 72, 153, 0.4);
    transform: translateY(-2px) scale(1.02);
}

/* Secondary Buttons */
.pg-secondary-button {
    background: rgba(6, 182, 212, 0.1);
    color: #E2E8F0;
    border: 1px solid rgba(6, 182, 212, 0.25);
}

.pg-secondary-button:hover {
    background: rgba(6, 182, 212, 0.2);
    border-color: rgba(6, 182, 212, 0.4);
    box-shadow: 0 4px 16px rgba(6, 182, 212, 0.2);
}

/* Icon Buttons */
.pg-icon-button {
    background: transparent;
    min-width: 38px;
    min-height: 38px;
    padding: 0;
    border-radius: 10px;
    color: #A78BFA;
    border: 1px solid transparent;
    transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.pg-icon-button:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.3);
    color: #C4B5FD;
    box-shadow: 0 0 16px rgba(139, 92, 246, 0.2);
}

.pg-preferences-button {
    background: transparent;
    min-width: 38px;
    min-height: 38px;
    padding: 0;
    border-radius: 10px;
    color: #A78BFA;
    border: 1px solid transparent;
    transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

.pg-preferences-button:hover {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.3);
    color: #C4B5FD;
    box-shadow: 0 0 16px rgba(139, 92, 246, 0.2);
}

/* ─────────────────────────────────────────────────────────────────────────────
   EDITOR PANELS - Glassmorphism Cards
   ───────────────────────────────────────────────────────────────────────────── */
.pg-panel-title {
    color: #C4B5FD;
    font-size: 10px;
    letter-spacing: 0.12em;
    font-weight: 700;
    text-transform: uppercase;
}

.pg-editor-shell {
    background: linear-gradient(145deg, rgba(30, 25, 55, 0.8) 0%, rgba(20, 15, 40, 0.9) 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 16px;
    transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.pg-output-editor {
    background: linear-gradient(145deg, rgba(6, 78, 97, 0.15) 0%, rgba(20, 15, 40, 0.9) 100%);
    border-color: rgba(6, 182, 212, 0.2);
}

.pg-editor-shell.focused {
    border-color: rgba(139, 92, 246, 0.5);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15), 0 8px 32px rgba(139, 92, 246, 0.2);
}

.pg-output-editor.focused {
    border-color: rgba(6, 182, 212, 0.5);
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15), 0 8px 32px rgba(6, 182, 212, 0.2);
}

.pg-output-editor.has-content {
    border-color: rgba(6, 182, 212, 0.4);
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.1);
}

.pg-editor-header {
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.1) 0%, transparent 100%);
    border-bottom: 1px solid rgba(139, 92, 246, 0.15);
    border-top-left-radius: 15px;
    border-top-right-radius: 15px;
    padding: 10px 14px;
}

.pg-output-editor .pg-editor-header {
    background: linear-gradient(180deg, rgba(6, 182, 212, 0.1) 0%, transparent 100%);
    border-bottom: 1px solid rgba(6, 182, 212, 0.15);
}

.pg-editor-count {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 500;
}

/* ─────────────────────────────────────────────────────────────────────────────
   TEXT VIEWS
   ───────────────────────────────────────────────────────────────────────────── */
textview,
text {
    background: transparent;
    color: #E2E8F0;
    caret-color: #A855F7;
}

textview selection,
text selection {
    background: rgba(139, 92, 246, 0.3);
}

.pg-placeholder {
    color: #64748B;
    font-style: italic;
}

/* ─────────────────────────────────────────────────────────────────────────────
   STATUS BAR
   ───────────────────────────────────────────────────────────────────────────── */
.pg-statusbar {
    background: linear-gradient(180deg, rgba(15, 10, 31, 0.95) 0%, rgba(139, 92, 246, 0.1) 100%);
    border-top: 1px solid rgba(139, 92, 246, 0.2);
    min-height: 40px;
}

.pg-status-dot {
    font-size: 10px;
    transition: all 300ms ease;
}

.pg-status-dot.state-ready {
    color: #64748B;
}

.pg-status-dot.state-cleared {
    color: #64748B;
}

.pg-status-dot.state-redacted {
    color: #A855F7;
    text-shadow: 0 0 12px rgba(168, 85, 247, 0.8);
}

.pg-status-dot.state-copy {
    color: #06B6D4;
    text-shadow: 0 0 12px rgba(6, 182, 212, 0.8);
}

.pg-status-dot.state-restore {
    color: #10B981;
    text-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
}

.pg-status-dot.state-warning {
    color: #F59E0B;
    text-shadow: 0 0 12px rgba(245, 158, 11, 0.8);
}

.pg-status-dot.state-import {
    color: #8B5CF6;
    text-shadow: 0 0 12px rgba(139, 92, 246, 0.8);
}

.pg-status-dot.state-export {
    color: #06B6D4;
    text-shadow: 0 0 12px rgba(6, 182, 212, 0.8);
}

.pg-status-label {
    color: #CBD5E1;
    font-size: 12px;
    font-weight: 500;
}

/* ─────────────────────────────────────────────────────────────────────────────
   STATISTICS PANEL
   ───────────────────────────────────────────────────────────────────────────── */
.pg-stats-panel {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(6, 182, 212, 0.08) 100%);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
}

.pg-stats-title {
    color: #C4B5FD;
    font-size: 10px;
    letter-spacing: 0.1em;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.pg-stats-row {
    padding: 4px 0;
}

.pg-stats-label {
    color: #94A3B8;
    font-size: 12px;
}

.pg-stats-value {
    color: #E2E8F0;
    font-size: 12px;
    font-weight: 600;
}

.pg-stats-badge {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(168, 85, 247, 0.2) 100%);
    color: #E9D5FF;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid rgba(139, 92, 246, 0.3);
}

/* ─────────────────────────────────────────────────────────────────────────────
   DRAG & DROP OVERLAY
   ───────────────────────────────────────────────────────────────────────────── */
.pg-drop-overlay {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(6, 182, 212, 0.15) 100%);
    border: 3px dashed rgba(139, 92, 246, 0.5);
    border-radius: 16px;
}

.pg-drop-label {
    color: #C4B5FD;
    font-size: 16px;
    font-weight: 600;
}

/* ─────────────────────────────────────────────────────────────────────────────
   TOOLTIPS
   ───────────────────────────────────────────────────────────────────────────── */
tooltip {
    background: linear-gradient(135deg, rgba(30, 25, 55, 0.95) 0%, rgba(20, 15, 40, 0.98) 100%);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 8px;
    color: #E2E8F0;
    padding: 6px 10px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

/* ─────────────────────────────────────────────────────────────────────────────
   COPY BUTTON INLINE
   ───────────────────────────────────────────────────────────────────────────── */
.pg-copy-inline {
    background: transparent;
    min-width: 28px;
    min-height: 28px;
    padding: 0;
    border-radius: 6px;
    color: #64748B;
    border: none;
    transition: all 200ms ease;
}

.pg-copy-inline:hover {
    background: rgba(139, 92, 246, 0.15);
    color: #A78BFA;
}

.pg-copy-inline.copied {
    color: #10B981;
}

/* ─────────────────────────────────────────────────────────────────────────────
   SCROLLBARS
   ───────────────────────────────────────────────────────────────────────────── */
scrollbar {
    background: transparent;
}

scrollbar slider {
    background: rgba(139, 92, 246, 0.3);
    border-radius: 10px;
    min-width: 8px;
    min-height: 8px;
}

scrollbar slider:hover {
    background: rgba(139, 92, 246, 0.5);
}

scrollbar slider:active {
    background: rgba(168, 85, 247, 0.6);
}

/* ─────────────────────────────────────────────────────────────────────────────
   KEYBOARD SHORTCUT HINTS
   ───────────────────────────────────────────────────────────────────────────── */
.pg-shortcut-hint {
    color: #64748B;
    font-size: 10px;
    font-weight: 500;
    background: rgba(100, 116, 139, 0.15);
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 8px;
}
"""

CATEGORY_LABELS = OrderedDict(
    [
        ("names", "Names"),
        ("emails", "Emails"),
        ("phones", "Phone"),
        ("api_keys", "API Keys"),
        ("addresses", "Addresses"),
        ("custom", "Custom"),
    ]
)

STATUS_MAP = {
    "EMAIL": "emails",
    "PERSON": "names",
    "PHONE": "phone numbers",
    "OPENAI_KEY": "API keys",
    "GITHUB_TOKEN": "API keys",
    "AWS_ACCESS_KEY": "API keys",
    "GOOGLE_API_KEY": "API keys",
    "STRIPE_KEY": "API keys",
    "GENERIC_SECRET": "secrets",
    "ADDRESS": "addresses",
    "LOCATION": "locations",
    "IPV4": "IP addresses",
    "IPV6": "IP addresses",
    "DOB": "dates of birth",
    "CREDIT_CARD": "credit cards",
    "SSN": "national IDs",
    "NID": "national IDs",
    "CUSTOM": "custom items",
}


class PrivacyGuardWindow(Adw.ApplicationWindow):
    """Primary application window."""

    def __init__(self, app: Adw.Application, settings: AppSettings) -> None:
        super().__init__(application=app, title="PrivacyGuard")
        self.set_default_size(1180, 760)
        self.set_size_request(900, 600)

        self._app = app
        self._settings = settings
        self._redactor = Redactor(spacy_model=self._settings.spacy_model)
        self._last_result: RedactionResult | None = None
        self._preferences_window: PreferencesWindow | None = None
        self._tray_controller = TrayController(window=self, app=app)

        self._build_ui()
        self._apply_css()
        self._setup_keyboard_shortcuts()
        self._setup_drag_drop()
        self.connect("close-request", self._on_close_request)
        self._start_update_check_if_enabled()

    def _apply_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(WINDOW_CSS.encode("utf-8"))
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    @staticmethod
    def _build_button_content(icon_name: str, text: str) -> Gtk.Box:
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        label = Gtk.Label(label=text)
        content.append(icon)
        content.append(label)
        return content

    def _new_toolbar_button(
        self,
        label: str,
        icon_name: str,
        style_classes: list[str],
        handler,
    ) -> Gtk.Button:
        button = Gtk.Button()
        button.set_child(self._build_button_content(icon_name, label))
        for style in style_classes:
            button.add_css_class(style)
        button.connect("clicked", handler)
        return button

    @staticmethod
    def _attach_row_hover(row: Gtk.Box) -> None:
        controller = Gtk.EventControllerMotion()
        controller.connect("enter", lambda *_args: row.add_css_class("hover"))
        controller.connect("leave", lambda *_args: row.remove_css_class("hover"))
        row.add_controller(controller)

    @staticmethod
    def _bind_editor_focus(view: Gtk.TextView, shell: Gtk.Box) -> None:
        controller = Gtk.EventControllerFocus()
        controller.connect("enter", lambda *_args: shell.add_css_class("focused"))
        controller.connect("leave", lambda *_args: shell.remove_css_class("focused"))
        view.add_controller(controller)

    @staticmethod
    def _count_summary(text: str) -> str:
        words = len([token for token in text.split() if token.strip()])
        return f"{len(text)} chars  •  {words} words"

    def _on_input_buffer_changed(self, buffer: Gtk.TextBuffer) -> None:
        self._sync_placeholder(buffer)
        self._input_count_label.set_text(self._count_summary(self._read_buffer(buffer)))

    def _on_output_buffer_changed(self, buffer: Gtk.TextBuffer) -> None:
        self._output_count_label.set_text(self._count_summary(self._read_buffer(buffer)))
        self._mark_output_content_state()

    def _set_status(self, message: str, kind: str) -> None:
        for css_class in ("state-ready", "state-cleared", "state-redacted", "state-copy", "state-restore", "state-warning", "state-import", "state-export"):
            self._status_dot.remove_css_class(css_class)
        self._status_dot.add_css_class(f"state-{kind}")
        self._status_label.set_text(message)

    def _mark_output_content_state(self) -> None:
        text = self._read_buffer(self._output_buffer)
        if text.strip():
            self._output_editor_shell.add_css_class("has-content")
        else:
            self._output_editor_shell.remove_css_class("has-content")

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.add_css_class("pg-root")
        self.set_content(root)

        self._update_banner = UpdateBannerController()
        root.append(self._update_banner.widget)

        header = Adw.HeaderBar()
        header.add_css_class("pg-headerbar")

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_box.add_css_class("pg-header-title-box")
        title_icon = Gtk.Image.new_from_icon_name("security-high-symbolic")
        title_icon.set_pixel_size(14)
        title_label = Gtk.Label(label="PrivacyGuard")
        title_label.add_css_class("pg-header-title")
        title_box.append(title_icon)
        title_box.append(title_label)
        header.set_title_widget(title_box)
        root.append(header)

        redact_btn = self._new_toolbar_button(
            label="Redact",
            icon_name="security-high-symbolic",
            style_classes=["pg-toolbar-button", "pg-redact-button"],
            handler=self._on_redact,
        )
        redact_btn.set_tooltip_text("Redact sensitive data (Ctrl+R)")

        copy_btn = self._new_toolbar_button(
            label="Copy",
            icon_name="edit-copy-symbolic",
            style_classes=["pg-toolbar-button", "pg-secondary-button"],
            handler=self._on_copy_clean,
        )
        copy_btn.set_tooltip_text("Copy redacted text (Ctrl+Shift+C)")

        restore_btn = self._new_toolbar_button(
            label="Restore",
            icon_name="edit-undo-symbolic",
            style_classes=["pg-toolbar-button", "pg-secondary-button"],
            handler=self._on_restore,
        )
        restore_btn.set_tooltip_text("Restore original values (Ctrl+Shift+R)")

        clear_btn = self._new_toolbar_button(
            label="Clear",
            icon_name="user-trash-symbolic",
            style_classes=["pg-toolbar-button", "pg-secondary-button"],
            handler=self._on_clear,
        )
        clear_btn.set_tooltip_text("Clear all text (Ctrl+L)")

        # File operations
        open_btn = Gtk.Button()
        open_btn.set_child(Gtk.Image.new_from_icon_name("document-open-symbolic"))
        open_btn.add_css_class("pg-icon-button")
        open_btn.set_tooltip_text("Open file (Ctrl+O)")
        open_btn.connect("clicked", self._on_open_file)

        save_btn = Gtk.Button()
        save_btn.set_child(Gtk.Image.new_from_icon_name("document-save-symbolic"))
        save_btn.add_css_class("pg-icon-button")
        save_btn.set_tooltip_text("Save redacted output (Ctrl+S)")
        save_btn.connect("clicked", self._on_save_file)

        prefs_btn = Gtk.Button()
        prefs_btn.set_child(Gtk.Image.new_from_icon_name("preferences-system-symbolic"))
        prefs_btn.add_css_class("pg-preferences-button")
        prefs_btn.set_tooltip_text("Preferences")
        prefs_btn.connect("clicked", self._on_preferences)

        header.pack_start(redact_btn)
        header.pack_start(copy_btn)
        header.pack_start(restore_btn)
        header.pack_start(clear_btn)
        header.pack_end(prefs_btn)
        header.pack_end(save_btn)
        header.pack_end(open_btn)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        body.add_css_class("pg-body")
        body.set_hexpand(True)
        body.set_vexpand(True)
        root.append(body)

        sidebar_shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_shell.add_css_class("pg-sidebar-shell")
        sidebar_shell.set_size_request(220, -1)
        sidebar_shell.set_hexpand(False)
        sidebar_shell.set_vexpand(True)
        body.append(sidebar_shell)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sidebar.set_margin_top(16)
        sidebar.set_margin_bottom(16)
        sidebar.set_margin_start(16)
        sidebar.set_margin_end(16)
        sidebar_shell.append(sidebar)

        divider = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        body.append(divider)

        sidebar_title = Gtk.Label(label="🛡️ DETECTION CATEGORIES", xalign=0)
        sidebar_title.add_css_class("pg-section-heading")
        sidebar.append(sidebar_title)

        self._switches: dict[str, Gtk.Switch] = {}
        for key, label in CATEGORY_LABELS.items():
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_hexpand(True)
            row.add_css_class("pg-detection-row")
            self._attach_row_hover(row)
            
            # Add icon
            icon_label = Gtk.Label(label=CATEGORY_ICONS.get(key, "•"))
            icon_label.add_css_class("pg-detection-icon")
            row.append(icon_label)
            
            text = Gtk.Label(label=label, xalign=0)
            text.set_hexpand(True)
            text.add_css_class("pg-detection-label")
            toggle = Gtk.Switch(active=self._settings.enabled_categories.get(key, True))
            toggle.set_halign(Gtk.Align.END)
            self._switches[key] = toggle
            row.append(text)
            row.append(toggle)
            sidebar.append(row)

        # Statistics panel (collapsible)
        stats_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        stats_separator.set_margin_top(12)
        stats_separator.set_margin_bottom(8)
        sidebar.append(stats_separator)
        
        stats_title = Gtk.Label(label="📊 LAST REDACTION", xalign=0)
        stats_title.add_css_class("pg-section-heading")
        sidebar.append(stats_title)
        
        self._stats_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._stats_panel.add_css_class("pg-stats-panel")
        self._stats_panel.set_visible(False)
        
        self._stats_total_label = Gtk.Label(label="Total: 0 items", xalign=0)
        self._stats_total_label.add_css_class("pg-stats-value")
        self._stats_panel.append(self._stats_total_label)
        
        self._stats_details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self._stats_panel.append(self._stats_details_box)
        
        sidebar.append(self._stats_panel)
        
        # No stats placeholder
        self._stats_empty = Gtk.Label(label="No redactions yet", xalign=0)
        self._stats_empty.add_css_class("pg-stats-label")
        self._stats_empty.set_margin_top(4)
        sidebar.append(self._stats_empty)

        main_content = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        main_content.set_hexpand(True)
        main_content.set_vexpand(True)
        main_content.set_wide_handle(True)
        main_content.connect("map", self._set_equal_split)
        body.append(main_content)

        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        input_box.set_hexpand(True)
        input_box.set_vexpand(True)
        input_box.set_margin_top(12)
        input_box.set_margin_start(12)
        input_box.set_margin_end(12)
        input_box.set_margin_bottom(6)

        self._input_editor_shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._input_editor_shell.add_css_class("pg-editor-shell")

        input_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        input_header.add_css_class("pg-editor-header")
        input_title = Gtk.Label(label="📥 INPUT", xalign=0)
        input_title.add_css_class("pg-panel-title")
        input_title.set_hexpand(True)
        self._input_count_label = Gtk.Label(label="0 chars  •  0 words", xalign=1)
        self._input_count_label.add_css_class("pg-editor-count")
        
        # Quick copy button for input
        input_copy_btn = Gtk.Button()
        input_copy_btn.set_child(Gtk.Image.new_from_icon_name("edit-copy-symbolic"))
        input_copy_btn.add_css_class("pg-copy-inline")
        input_copy_btn.set_tooltip_text("Copy input text")
        input_copy_btn.connect("clicked", self._on_copy_input)
        
        input_header.append(input_title)
        input_header.append(self._input_count_label)
        input_header.append(input_copy_btn)
        self._input_editor_shell.append(input_header)

        input_overlay = Gtk.Overlay()
        self._input_view = Gtk.TextView()
        self._input_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._input_view.set_monospace(True)
        self._input_view.set_left_margin(12)
        self._input_view.set_right_margin(12)
        self._input_view.set_top_margin(12)
        self._input_view.set_bottom_margin(12)
        self._input_view.set_hexpand(True)
        self._input_view.set_vexpand(True)
        self._input_buffer = self._input_view.get_buffer()
        self._input_buffer.connect("changed", self._on_input_buffer_changed)

        self._placeholder = Gtk.Label(label="📝 Paste or drop your text here... (or press Ctrl+O to open a file)")
        self._placeholder.add_css_class("pg-placeholder")
        self._placeholder.set_halign(Gtk.Align.START)
        self._placeholder.set_valign(Gtk.Align.START)
        self._placeholder.set_margin_start(14)
        self._placeholder.set_margin_top(14)

        input_scroll = Gtk.ScrolledWindow()
        input_scroll.set_hexpand(True)
        input_scroll.set_vexpand(True)
        input_scroll.set_child(self._input_view)

        input_overlay.set_child(input_scroll)
        input_overlay.add_overlay(self._placeholder)
        input_overlay.set_hexpand(True)
        input_overlay.set_vexpand(True)
        self._input_editor_shell.append(input_overlay)
        self._bind_editor_focus(self._input_view, self._input_editor_shell)
        input_box.append(self._input_editor_shell)

        output_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        output_box.set_hexpand(True)
        output_box.set_vexpand(True)
        output_box.set_margin_top(6)
        output_box.set_margin_bottom(12)
        output_box.set_margin_start(12)
        output_box.set_margin_end(12)

        self._output_editor_shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._output_editor_shell.add_css_class("pg-editor-shell")
        self._output_editor_shell.add_css_class("pg-output-editor")

        output_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        output_header.add_css_class("pg-editor-header")
        output_title = Gtk.Label(label="📤 REDACTED OUTPUT", xalign=0)
        output_title.add_css_class("pg-panel-title")
        output_title.set_hexpand(True)
        self._output_count_label = Gtk.Label(label="0 chars  •  0 words", xalign=1)
        self._output_count_label.add_css_class("pg-editor-count")
        
        # Quick copy button for output
        output_copy_btn = Gtk.Button()
        output_copy_btn.set_child(Gtk.Image.new_from_icon_name("edit-copy-symbolic"))
        output_copy_btn.add_css_class("pg-copy-inline")
        output_copy_btn.set_tooltip_text("Copy redacted output")
        output_copy_btn.connect("clicked", self._on_copy_clean)
        
        output_header.append(output_title)
        output_header.append(self._output_count_label)
        output_header.append(output_copy_btn)
        self._output_editor_shell.append(output_header)

        self._output_view = Gtk.TextView()
        self._output_view.set_editable(False)
        self._output_view.set_cursor_visible(False)
        self._output_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._output_view.set_monospace(True)
        self._output_view.set_left_margin(12)
        self._output_view.set_right_margin(12)
        self._output_view.set_top_margin(12)
        self._output_view.set_bottom_margin(12)
        self._output_view.set_hexpand(True)
        self._output_view.set_vexpand(True)
        self._output_buffer = self._output_view.get_buffer()
        self._output_buffer.connect("changed", self._on_output_buffer_changed)
        self._redaction_tag = self._output_buffer.create_tag(
            "redaction-zone",
            background="#3B2066",
            foreground="#E9D5FF",
            weight=700,
        )

        output_scroll = Gtk.ScrolledWindow()
        output_scroll.set_hexpand(True)
        output_scroll.set_vexpand(True)
        output_scroll.set_child(self._output_view)
        self._output_editor_shell.append(output_scroll)
        self._bind_editor_focus(self._output_view, self._output_editor_shell)
        output_box.append(self._output_editor_shell)

        main_content.set_start_child(input_box)
        main_content.set_end_child(output_box)
        main_content.set_resize_start_child(True)
        main_content.set_resize_end_child(True)
        main_content.set_shrink_start_child(False)
        main_content.set_shrink_end_child(False)
        main_content.set_position(340)

        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        status_bar.add_css_class("pg-statusbar")
        status_bar.set_margin_start(0)
        status_bar.set_margin_end(0)
        status_bar.set_margin_bottom(0)
        status_bar.set_margin_top(0)
        status_bar.set_hexpand(True)

        self._status_dot = Gtk.Label(label="●")
        self._status_dot.add_css_class("pg-status-dot")
        self._status_dot.set_margin_start(12)
        self._status_dot.set_margin_end(8)
        self._status_dot.set_margin_top(8)
        self._status_dot.set_margin_bottom(8)
        status_bar.append(self._status_dot)

        self._status_label = Gtk.Label(label="", xalign=0)
        self._status_label.add_css_class("pg-status-label")
        self._status_label.set_margin_start(0)
        self._status_label.set_margin_end(12)
        self._status_label.set_margin_top(8)
        self._status_label.set_margin_bottom(8)
        self._status_label.set_hexpand(True)
        status_bar.append(self._status_label)
        root.append(status_bar)
        self._set_status("Ready", kind="ready")

    def _sync_placeholder(self, _buffer: Gtk.TextBuffer) -> None:
        start = self._input_buffer.get_start_iter()
        end = self._input_buffer.get_end_iter()
        text = self._input_buffer.get_text(start, end, True)
        self._placeholder.set_visible(not text.strip())

    def _active_category_map(self) -> dict[str, bool]:
        enabled = dict(self._settings.enabled_categories)
        for key, toggle in self._switches.items():
            enabled[key] = toggle.get_active()
        self._settings.enabled_categories = enabled
        return enabled

    def _set_output_with_highlights(self, result: RedactionResult) -> None:
        self._output_buffer.set_text(result.redacted_text)
        self._mark_output_content_state()
        self._output_buffer.remove_tag(
            self._redaction_tag,
            self._output_buffer.get_start_iter(),
            self._output_buffer.get_end_iter(),
        )
        for replacement in result.replacements:
            start = self._output_buffer.get_iter_at_offset(replacement.output_start)
            end = self._output_buffer.get_iter_at_offset(replacement.output_end)
            self._output_buffer.apply_tag(self._redaction_tag, start, end)

    @staticmethod
    def _read_buffer(buffer: Gtk.TextBuffer) -> str:
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        return buffer.get_text(start, end, True)

    def _build_status_text(self, result: RedactionResult) -> str:
        labels: dict[str, int] = {}
        for entity, count in result.counts_by_type.items():
            label = STATUS_MAP.get(entity, entity.lower())
            labels[label] = labels.get(label, 0) + count

        if not labels:
            return "No redactions found"

        parts = [f"{count} {label}" for label, count in sorted(labels.items())]
        return ", ".join(parts) + " redacted"

    def _on_redact(self, _button: Gtk.Button | None = None) -> None:
        input_text = self._read_buffer(self._input_buffer)
        if not input_text.strip():
            self._output_buffer.set_text("")
            self._mark_output_content_state()
            self._set_status("Input is empty", kind="warning")
            return

        self._redactor.spacy_model = self._settings.spacy_model
        result = self._redactor.redact(
            input_text,
            enabled_categories=self._active_category_map(),
            custom_regex=self._settings.custom_regex,
            custom_keywords=self._settings.custom_keywords,
        )
        self._last_result = result
        self._set_output_with_highlights(result)
        self._set_status(self._build_status_text(result), kind="redacted")
        self._update_stats_panel(result)
        save_settings(self._settings)

    def _on_copy_clean(self, _button: Gtk.Button | None = None) -> None:
        text = self._read_buffer(self._output_buffer)
        if not text.strip():
            return
        clipboard: Gdk.Clipboard = self.get_clipboard()
        clipboard.set(text)
        self._set_status("✓ Redacted text copied to clipboard", kind="copy")

    def _on_restore(self, _button: Gtk.Button | None = None) -> None:
        if self._last_result is None:
            self._set_status("Nothing to restore", kind="warning")
            return
        current_output = self._read_buffer(self._output_buffer)
        restored = self._last_result.restore_text(current_output)
        self._output_buffer.set_text(restored)
        self._mark_output_content_state()
        self._set_status("✓ Original values restored in output", kind="restore")

    def _on_clear(self, _button: Gtk.Button | None = None) -> None:
        self._input_buffer.set_text("")
        self._output_buffer.set_text("")
        self._mark_output_content_state()
        self._set_status("Cleared", kind="cleared")
        self._last_result = None
        self._clear_stats_panel()

    def _on_preferences(self, _button: Gtk.Button) -> None:
        if self._preferences_window is not None:
            self._preferences_window.present()
            return

        def _save(updated_settings: AppSettings) -> None:
            self._settings = updated_settings
            save_settings(self._settings)
            self._preferences_window = None

        pref = PreferencesWindow(parent=self, settings=self._settings, on_save=_save)
        pref.connect("close-request", self._on_preferences_closed)
        self._preferences_window = pref
        pref.present()

    def _on_preferences_closed(self, _window: Gtk.Window) -> bool:
        self._preferences_window = None
        return False

    def _start_update_check_if_enabled(self) -> None:
        if not self._settings.check_updates:
            return

        checker = UpdateChecker(repo=self._settings.github_repo)

        def _on_update(info):
            release = ReleaseInfo(
                version=info.version,
                html_url=info.html_url,
                body=info.body,
                assets=info.assets,
            )
            GLib.idle_add(self._present_update_banner, release)

        checker.check_in_background(on_update=_on_update, on_error=lambda _err: None)

    def _present_update_banner(self, release: ReleaseInfo) -> bool:
        self._update_banner.show_update(release)
        return False

    def present_main_window(self) -> None:
        self._tray_controller.show_window()

    def _on_close_request(self, _window: Gtk.Window) -> bool:
        return self._tray_controller.handle_close_request()

    def _set_equal_split(self, pane: Gtk.Paned) -> None:
        def _apply() -> bool:
            height = pane.get_height()
            if height > 0:
                pane.set_position(height // 2)
            return False

        GLib.idle_add(_apply)

    # ─────────────────────────────────────────────────────────────────────────
    # Keyboard Shortcuts
    # ─────────────────────────────────────────────────────────────────────────
    def _setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts for common actions."""
        controller = Gtk.ShortcutController()
        controller.set_scope(Gtk.ShortcutScope.MANAGED)
        
        # Ctrl+R - Redact
        controller.add_shortcut(Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>r"),
            Gtk.CallbackAction.new(lambda *_: self._on_redact() or True)
        ))
        
        # Ctrl+Shift+C - Copy clean text
        controller.add_shortcut(Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control><Shift>c"),
            Gtk.CallbackAction.new(lambda *_: self._on_copy_clean() or True)
        ))
        
        # Ctrl+Shift+R - Restore
        controller.add_shortcut(Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control><Shift>r"),
            Gtk.CallbackAction.new(lambda *_: self._on_restore() or True)
        ))
        
        # Ctrl+L - Clear
        controller.add_shortcut(Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>l"),
            Gtk.CallbackAction.new(lambda *_: self._on_clear() or True)
        ))
        
        # Ctrl+O - Open file
        controller.add_shortcut(Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>o"),
            Gtk.CallbackAction.new(lambda *_: self._on_open_file() or True)
        ))
        
        # Ctrl+S - Save file
        controller.add_shortcut(Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string("<Control>s"),
            Gtk.CallbackAction.new(lambda *_: self._on_save_file() or True)
        ))
        
        self.add_controller(controller)

    # ─────────────────────────────────────────────────────────────────────────
    # Drag & Drop Support
    # ─────────────────────────────────────────────────────────────────────────
    def _setup_drag_drop(self) -> None:
        """Enable drag and drop of files into the input area."""
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_file_drop)
        self._input_view.add_controller(drop_target)

    def _on_file_drop(self, _target: Gtk.DropTarget, value: Gio.File, _x: float, _y: float) -> bool:
        """Handle dropped files."""
        if not isinstance(value, Gio.File):
            return False
        
        path = value.get_path()
        if path is None:
            return False
        
        try:
            file_path = Path(path)
            if file_path.suffix.lower() not in {".txt", ".md", ".log", ".json", ".xml", ".csv", ".yaml", ".yml", ""}:
                self._set_status(f"Unsupported file type: {file_path.suffix}", kind="warning")
                return False
            
            content = file_path.read_text(encoding="utf-8")
            self._input_buffer.set_text(content)
            self._set_status(f"📂 Loaded: {file_path.name}", kind="import")
            return True
        except Exception as e:
            self._set_status(f"Failed to read file: {e}", kind="warning")
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # File Import/Export
    # ─────────────────────────────────────────────────────────────────────────
    def _on_open_file(self, _button: Gtk.Button | None = None) -> None:
        """Open a file dialog to load text into the input."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Open Text File")
        
        # Set up file filters
        filters = Gio.ListStore.new(Gtk.FileFilter)
        
        text_filter = Gtk.FileFilter()
        text_filter.set_name("Text Files")
        text_filter.add_mime_type("text/plain")
        text_filter.add_pattern("*.txt")
        text_filter.add_pattern("*.md")
        text_filter.add_pattern("*.log")
        filters.append(text_filter)
        
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        filters.append(all_filter)
        
        dialog.set_filters(filters)
        dialog.open(self, None, self._on_open_file_response)

    def _on_open_file_response(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        """Handle the file open dialog response."""
        try:
            file = dialog.open_finish(result)
            if file is None:
                return
            
            path = file.get_path()
            if path is None:
                return
            
            file_path = Path(path)
            content = file_path.read_text(encoding="utf-8")
            self._input_buffer.set_text(content)
            self._set_status(f"📂 Loaded: {file_path.name} ({len(content)} chars)", kind="import")
        except GLib.Error:
            pass  # User cancelled
        except Exception as e:
            self._set_status(f"Failed to open file: {e}", kind="warning")

    def _on_save_file(self, _button: Gtk.Button | None = None) -> None:
        """Open a file dialog to save the redacted output."""
        output_text = self._read_buffer(self._output_buffer)
        if not output_text.strip():
            self._set_status("Nothing to save - output is empty", kind="warning")
            return
        
        dialog = Gtk.FileDialog()
        dialog.set_title("Save Redacted Output")
        dialog.set_initial_name("redacted_output.txt")
        dialog.save(self, None, self._on_save_file_response)

    def _on_save_file_response(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        """Handle the file save dialog response."""
        try:
            file = dialog.save_finish(result)
            if file is None:
                return
            
            path = file.get_path()
            if path is None:
                return
            
            output_text = self._read_buffer(self._output_buffer)
            file_path = Path(path)
            file_path.write_text(output_text, encoding="utf-8")
            self._set_status(f"💾 Saved: {file_path.name}", kind="export")
        except GLib.Error:
            pass  # User cancelled
        except Exception as e:
            self._set_status(f"Failed to save file: {e}", kind="warning")

    # ─────────────────────────────────────────────────────────────────────────
    # Copy Input
    # ─────────────────────────────────────────────────────────────────────────
    def _on_copy_input(self, _button: Gtk.Button) -> None:
        """Copy the input text to clipboard."""
        text = self._read_buffer(self._input_buffer)
        if not text.strip():
            return
        clipboard: Gdk.Clipboard = self.get_clipboard()
        clipboard.set(text)
        self._set_status("✓ Input text copied to clipboard", kind="copy")

    # ─────────────────────────────────────────────────────────────────────────
    # Statistics Panel
    # ─────────────────────────────────────────────────────────────────────────
    def _update_stats_panel(self, result: RedactionResult) -> None:
        """Update the statistics panel with redaction results."""
        # Clear existing stats
        while True:
            child = self._stats_details_box.get_first_child()
            if child is None:
                break
            self._stats_details_box.remove(child)
        
        total = sum(result.counts_by_type.values())
        if total == 0:
            self._stats_panel.set_visible(False)
            self._stats_empty.set_text("No sensitive data found")
            self._stats_empty.set_visible(True)
            return
        
        self._stats_empty.set_visible(False)
        self._stats_panel.set_visible(True)
        self._stats_total_label.set_text(f"🔒 Total: {total} item{'s' if total != 1 else ''} redacted")
        
        # Add breakdown by type
        for entity_type, count in sorted(result.counts_by_type.items()):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.add_css_class("pg-stats-row")
            
            label_text = STATUS_MAP.get(entity_type, entity_type.lower())
            label = Gtk.Label(label=f"  • {label_text.capitalize()}", xalign=0)
            label.add_css_class("pg-stats-label")
            label.set_hexpand(True)
            
            badge = Gtk.Label(label=str(count))
            badge.add_css_class("pg-stats-badge")
            
            row.append(label)
            row.append(badge)
            self._stats_details_box.append(row)

    def _clear_stats_panel(self) -> None:
        """Clear the statistics panel."""
        self._stats_panel.set_visible(False)
        self._stats_empty.set_text("No redactions yet")
        self._stats_empty.set_visible(True)
        
        while True:
            child = self._stats_details_box.get_first_child()
            if child is None:
                break
            self._stats_details_box.remove(child)
