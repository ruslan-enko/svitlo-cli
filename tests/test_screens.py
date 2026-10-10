import asyncio

from textual.color import Color
from textual.widgets import Static

import core.preferences as preferences
import core.ui_manager as ui_manager_module
import main as main_module
from core.themes import DEFAULT_THEME
from screens import (
    AddressLookupDialog,
    GroupSelectDialog,
    GroupSelectionScreen,
    HelpDialog,
    ThemeDialog,
)

DIALOGS = [GroupSelectionScreen, GroupSelectDialog, AddressLookupDialog, HelpDialog, ThemeDialog]
CONTAINER_CLASSES = [
    "modal-container",
    "dialog-container",
    "lookup-container",
    "help-container",
    "theme-container",
]


async def _noop_load_schedule(self) -> None:
    """Replacement for the network fetch during tests."""


def test_every_dialog_renders_with_themed_styles(tmp_path, monkeypatch):
    """Dialog styles moved from inline CSS into styles.css; check they still apply."""
    tmp_path_prefs = tmp_path / "preferences.json"
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(tmp_path_prefs))
    monkeypatch.setattr(main_module, "is_first_run", lambda: False)
    monkeypatch.setattr(main_module, "get_saved_group", lambda: "6.1")
    monkeypatch.setattr(main_module, "get_theme", lambda: "nord")
    monkeypatch.setattr(main_module.SvitloApp, "_load_schedule", _noop_load_schedule)
    monkeypatch.setattr(ui_manager_module, "desktop_notifications_enabled", lambda: False)

    app = main_module.SvitloApp()

    async def exercise():
        async with app.run_test() as pilot:
            for screen_type in DIALOGS:
                await app.push_screen(screen_type())
                await pilot.pause()

                expected_bg = Color.parse(app.theme_colors['bg'])
                expected_accent = Color.parse(app.theme_colors['accent'])

                containers = [
                    node
                    for class_name in CONTAINER_CLASSES
                    for node in app.screen.query(f".{class_name}")
                ]
                assert containers, f"{screen_type.__name__} has no themed container"

                for container in containers:
                    assert container.styles.background == expected_bg
                    border_style, border_color = container.styles.border_top
                    assert border_style == "solid"
                    assert border_color == expected_accent

                assert app.screen.query(Static)
                app.pop_screen()
                await pilot.pause()

    asyncio.run(exercise())


def test_dialogs_shrink_to_their_content(tmp_path, monkeypatch):
    """Row containers default to height 1fr, which used to stretch dialogs."""
    tmp_path_prefs = tmp_path / "preferences.json"
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(tmp_path_prefs))
    monkeypatch.setattr(main_module, "is_first_run", lambda: False)
    monkeypatch.setattr(main_module, "get_saved_group", lambda: "6.1")
    monkeypatch.setattr(main_module, "get_theme", lambda: DEFAULT_THEME)
    monkeypatch.setattr(main_module.SvitloApp, "_load_schedule", _noop_load_schedule)
    monkeypatch.setattr(ui_manager_module, "desktop_notifications_enabled", lambda: False)

    app = main_module.SvitloApp()

    async def exercise():
        async with app.run_test(size=(90, 26)) as pilot:
            screen_height = app.screen.size.height

            for screen_type in DIALOGS:
                await app.push_screen(screen_type())
                await pilot.pause()

                for row_class in ("dialog-back-container", "modal-back-container", "lookup-actions"):
                    for row in app.screen.query(f".{row_class}"):
                        assert row.size.height <= 2, f"{screen_type.__name__} {row_class} is not content sized"

                for class_name in CONTAINER_CLASSES:
                    for container in app.screen.query(f".{class_name}"):
                        assert container.size.height < screen_height

                app.pop_screen()
                await pilot.pause()

    asyncio.run(exercise())


def test_dialogs_do_not_span_the_whole_width(tmp_path, monkeypatch):
    """The group dialogs used to stretch to the full terminal width."""
    tmp_path_prefs = tmp_path / "preferences.json"
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(tmp_path_prefs))
    monkeypatch.setattr(main_module, "is_first_run", lambda: False)
    monkeypatch.setattr(main_module, "get_saved_group", lambda: "6.1")
    monkeypatch.setattr(main_module, "get_theme", lambda: DEFAULT_THEME)
    monkeypatch.setattr(main_module.SvitloApp, "_load_schedule", _noop_load_schedule)
    monkeypatch.setattr(ui_manager_module, "desktop_notifications_enabled", lambda: False)

    app = main_module.SvitloApp()

    async def exercise():
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            screen_width = app.screen.size.width

            for screen_type in (GroupSelectDialog, GroupSelectionScreen):
                await app.push_screen(screen_type())
                await pilot.pause()

                width = app.screen.query_one(".dialog-container, .modal-container").size.width
                assert width < screen_width / 2, f"{screen_type.__name__} is {width} of {screen_width}"

                app.pop_screen()
                await pilot.pause()

    asyncio.run(exercise())
