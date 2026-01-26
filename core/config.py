"""Configuration and constants for Svitlo CLI application"""

import os

APP_NAME = "Svitlo CLI"
APP_VERSION = "1.0.0"

# File paths
PREFERENCES_DIR = os.path.expanduser("~/.config/svitlo-cli")
PREFERENCES_FILE = os.path.join(PREFERENCES_DIR, "preferences.json")
DATA_FILE = os.path.join(PREFERENCES_DIR, "last_data.json")

# Available groups
AVAILABLE_GROUPS = [
    "1.1", "1.2", "2.1", "2.2", "3.1", "3.2",
    "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"
]
DEFAULT_GROUP = "6.1"

# Ukrainian month names
MONTHS_UA = [
    'Січня', 'Лютого', 'Березня', 'Квітня', 'Травня', 'Червня',
    'Липня', 'Серпня', 'Вересня', 'Жовтня', 'Листопада', 'Грудня'
]

# Button ID prefixes (for consistent UI element naming)
BTN_PREFIX_GROUP = "btn-group-"
BTN_PREFIX_MODAL = "btn-modal-"
BTN_PREFIX_ACTION = "btn-action-"
BTN_ID_REFRESH = "action-refresh"
BTN_ID_QUIT = "action-quit"
BTN_ID_GROUP_SELECT = "btn-group-select"

# Timeline settings
TIMELINE_INTERVALS_PER_HOUR = 2
TIMELINE_TOTAL_HOURS = 24

# Time thresholds
UPDATE_INTERVAL = 1
DATA_REFRESH_INTERVAL = 600
TIME_THRESHOLD_HOURS = 1
TIME_THRESHOLD_MINUTES = 30
NOTIFICATION_DURATION = 10
NOTIFICATION_THRESHOLD = 30

# Status texts
STATUS_LIGHT_ON = "Світло є"
STATUS_LIGHT_OFF = "Світла немає"
STATUS_LOADING = "Завантаження..."
STATUS_UPDATING = "Оновлення..."
STATUS_NO_MORE_CHANGES = "✓ Сьогодні більше змін немає"
STATUS_ALL_DAY = "✓ Світло буде цілий день"
STATUS_ALL_DAY_TOMORROW = "✓ Завтра світло буде цілий день"

STATUS_TEXTS = {
    'light_on': STATUS_LIGHT_ON,
    'light_off': STATUS_LIGHT_OFF,
    'loading': STATUS_LOADING,
    'updating': STATUS_UPDATING,
    'no_more_changes': STATUS_NO_MORE_CHANGES,
    'all_day': STATUS_ALL_DAY,
    'all_day_tomorrow': STATUS_ALL_DAY_TOMORROW
}

# Notifications
NOTIFICATIONS = {
    'no_light_now': '□ УВАГА: ЗАРАЗ НЕМАЄ СВІТЛА!',
    'light_coming_soon': '[■] СВІТЛО З\'ЯВИТЬСЯ ЧЕРЕЗ {} ХВИЛИН!',
    'light_going_soon': '[□] СВІТЛО ВИМКНЕТЬСЯ ЧЕРЕЗ {} ХВИЛИН!',
    'next_on': '[■] Світло з\'явиться о {}',
    'next_off': '[□] Відключення о {}',
    'time_to_on': 'Наступне ВВІМКНЕННЯ через: {} год {}хв {}сек',
    'time_to_off': 'Наступне ВИМКНЕННЯ через: {} год {}хв {}сек'
}

# First run
FIRST_RUN_TITLE = "Ласкаво просимо до Svitlo CLI"
FIRST_RUN_MESSAGE = "Оберіть вашу групу для моніторингу графіку відключень:"

# Colors
COLORS = {
    'background': '#1a1a1a',
    'primary': '#D96800',
    'success': '#00a853',
    'error': '#333333',
    'text': '#fff',
    'text_secondary': '#888',
    'text_muted': '#666',
    'border': '#2a2a2a',
    'border_light': '#222',
    'current': '#fff'
}