"""Utility functions for error handling and logging"""

import logging
from functools import wraps
from typing import Callable, Any, Optional
from datetime import datetime


def setup_logging(level: int = logging.WARNING) -> None:
    """Setup application logging with console output only"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def safe_query(widget_id: str, widget_type: type, app=None) -> Optional[Any]:
    """Safely query for a widget with proper error handling"""
    try:
        if app is None:
            return None
        return app.query_one(f"#{widget_id}", widget_type)
    except Exception as e:
        logging.warning(f"Failed to query widget #{widget_id}: {e}")
    return None


def safe_widget_update(widget: Any, content: str) -> bool:
    """Safely update widget content with error handling"""
    try:
        if widget:
            widget.update(content)
            return True
    except Exception as e:
        logging.warning(f"Failed to update widget: {e}")
    return False


def handle_ui_errors(func: Callable) -> Callable:
    """Decorator to handle UI errors gracefully and prevent crashes"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"UI Error in {func.__name__}: {e}")
            return None
    return wrapper


def handle_async_errors(func: Callable) -> Callable:
    """Decorator to handle async function errors gracefully and prevent crashes"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Async Error in {func.__name__}: {e}")
            return None
    return wrapper


def format_time_duration(seconds: int) -> str:
    """Format seconds into human readable time"""
    if seconds <= 0:
        return "0сек"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours}год")
    if minutes > 0:
        parts.append(f"{minutes}хв")
    if secs > 0 or not parts:
        parts.append(f"{secs}сек")
    return " ".join(parts)


def is_light_on(status_text: str) -> bool:
    """Check if status indicates light is on"""
    if not status_text:
        return False
    status_lower = status_text.lower()
    if 'немає' in status_lower or ' немає' in status_lower:
        return False
    return any(keyword in status_lower for keyword in [
        'світло', 'є', 'on', 'електроенергія є', 'електроенергії є'
    ])


def parse_time_to_minutes(time_str: str) -> int:
    """Parse time string like '14:30' to minutes from midnight"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return hour * 60 + minute
    except (ValueError, AttributeError):
        return 0


def minutes_to_time_str(minutes: int) -> str:
    """Convert minutes from midnight to time string"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def format_off_ranges(off_ranges: list) -> list:
    """Format off ranges as list of strings with duration"""
    if not off_ranges:
        return []
    result = []
    for range_item in off_ranges:
        start = range_item['start']
        end = range_item['end']
        start_str = f"{start[0]:02d}:{start[1]:02d}"
        end_str = f"{end[0]:02d}:{end[1]:02d}"
        start_minutes = start[0] * 60 + start[1]
        end_minutes = end[0] * 60 + end[1]
        duration_minutes = end_minutes - start_minutes
        if duration_minutes < 0:
            duration_minutes += 24 * 60
        duration_hours = duration_minutes // 60
        duration_mins = duration_minutes % 60
        if duration_mins > 0:
            duration_str = f"{duration_hours}:{duration_mins:02d} год."
        else:
            duration_str = f"{duration_hours} год."
        result.append(f"З {start_str} до {end_str}, тривалість {duration_str}")
    return result


def parse_group_from_button_id(button_id: str, prefix: str = "btn-group-") -> Optional[str]:
    """Parse group from button ID like 'btn-group-6_1' -> '6.1'"""
    if button_id and button_id.startswith(prefix):
        return button_id[len(prefix):].replace("_", ".")
    return None


def button_id_from_group(group: str, prefix: str = "btn-group-") -> str:
    """Create button ID from group like '6.1' -> 'btn-group-6_1'"""
    return f"{prefix}{group.replace('.', '_')}"


def get_current_time_minutes() -> int:
    """Get current time as minutes from midnight"""
    now = datetime.now()
    return now.hour * 60 + now.minute


def time_range_contains(current_minutes: int, start_minutes: int, end_minutes: int) -> bool:
    """Check if current time falls within a time range (handles midnight crossing)"""
    if start_minutes < end_minutes:
        return start_minutes <= current_minutes < end_minutes
    else:
        return current_minutes >= start_minutes or current_minutes < end_minutes