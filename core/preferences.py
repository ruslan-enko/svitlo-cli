"""User preferences management for Svitlo CLI"""

__version__ = "0.44"

import json
import os
from typing import Optional
from core.config import PREFERENCES_FILE

def save_preferences(group: str, is_first_run: bool = False) -> None:
    """Save user preferences to JSON file"""
    os.makedirs(os.path.dirname(PREFERENCES_FILE), exist_ok=True)
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
