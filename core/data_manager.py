"""Data management for Svitlo CLI - handles persistent storage of parsed results"""

import json
import logging
import os

from core.config import DATA_FILE, PREFERENCES_DIR

logger = logging.getLogger(__name__)

def save_last_data(data: dict) -> bool:
    """Save the latest parsed data to a file"""
    try:
        os.makedirs(PREFERENCES_DIR, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except (OSError, TypeError, ValueError):
        logger.exception("Failed to save data to %s", DATA_FILE)
        return False
    return True

def load_last_data() -> dict | None:
    """Load the last saved data from file"""
    try:
        if not os.path.exists(DATA_FILE):
            return None
        with open(DATA_FILE, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to load data from %s", DATA_FILE)
        return None
