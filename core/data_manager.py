"""Data management for Svitlo CLI - handles persistent storage of parsed results"""

import json
import os
import logging
from typing import Dict, Optional
from core.config import DATA_FILE, PREFERENCES_DIR

logger = logging.getLogger(__name__)

def save_last_data(data: Dict) -> bool:
    """Save the latest parsed data to a file"""
    try:
        os.makedirs(PREFERENCES_DIR, exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save data to {DATA_FILE}: {e}")
        return False

def load_last_data() -> Optional[Dict]:
    """Load the last saved data from file"""
    try:
        if not os.path.exists(DATA_FILE):
            return None
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load data from {DATA_FILE}: {e}")
        return None
