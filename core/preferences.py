"""User preferences management for Svitlo CLI."""

import json
import logging
import os
from typing import Any

from core.config import DEFAULT_GROUP, PREFERENCES_DIR, PREFERENCES_FILE
from core.themes import DEFAULT_THEME

logger = logging.getLogger(__name__)


def _default_preferences() -> dict[str, Any]:
    """Build the preferences payload used when none is stored yet."""
    return {
        'group': DEFAULT_GROUP,
        'first_run': True,
        'favorites': [DEFAULT_GROUP],
        'theme': DEFAULT_THEME,
        'enable_desktop_notifications': True
    }


def save_preferences(
    group: str,
    is_first_run: bool = False,
    favorites: list[str] | None = None,
    theme: str | None = None,
    enable_desktop_notifications: bool | None = None
) -> None:
    """Save user preferences to JSON file.

    Arguments left as ``None`` keep whatever is already stored, so switching a
    group does not reset the theme or the notification setting.
    """
    os.makedirs(PREFERENCES_DIR, exist_ok=True)
    prefs = load_preferences()
    was_first_run = bool(prefs.get('first_run', True))

    prefs['group'] = group
    prefs['first_run'] = is_first_run

    if theme is not None:
        prefs['theme'] = theme
    if enable_desktop_notifications is not None:
        prefs['enable_desktop_notifications'] = enable_desktop_notifications

    if favorites is not None:
        prefs['favorites'] = favorites
    elif was_first_run:
        # On the very first run the group the user picked becomes the first favorite.
        prefs['favorites'] = [group]

    with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)


def load_preferences() -> dict[str, Any]:
    """Load user preferences from JSON file."""
    try:
        with open(PREFERENCES_FILE, encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _default_preferences()

    if not isinstance(data, dict):
        logger.warning("Preferences file does not contain an object, using defaults")
        return _default_preferences()

    return data


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


def desktop_notifications_enabled() -> bool:
    """Check whether native desktop notifications are enabled."""
    return bool(load_preferences().get('enable_desktop_notifications', True))


def get_theme() -> str:
    """Get the stored colour theme, falling back to the default one."""
    theme = load_preferences().get('theme')
    return theme if isinstance(theme, str) and theme else DEFAULT_THEME
