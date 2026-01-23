"""User preferences management for Svitlo CLI"""

import json
import os
from typing import Optional
from core.config import PREFERENCES_DIR, PREFERENCES_FILE


def save_preferences(group: str, is_first_run: bool = False) -> None:
    """Save user preferences to JSON file"""
    os.makedirs(PREFERENCES_DIR, exist_ok=True)
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump({'group': group, 'first_run': is_first_run}, f)


def load_preferences() -> dict:
    """Load user preferences from JSON file"""
    try:
        with open(PREFERENCES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'group': None, 'first_run': True}


def is_first_run() -> bool:
    """Check if this is first launch"""
    prefs = load_preferences()
    return prefs.get('first_run', True)


def get_saved_group() -> Optional[str]:
    """Get previously saved group"""
    prefs = load_preferences()
    return prefs.get('group', None)


def save_last_update_check(timestamp: str) -> None:
    """Save the timestamp of the last update check"""
    prefs = load_preferences()
    prefs['last_update_check'] = timestamp
    os.makedirs(PREFERENCES_DIR, exist_ok=True)
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump(prefs, f)


def get_last_update_check() -> Optional[str]:
    """Get the timestamp of the last update check"""
    prefs = load_preferences()
    return prefs.get('last_update_check', None)


def save_latest_version(version_str: str) -> None:
    """Save the latest version found from GitHub"""
    prefs = load_preferences()
    prefs['latest_version'] = version_str
    os.makedirs(PREFERENCES_DIR, exist_ok=True)
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump(prefs, f)


def get_latest_version() -> Optional[str]:
    """Get the cached latest version from GitHub"""
    prefs = load_preferences()
    return prefs.get('latest_version', None)
