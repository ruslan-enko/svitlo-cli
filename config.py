"""Configuration and constants for Svitlo CLI application"""

# Application info
APP_NAME = "Svitlo CLI"
APP_VERSION = "1.0.0"

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