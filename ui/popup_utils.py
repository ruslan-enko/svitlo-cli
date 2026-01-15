"""Popup utilities for Svitlo CLI application"""

__version__ = "0.44"

from rich.text import Text
from rich.style import Style


def make_button_label(text: str) -> Text:
    """Create button label [ text ] with white [] and gray text
    
    Args:
        text: Button text (e.g., "Група 6.1", "Назад")
    
    Returns:
        Text object with formatted label
    """
    full_text = f"[ {text} ]"
    text_obj = Text(full_text)
    text_obj.stylize(Style(color="#ffffff"), 0, 1)           # [
    text_obj.stylize(Style(color="#888888"), 1, -1)          # text
    text_obj.stylize(Style(color="#ffffff"), -1)             # ]
    return text_obj
