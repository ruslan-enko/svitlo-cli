"""Configuration and constants for Svitlo CLI application"""

__version__ = "0.44"

import os

# Application info
APP_NAME = "Svitlo CLI"
APP_VERSION = "0.44"

# Preferences file path
PREFERENCES_FILE = os.path.expanduser("~/.config/svitlo-cli/preferences.json")

# First run messages
FIRST_RUN_TITLE = "Ласкаво просимо до Svitlo CLI"
FIRST_RUN_MESSAGE = "Оберіть вашу групу для моніторингу графіку відключень:"

# Color scheme
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

# UI settings
UPDATE_INTERVAL = 1  # seconds (timer only)
DATA_REFRESH_INTERVAL = 600  # seconds (10 minutes)
NOTIFICATION_DURATION = 10  # seconds
NOTIFICATION_THRESHOLD = 30  # minutes before status change

# Available groups
AVAILABLE_GROUPS = [
    "1.1", "1.2", "2.1", "2.2", "3.1", "3.2", 
    "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"
]

# Default settings
DEFAULT_GROUP = "6.1"

# Status texts
STATUS_TEXTS = {
    'light_on': 'Світло є',
    'light_off': 'Світла немає',
    'loading': 'Завантаження...',
    'updating': 'Оновлення...',
    'no_more_changes': '✓ Сьогодні більше змін немає'
}

# Notification messages
NOTIFICATIONS = {
    'no_light_now': '□ УВАГА: ЗАРАЗ НЕМАЄ СВІТЛА!',
    'light_coming_soon': '[■] СВІТЛО З\'ЯВИТЬСЯ ЧЕРЕЗ {} ХВИЛИН!',
    'light_going_soon': '[□] СВІТЛО ВИМКНЕТЬСЯ ЧЕРЕЗ {} ХВИЛИН!',
    'next_on': '[■] Світло з\'явиться о {}',
    'next_off': '[□] Відключення о {}',
    'time_to_on': 'Наступне ВВІМКНЕННЯ через: {} год {}хв {}сек',
    'time_to_off': 'Наступне ВИМКНЕННЯ через: {} год {}хв {}сек'
}

# Additional configuration for better maintainability
UI_SETTINGS = {
    'update_interval': 1,
    'notification_duration': 10,
    'notification_threshold': 30,
    'loading_timeout': 30,
    'theme_colors': {
        'primary': '#D96800',
        'success': '#00a853',
        'error': '#ff4444',
        'warning': '#ff9800',
        'info': '#D96800'
    }
}

# Responsive layout breakpoints
BREAKPOINT_TINY = 60
BREAKPOINT_SMALL = 80
BREAKPOINT_MEDIUM = 120
BREAKPOINT_LARGE = 160

MIN_TERMINAL_WIDTH = BREAKPOINT_TINY
MIN_TERMINAL_HEIGHT = 18

LAYOUT_CONFIGS = {
    'tiny': {
        'logo_rows': 1,
        'timeline_columns': 1,
        'popup_columns': 1,
        'button_min_width': 16,
        'show_legend': False,
        'timeline_compressed': True,
        'button_text': '[{group}]',
    },
    'small': {
        'logo_rows': 2,
        'timeline_columns': 1,
        'popup_columns': 2,
        'button_min_width': 18,
        'show_legend': False,
        'timeline_compressed': True,
        'button_text': '[{group}]',
    },
    'medium': {
        'logo_rows': 4,
        'timeline_columns': 2,
        'popup_columns': 2,
        'button_min_width': 20,
        'show_legend': True,
        'timeline_compressed': False,
        'button_text': '[ Гр. {group} ]',
    },
    'large': {
        'logo_rows': 4,
        'timeline_columns': 3,
        'popup_columns': 3,
        'button_min_width': 24,
        'show_legend': True,
        'timeline_compressed': False,
        'button_text': '[ Гр. {group} ]',
    }
}

TERMINAL_SIZE_WARNING = (
    "⚠️ Вікно занадто мале для повного відображення.\n"
    "Рекомендований мінімальний розмір: {min_width}x{min_height}\n"
    "Поточний розмір: {current_width}x{current_height}\n"
    "Деякий контент може бути приховано."
)