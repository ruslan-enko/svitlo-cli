"""Layout manager for responsive UI adaptation"""

__version__ = "0.44"

from typing import Literal

LayoutType = Literal['tiny', 'small', 'medium', 'large']

BREAKPOINT_TINY = 60
BREAKPOINT_SMALL = 80
BREAKPOINT_MEDIUM = 120
BREAKPOINT_LARGE = 160

LAYOUT_CONFIGS = {
    'tiny': {
        'logo_rows': 1,
        'timeline_columns': 1,
        'popup_columns': 1,
        'show_legend': False,
        'timeline_compressed': True,
        'button_text': '[{group}]',
    },
    'small': {
        'logo_rows': 2,
        'timeline_columns': 1,
        'popup_columns': 2,
        'show_legend': False,
        'timeline_compressed': True,
        'button_text': '[{group}]',
    },
    'medium': {
        'logo_rows': 4,
        'timeline_columns': 2,
        'popup_columns': 2,
        'show_legend': True,
        'timeline_compressed': False,
        'button_text': '[{group}]',
    },
    'large': {
        'logo_rows': 4,
        'timeline_columns': 3,
        'popup_columns': 3,
        'show_legend': True,
        'timeline_compressed': False,
        'button_text': '[{group}]',
    }
}

TERMINAL_SIZE_WARNING = (
    "⚠️ Вікно занадто мале для повного відображення.\n"
    "Рекомендований мінімальний розмір: {min_width}x{min_height}\n"
    "Поточний розмір: {current_width}x{current_height}\n"
    "Деякий контент може бути приховано."
)

MIN_TERMINAL_WIDTH = BREAKPOINT_TINY
MIN_TERMINAL_HEIGHT = 18


class LayoutManager:
    """Centralized responsive layout management"""

    @staticmethod
    def get_layout_type(terminal_width: int, terminal_height: int) -> LayoutType:
        """Determine layout type based on terminal size"""
        if terminal_width < BREAKPOINT_SMALL:
            return 'tiny' if terminal_width < BREAKPOINT_TINY else 'small'
        elif terminal_width < BREAKPOINT_MEDIUM:
            return 'medium'
        else:
            return 'large'

    @staticmethod
    def get_config(layout_type: LayoutType) -> dict:
        """Return configuration for layout type"""
        return LAYOUT_CONFIGS[layout_type]

    @staticmethod
    def calculate_grid_columns(terminal_width: int, item_count: int = 12) -> int:
        """Calculate optimal columns for grid"""
        layout = LayoutManager.get_layout_type(terminal_width, 24)
        config = LayoutManager.get_config(layout)
        cols = min(config['popup_columns'], item_count)
        return max(1, cols)

    @staticmethod
    def get_button_text(layout_type: LayoutType) -> str:
        """Return button text format for layout type"""
        return LAYOUT_CONFIGS[layout_type]['button_text']

    @staticmethod
    def should_show_warning(terminal_width: int, terminal_height: int) -> bool:
        """Whether to show terminal size warning"""
        return terminal_width < BREAKPOINT_TINY

    @staticmethod
    def get_logo_rows(layout_type: LayoutType) -> int:
        """Return number of rows for ASCII logo"""
        return LAYOUT_CONFIGS[layout_type]['logo_rows']

    @staticmethod
    def get_timeline_columns(layout_type: LayoutType) -> int:
        """Return number of columns for timeline"""
        return LAYOUT_CONFIGS[layout_type]['timeline_columns']

    @staticmethod
    def format_warning(min_width: int, min_height: int, current_width: int, current_height: int) -> str:
        """Format terminal size warning message"""
        return TERMINAL_SIZE_WARNING.format(
            min_width=min_width,
            min_height=min_height,
            current_width=current_width,
            current_height=current_height
        )
