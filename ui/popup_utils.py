"""Popup utilities for Svitlo CLI application"""

__version__ = "0.44"

from rich.style import Style
from rich.text import Text


def make_button_label(text: str) -> Text:
    """Create button label [ text ] with white [] and gray text"""
    full_text = f"[ {text} ]"
    text_obj = Text(full_text)
    text_obj.stylize(Style(color="#ffffff"), 0, 1)
    text_obj.stylize(Style(color="#888888"), 1, len(full_text) - 1)
    text_obj.stylize(Style(color="#ffffff"), len(full_text) - 1, len(full_text))
    return text_obj
