"""Colour themes for Svitlo CLI.

Each theme is a flat mapping of token name to colour. Tokens are used in two
places: as Textual CSS variables (``$token`` in styles.css) and as Rich markup
colours for the timeline, which is rendered as plain text.
"""

DEFAULT_THEME = "dark"

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#1a1a1a",
        "accent": "#d96800",
        "text": "#ffffff",
        "text_dim": "#888888",
        "text_faint": "#666666",
        "on": "#50fa7b",
        "off": "#ff5555",
        "now": "#ffd700",
    },
    "nord": {
        "bg": "#2e3440",
        "accent": "#88c0d0",
        "text": "#eceff4",
        "text_dim": "#d8dee9",
        "text_faint": "#81a1c1",
        "on": "#a3be8c",
        "off": "#bf616a",
        "now": "#ebcb8b",
    },
    "catppuccin": {
        "bg": "#1e1e2e",
        "accent": "#cba6f7",
        "text": "#cdd6f4",
        "text_dim": "#a6adc8",
        "text_faint": "#6c7086",
        "on": "#a6e3a1",
        "off": "#f38ba8",
        "now": "#f9e2af",
    },
    "high_contrast": {
        "bg": "#000000",
        "accent": "#00ffff",
        "text": "#ffffff",
        "text_dim": "#e0e0e0",
        "text_faint": "#b0b0b0",
        "on": "#00ff00",
        "off": "#ff0000",
        "now": "#ffff00",
    },
}

AVAILABLE_THEMES = list(THEMES)


def colors_for(theme: str | None) -> dict[str, str]:
    """Return the colour tokens of a theme, falling back to the default one."""
    return THEMES.get(theme or "", THEMES[DEFAULT_THEME])


def next_theme(theme: str | None) -> str:
    """Return the theme that follows ``theme`` in the cycle."""
    current = theme if theme in THEMES else DEFAULT_THEME
    index = AVAILABLE_THEMES.index(current)
    return AVAILABLE_THEMES[(index + 1) % len(AVAILABLE_THEMES)]
