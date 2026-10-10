"""Popup utilities for Svitlo CLI application."""

from rich.style import Style
from rich.text import Text

from core.themes import DEFAULT_THEME, colors_for


def make_button_label(text: str, colors: dict[str, str] | None = None) -> Text:
    """Create button label [ text ] with bright brackets and dim text"""
    palette = colors or colors_for(DEFAULT_THEME)
    full_text = f"[ {text} ]"
    text_obj = Text(full_text)
    text_obj.stylize(Style(color=palette['text']), 0, 1)
    text_obj.stylize(Style(color=palette['text_dim']), 1, len(full_text) - 1)
    text_obj.stylize(Style(color=palette['text']), len(full_text) - 1, len(full_text))
    return text_obj
