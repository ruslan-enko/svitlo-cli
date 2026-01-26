"""Layout manager for responsive UI adaptation"""

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
