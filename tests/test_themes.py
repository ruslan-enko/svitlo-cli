import asyncio
import re
from pathlib import Path

from textual.color import Color

import core.preferences as preferences
import core.ui_manager as ui_manager_module
import main as main_module
from core.themes import AVAILABLE_THEMES, DEFAULT_THEME, THEMES, colors_for, next_theme

CSS_TOKEN_RE = re.compile(r"\$(\w+)")


def _isolate_prefs(tmp_path, monkeypatch):
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(tmp_path / "preferences.json"))


def test_every_theme_defines_the_same_tokens():
    expected = set(THEMES[DEFAULT_THEME])

    for name, colors in THEMES.items():
        assert set(colors) == expected, f"theme {name} has mismatched tokens"


def test_colors_for_falls_back_to_default():
    assert colors_for("nord") == THEMES["nord"]
    assert colors_for("does-not-exist") == THEMES[DEFAULT_THEME]
    assert colors_for(None) == THEMES[DEFAULT_THEME]


def test_next_theme_wraps_around():
    assert next_theme(None) == "nord"
    assert next_theme("nord") == "catppuccin"
    assert next_theme(AVAILABLE_THEMES[-1]) == AVAILABLE_THEMES[0]


def test_stylesheet_only_uses_defined_tokens():
    stylesheet = Path(main_module.__file__).parent / "styles.css"
    used = set(CSS_TOKEN_RE.findall(stylesheet.read_text(encoding="utf-8")))

    assert used, "expected the stylesheet to use theme tokens"
    for theme, colors in THEMES.items():
        undefined = used - set(colors)
        assert not undefined, f"theme {theme} does not define {sorted(undefined)}"


def test_app_starts_and_switches_through_every_theme(tmp_path, monkeypatch):
    """Boot the real app headless so unresolved CSS variables would surface."""
    _isolate_prefs(tmp_path, monkeypatch)
    monkeypatch.setattr(main_module, "is_first_run", lambda: False)
    monkeypatch.setattr(main_module, "get_saved_group", lambda: "6.1")
    monkeypatch.setattr(main_module, "get_theme", lambda: DEFAULT_THEME)
    # No network and no real OS notifications during the test.
    monkeypatch.setattr(main_module.SvitloApp, "_load_schedule", _noop_load_schedule)
    monkeypatch.setattr(ui_manager_module, "desktop_notifications_enabled", lambda: False)

    app = main_module.SvitloApp()

    async def exercise():
        async with app.run_test() as pilot:
            for theme in AVAILABLE_THEMES:
                app.set_theme(theme)
                await pilot.pause()
                assert app.theme_name == theme
                assert app.theme_colors == THEMES[theme]
                # The stylesheet has really been re-parsed with the new colours.
                assert app.screen.styles.background == Color.parse(THEMES[theme]['bg'])

            app.set_theme("not-a-theme")
            assert app.theme_name == AVAILABLE_THEMES[-1]

    asyncio.run(exercise())


def test_theme_choice_is_persisted(tmp_path, monkeypatch):
    _isolate_prefs(tmp_path, monkeypatch)

    preferences.save_preferences("6.1", theme="nord")

    assert preferences.get_theme() == "nord"


async def _noop_load_schedule(self) -> None:
    """Replacement for the network fetch during tests."""
