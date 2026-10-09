"""User preferences management for Svitlo CLI."""

import json
import os
from typing import Any

from core.config import DEFAULT_GROUP, DEFAULT_THEME, PREFERENCES_DIR, PREFERENCES_FILE


def save_preferences(
    group: str,
    is_first_run: bool = False,
    favorites: list[str] | None = None,
    theme: str = DEFAULT_THEME,
    enable_desktop_notifications: bool = True
) -> None:
    """Save user preferences to JSON file."""
    os.makedirs(PREFERENCES_DIR, exist_ok=True)
    prefs = load_preferences()
    
    prefs['group'] = group
    prefs['first_run'] = is_first_run
    prefs['theme'] = theme
    prefs['enable_desktop_notifications'] = enable_desktop_notifications

    if favorites is not None:
        prefs['favorites'] = favorites
    elif 'favorites' not in prefs:
        prefs['favorites'] = [group]

    with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)


def load_preferences() -> dict[str, Any]:
    """Load user preferences from JSON file."""
    try:
        with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Preferences root must be a dict")
            return data
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {
            'group': DEFAULT_GROUP,
            'first_run': True,
            'favorites': [DEFAULT_GROUP],
            'theme': DEFAULT_THEME,
            'enable_desktop_notifications': True
        }


def is_first_run() -> bool:
    """Check if this is first launch."""
    prefs = load_preferences()
    return prefs.get('first_run', True)


def get_saved_group() -> str | None:
    """Get previously saved group."""
    prefs = load_preferences()
    return prefs.get('group', DEFAULT_GROUP)


def get_favorites() -> list[str]:
    """Get list of favorite groups."""
    prefs = load_preferences()
    favs = prefs.get('favorites', [])
    if not favs:
        saved = prefs.get('group', DEFAULT_GROUP)
        return [saved] if saved else [DEFAULT_GROUP]
    return favs
