"""Tests for app level actions that change stored state."""

import asyncio

import core.preferences as preferences
import core.ui_manager as ui_manager_module
import main as main_module
from core.themes import DEFAULT_THEME


async def _noop_load_schedule(self) -> None:
    """Replacement for the network fetch during tests."""


def test_toggle_notifications_action_flips_and_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(tmp_path / "preferences.json"))
    monkeypatch.setattr(main_module, "is_first_run", lambda: False)
    monkeypatch.setattr(main_module, "get_saved_group", lambda: "6.1")
    monkeypatch.setattr(main_module, "get_theme", lambda: DEFAULT_THEME)
    monkeypatch.setattr(main_module.SvitloApp, "_load_schedule", _noop_load_schedule)
    # Keep the confirmation message in the widget only, no real OS notification.
    monkeypatch.setattr(ui_manager_module, "desktop_notifications_enabled", lambda: False)

    app = main_module.SvitloApp()

    async def exercise():
        async with app.run_test() as pilot:
            assert preferences.desktop_notifications_enabled() is True

            app.action_toggle_notifications()
            await pilot.pause()
            assert preferences.desktop_notifications_enabled() is False

            app.action_toggle_notifications()
            await pilot.pause()
            assert preferences.desktop_notifications_enabled() is True

    asyncio.run(exercise())


def test_toggle_notifications_keeps_the_selected_group(tmp_path, monkeypatch):
    """Regression: saving the flag used to be able to reset unrelated settings."""
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(tmp_path / "preferences.json"))

    preferences.save_preferences("4.2", theme="catppuccin")
    preferences.save_preferences("4.2", enable_desktop_notifications=False)

    loaded = preferences.load_preferences()
    assert loaded['group'] == "4.2"
    assert loaded['theme'] == "catppuccin"
    assert loaded['enable_desktop_notifications'] is False
