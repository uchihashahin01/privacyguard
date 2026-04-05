"""Preferences editor for user-defined redaction settings."""

from __future__ import annotations

from typing import Callable

from gi.repository import Gdk, Gtk

from privacyguard.config.settings import AppSettings


PREFERENCES_CSS = """
.pref-window {
    background: linear-gradient(135deg, #0F0A1F 0%, #1A1033 50%, #0D1525 100%);
}

.pref-header {
    color: #C4B5FD;
    font-size: 10px;
    letter-spacing: 0.12em;
    font-weight: 700;
    text-transform: uppercase;
    margin-top: 16px;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.pref-label {
    color: #E2E8F0;
    font-size: 13px;
}

.pref-entry {
    background: rgba(30, 25, 55, 0.8);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 8px;
    color: #E2E8F0;
    padding: 8px 12px;
    min-height: 36px;
}

.pref-entry:focus {
    border-color: rgba(139, 92, 246, 0.5);
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
}

.pref-switch-row {
    background: rgba(139, 92, 246, 0.05);
    border: 1px solid rgba(139, 92, 246, 0.1);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 4px 0;
}

.pref-textview {
    background: rgba(30, 25, 55, 0.8);
    border: 1px solid rgba(139, 92, 246, 0.25);
    border-radius: 10px;
    color: #E2E8F0;
    padding: 8px;
}

.pref-textview:focus-within {
    border-color: rgba(139, 92, 246, 0.5);
    box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
}

.pref-btn-cancel {
    background: rgba(100, 116, 139, 0.2);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 10px;
    color: #CBD5E1;
    padding: 8px 20px;
    min-height: 38px;
}

.pref-btn-cancel:hover {
    background: rgba(100, 116, 139, 0.3);
    border-color: rgba(100, 116, 139, 0.5);
}

.pref-btn-save {
    background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 100%);
    border: none;
    border-radius: 10px;
    color: #FFFFFF;
    padding: 8px 20px;
    min-height: 38px;
    font-weight: 600;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
}

.pref-btn-save:hover {
    background: linear-gradient(135deg, #9D6FFF 0%, #B96CFF 100%);
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
}

textview text {
    background: transparent;
    color: #E2E8F0;
}
"""


class PreferencesWindow(Gtk.Window):
    """Settings window for custom patterns and app behavior."""

    def __init__(
        self,
        parent: Gtk.Window,
        settings: AppSettings,
        on_save: Callable[[AppSettings], None],
    ) -> None:
        super().__init__(title="⚙️ PrivacyGuard Preferences", transient_for=parent, modal=True)
        self.set_default_size(680, 580)
        self._settings = settings
        self._on_save = on_save

        self._apply_css()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.add_css_class("pref-window")
        root.set_margin_top(20)
        root.set_margin_bottom(20)
        root.set_margin_start(24)
        root.set_margin_end(24)
        self.set_child(root)

        # General section
        general_header = Gtk.Label(label="🔧 GENERAL SETTINGS", xalign=0)
        general_header.add_css_class("pref-header")
        root.append(general_header)

        repo_label = Gtk.Label(label="GitHub repository (owner/repo)", xalign=0)
        repo_label.add_css_class("pref-label")
        self._repo_entry = Gtk.Entry(text=self._settings.github_repo)
        self._repo_entry.add_css_class("pref-entry")
        root.append(repo_label)
        root.append(self._repo_entry)

        updates_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        updates_row.add_css_class("pref-switch-row")
        updates_label = Gtk.Label(label="Check for updates on startup", xalign=0)
        updates_label.add_css_class("pref-label")
        updates_label.set_hexpand(True)
        self._updates_switch = Gtk.Switch(active=self._settings.check_updates)
        updates_row.append(updates_label)
        updates_row.append(self._updates_switch)
        root.append(updates_row)

        model_label = Gtk.Label(label="spaCy model for NLP processing", xalign=0)
        model_label.add_css_class("pref-label")
        self._model_drop = Gtk.DropDown.new_from_strings(["en_core_web_sm (faster)", "en_core_web_trf (more accurate)"])
        self._model_drop.set_selected(1 if self._settings.spacy_model == "en_core_web_trf" else 0)
        root.append(model_label)
        root.append(self._model_drop)

        # Custom patterns section
        custom_header = Gtk.Label(label="📝 CUSTOM PATTERNS", xalign=0)
        custom_header.add_css_class("pref-header")
        root.append(custom_header)

        regex_label = Gtk.Label(label="Custom regex patterns (one per line)", xalign=0)
        regex_label.add_css_class("pref-label")
        self._regex_view = Gtk.TextView()
        self._regex_view.set_monospace(True)
        self._regex_view.set_vexpand(True)
        regex_buffer = self._regex_view.get_buffer()
        regex_buffer.set_text("\n".join(self._settings.custom_regex))

        regex_scroll = Gtk.ScrolledWindow()
        regex_scroll.set_min_content_height(100)
        regex_scroll.set_child(self._regex_view)
        regex_scroll.add_css_class("pref-textview")

        root.append(regex_label)
        root.append(regex_scroll)

        keywords_label = Gtk.Label(label="Custom keywords (one per line)", xalign=0)
        keywords_label.add_css_class("pref-label")
        self._keywords_view = Gtk.TextView()
        self._keywords_view.set_vexpand(True)
        keywords_buffer = self._keywords_view.get_buffer()
        keywords_buffer.set_text("\n".join(self._settings.custom_keywords))

        keywords_scroll = Gtk.ScrolledWindow()
        keywords_scroll.set_min_content_height(100)
        keywords_scroll.set_child(self._keywords_view)
        keywords_scroll.add_css_class("pref-textview")

        root.append(keywords_label)
        root.append(keywords_scroll)

        # Actions
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions.set_halign(Gtk.Align.END)
        actions.set_margin_top(12)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.add_css_class("pref-btn-cancel")
        
        save_button = Gtk.Button(label="💾 Save Settings")
        save_button.add_css_class("pref-btn-save")
        
        cancel_button.connect("clicked", lambda _btn: self.close())
        save_button.connect("clicked", self._handle_save)
        
        actions.append(cancel_button)
        actions.append(save_button)
        root.append(actions)

    def _apply_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(PREFERENCES_CSS.encode("utf-8"))
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    @staticmethod
    def _extract_lines(view: Gtk.TextView) -> list[str]:
        buffer = view.get_buffer()
        start = buffer.get_start_iter()
        end = buffer.get_end_iter()
        text = buffer.get_text(start, end, True)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _handle_save(self, _button: Gtk.Button) -> None:
        self._settings.github_repo = self._repo_entry.get_text().strip() or self._settings.github_repo
        self._settings.check_updates = self._updates_switch.get_active()
        self._settings.spacy_model = (
            "en_core_web_trf" if self._model_drop.get_selected() == 1 else "en_core_web_sm"
        )
        self._settings.custom_regex = self._extract_lines(self._regex_view)
        self._settings.custom_keywords = self._extract_lines(self._keywords_view)
        self._on_save(self._settings)
        self.close()
