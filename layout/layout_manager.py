"""Layout manager for responsive UI adaptation"""

from typing import Literal

LayoutType = Literal['tiny', 'small', 'medium', 'large']

BREAKPOINT_MEDIUM = 80
BREAKPOINT_LARGE = 120

LAYOUT_CONFIGS = {
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
        if terminal_width < BREAKPOINT_LARGE:
            return 'medium'
        else:
            return 'large'

    @staticmethod
    def get_config(layout_type: LayoutType) -> dict:
        """Return configuration for layout type"""
        return LAYOUT_CONFIGS.get(layout_type, LAYOUT_CONFIGS['medium'])
