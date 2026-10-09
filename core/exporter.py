"""Exporter module for Svitlo CLI to export schedule to iCalendar (.ics) format."""

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def generate_ics_content(group: str, schedule_data: dict[str, Any]) -> str:
    """Generate iCalendar (.ics) content for power outage ranges in schedule_data."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Svitlo CLI//Power Outage Schedule//UA",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Графік відключень світла",
        "X-WR-TIMEZONE:Europe/Kyiv",
    ]

    now_str = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    # Extract date for current day
    schedule_date_str = schedule_data.get('schedule_date', '')
    off_ranges = schedule_data.get('off_ranges', [])

    # Process today ranges
    _add_events_for_day(lines, group, off_ranges, schedule_date_str, now_str)

    # Process next day ranges if available
    if schedule_data.get('has_next_day'):
        next_day_date_str = schedule_data.get('next_day_date', '')
        next_off_ranges = schedule_data.get('next_day_off_ranges', [])
        _add_events_for_day(lines, group, next_off_ranges, next_day_date_str, now_str)

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def _add_events_for_day(
    lines: list[str],
    group: str,
    off_ranges: list[dict[str, Any]],
    date_str: str,
    stamp: str
) -> None:
    """Parse date and off_ranges to append VEVENT entries to lines list."""
    if not off_ranges:
        return

    # Parse date_str like '5 Серпня 2026' or '05.08.2026'
    target_date = _parse_date_string(date_str)
    if not target_date:
        target_date = datetime.now()

    for idx, r in enumerate(off_ranges):
        start_hour, start_min = r['start']
        end_hour, end_min = r['end']

        dt_start = target_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)

        # Handle midnight end time (24:00 -> next day 00:00)
        if end_hour >= 24:
            dt_end = target_date.replace(hour=0, minute=end_min, second=0, microsecond=0)
            from datetime import timedelta
            dt_end += timedelta(days=1)
        else:
            dt_end = target_date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

        uid = f"svitlo-{group}-{dt_start.strftime('%Y%m%d%H%M')}-{idx}@loe"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{dt_start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{dt_end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:Відключення світла (Група {group})",
            f"DESCRIPTION:Планове відключення електроенергії згідно графіку ЛьвівОблЕнерго для групи {group}.",
            "STATUS:CONFIRMED",
            "END:VEVENT"
        ])


def _parse_date_string(date_str: str) -> datetime:
    """Parse formatted Ukrainian or dot-separated date into datetime object."""
    from core.config import MONTHS_UA

    now = datetime.now()
    if not date_str:
        return now

    # Try dot format '05.08.2026'
    try:
        parts = date_str.split('.')
        if len(parts) == 3:
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
    except ValueError:
        logger.debug("Date %r is not in dot format", date_str)

    # Try '5 Серпня 2026'
    try:
        parts = date_str.split()
        if len(parts) >= 3:
            day = int(parts[0])
            month_name = parts[1]
            year = int(parts[2])

            month = 1
            for i, m in enumerate(MONTHS_UA):
                if m.lower() in month_name.lower():
                    month = i + 1
                    break
            return datetime(year, month, day)
    except ValueError:
        logger.debug("Date %r is not in Ukrainian month-name format", date_str)

    return now


def export_to_ics_file(group: str, schedule_data: dict[str, Any], filepath: str | None = None) -> str:
    """Export schedule data to an .ics file and return the absolute path."""
    if not filepath:
        filename = f"svitlo_group_{group.replace('.', '_')}.ics"
        filepath = os.path.join(os.path.expanduser("~"), filename)

    content = generate_ics_content(group, schedule_data)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
