import json

import core.preferences as preferences
from core.config import DEFAULT_GROUP


def _use_tmp_prefs(tmp_path, monkeypatch):
    """Point the preferences module at a throwaway directory."""
    prefs_file = tmp_path / "preferences.json"
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(prefs_file))
    return prefs_file


def test_load_preferences_returns_defaults_for_missing_file(tmp_path, monkeypatch):
    _use_tmp_prefs(tmp_path, monkeypatch)

    loaded = preferences.load_preferences()

    assert loaded == {
        'group': DEFAULT_GROUP,
        'first_run': True,
        'favorites': [DEFAULT_GROUP],
        'theme': 'dark',
        'enable_desktop_notifications': True,
    }


def test_load_preferences_returns_defaults_for_invalid_json(tmp_path, monkeypatch):
    prefs_file = _use_tmp_prefs(tmp_path, monkeypatch)
    prefs_file.write_text("{invalid-json", encoding="utf-8")

    loaded = preferences.load_preferences()

    assert loaded['group'] == DEFAULT_GROUP
    assert loaded['first_run'] is True


def test_load_preferences_returns_defaults_for_non_object_root(tmp_path, monkeypatch):
    prefs_file = _use_tmp_prefs(tmp_path, monkeypatch)
    prefs_file.write_text("[1, 2, 3]", encoding="utf-8")

    loaded = preferences.load_preferences()

    assert loaded['group'] == DEFAULT_GROUP


def test_save_and_load_preferences_roundtrip(tmp_path, monkeypatch):
    _use_tmp_prefs(tmp_path, monkeypatch)

    preferences.save_preferences("4.2", is_first_run=False)

    loaded = preferences.load_preferences()
    assert loaded['group'] == "4.2"
    assert loaded['first_run'] is False
    assert loaded['favorites'] == ["4.2"]


def test_switching_group_keeps_theme_and_notification_flag(tmp_path, monkeypatch):
    """Regression: saving a group used to reset unrelated preferences."""
    _use_tmp_prefs(tmp_path, monkeypatch)

    preferences.save_preferences("4.2", theme="nord", enable_desktop_notifications=False)
    preferences.save_preferences("6.1")

    loaded = preferences.load_preferences()
    assert loaded['group'] == "6.1"
    assert loaded['theme'] == "nord"
    assert loaded['enable_desktop_notifications'] is False


def test_saved_favorites_are_replaced_not_appended(tmp_path, monkeypatch):
    _use_tmp_prefs(tmp_path, monkeypatch)

    preferences.save_preferences("4.2", favorites=["4.2", "6.1"])
    preferences.save_preferences("6.1", favorites=["6.1", "1.1"])

    assert preferences.get_favorites() == ["6.1", "1.1"]


def test_preferences_file_is_human_readable_unicode(tmp_path, monkeypatch):
    prefs_file = _use_tmp_prefs(tmp_path, monkeypatch)

    preferences.save_preferences("6.1")

    raw = json.loads(prefs_file.read_text(encoding="utf-8"))
    assert raw['group'] == "6.1"
    assert "6.1" in prefs_file.read_text(encoding="utf-8")


def test_desktop_notifications_enabled_reflects_stored_flag(tmp_path, monkeypatch):
    _use_tmp_prefs(tmp_path, monkeypatch)

    assert preferences.desktop_notifications_enabled() is True

    preferences.save_preferences("6.1", enable_desktop_notifications=False)

    assert preferences.desktop_notifications_enabled() is False


def test_get_favorites_falls_back_to_saved_group(tmp_path, monkeypatch):
    prefs_file = _use_tmp_prefs(tmp_path, monkeypatch)
    prefs_file.write_text(json.dumps({'group': '3.1', 'first_run': False}), encoding="utf-8")

    assert preferences.get_favorites() == ["3.1"]
