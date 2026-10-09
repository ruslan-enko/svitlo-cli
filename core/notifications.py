"""Desktop OS notifications module for Svitlo CLI."""

import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


def send_desktop_notification(title: str, message: str) -> bool:
    """Send native desktop notification (macOS osascript or notify-send on Linux)."""
    system = platform.system()

    try:
        if system == "Darwin":
            # macOS osascript
            script = f'display notification "{message}" with title "{title}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        elif system == "Linux":
            # Linux notify-send
            subprocess.run(["notify-send", title, message], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    except Exception as e:
        logger.warning(f"Failed to send desktop notification: {e}")

    return False
