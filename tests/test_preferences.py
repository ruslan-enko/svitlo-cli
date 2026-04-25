import core.preferences as preferences


def test_load_preferences_returns_default_for_missing_file(tmp_path, monkeypatch) -> None:
    prefs_file = tmp_path / "preferences.json"
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(prefs_file))

    loaded = preferences.load_preferences()

    assert loaded == {"group": None, "first_run": True}


def test_save_and_load_preferences_roundtrip(tmp_path, monkeypatch) -> None:
    prefs_file = tmp_path / "preferences.json"
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(prefs_file))

    preferences.save_preferences("4.2", is_first_run=False)
    loaded = preferences.load_preferences()

    assert loaded == {"group": "4.2", "first_run": False}


def test_load_preferences_returns_default_for_invalid_json(tmp_path, monkeypatch) -> None:
    prefs_file = tmp_path / "preferences.json"
    prefs_file.write_text("{invalid-json", encoding="utf-8")
    monkeypatch.setattr(preferences, "PREFERENCES_DIR", str(tmp_path))
    monkeypatch.setattr(preferences, "PREFERENCES_FILE", str(prefs_file))

    loaded = preferences.load_preferences()

    assert loaded == {"group": None, "first_run": True}
