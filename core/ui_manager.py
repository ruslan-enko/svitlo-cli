"""UI management module for Svitlo CLI application."""

import logging
from datetime import datetime
from typing import Any

from textual.widgets import Static

from core.config import NOTIFICATION_THRESHOLD, NOTIFICATIONS, STATUS_TEXTS
from core.notifications import send_desktop_notification
from core.preferences import desktop_notifications_enabled
from core.utils import (
    format_off_ranges,
    format_time_duration,
    is_light_on,
    safe_query,
    safe_widget_update,
)


class UIManager:
    """Manages UI updates and state for the application."""

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.showing_next_day = False
        self.notification_clear_timer = None

    def show_loading(self, is_loading: bool) -> None:
        loading_text = STATUS_TEXTS['loading'] if is_loading else ""
        updating_text = STATUS_TEXTS['updating'] if is_loading else ""
        loading_indicator = safe_query("loading-indicator", Static, self.app)
        timer_display = safe_query("timer-display", Static, self.app)
        safe_widget_update(loading_indicator, f"{loading_text}")
        if is_loading:
            safe_widget_update(timer_display, f"{updating_text}")

    def show_error(self, error: str) -> None:
        timer_display = safe_query("timer-display", Static, self.app)
        safe_widget_update(timer_display, f"□ Помилка: {error}")
        self.logger.error(f"Error displayed: {error}")

    def update_status_display(self, data: dict[str, Any]) -> None:
        status = data.get('current_status', 'unknown')
        timer_display = safe_query("timer-display", Static, self.app)

        if is_light_on(status):
            safe_widget_update(timer_display, f"█ {status}")
            if timer_display:
                timer_display.remove_class("status-indicator-off")
                timer_display.add_class("status-indicator-on")
        else:
            safe_widget_update(timer_display, f"□ {status}")
            if timer_display:
                timer_display.remove_class("status-indicator-on")
                timer_display.add_class("status-indicator-off")

    def update_off_schedule(self, data: dict[str, Any]) -> None:
        off_schedule_widget = safe_query("off-schedule-text", Static, self.app)
        if not off_schedule_widget:
            return
        display_data = self.get_schedule_for_display(data)
        off_ranges = display_data.get('off_ranges', [])
        if not off_ranges:
            safe_widget_update(off_schedule_widget, "")
            return
        formatted_lines = format_off_ranges(off_ranges)
        if formatted_lines:
            text = "\n".join(formatted_lines)
            safe_widget_update(off_schedule_widget, text)
        else:
            safe_widget_update(off_schedule_widget, "")

    def update_date_display(self, data: dict[str, Any]) -> None:
        display_data = self.get_schedule_for_display(data)
        schedule_date = display_data.get('schedule_date', '')
        if schedule_date:
            date_widget = safe_query("timeline-date", Static, self.app)
            next_day_indicator = self.get_next_day_indicator(data)
            now = datetime.now()
            current_time = now.strftime("%H:%M")

            # Format data freshness indicator
            updated_iso = data.get('updated', '')
            freshness = ""
            if updated_iso:
                try:
                    updated_dt = datetime.fromisoformat(updated_iso)
                except (TypeError, ValueError):
                    self.logger.debug("Unparsable 'updated' value: %r", updated_iso)
                else:
                    mins_ago = max(0, int((now - updated_dt).total_seconds() / 60))
                    freshness = (
                        " | [оновлено щойно]" if mins_ago == 0
                        else f" | [оновлено {mins_ago} хв тому]"
                    )

            is_stale = data.get('is_stale', False)
            stale_badge = " [⚠️ Кеш (Офлайн)]" if is_stale else ""
            date_line = f"Дата: {schedule_date} {current_time}{freshness}{stale_badge}"

            if next_day_indicator:
                safe_widget_update(date_widget, f"{date_line} | {next_day_indicator}")
            else:
                safe_widget_update(date_widget, date_line)

    def toggle_day(self) -> bool:
        self.showing_next_day = not self.showing_next_day
        return self.showing_next_day

    def is_showing_next_day(self) -> bool:
        return self.showing_next_day

    def get_schedule_for_display(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.showing_next_day and data.get('has_next_day'):
            return {
                'schedule': data.get('next_day_schedule', []),
                'schedule_date': data.get('next_day_date', ''),
                'is_next_day': True,
                'has_next_day': data.get('has_next_day', False),
                'off_ranges': data.get('next_day_off_ranges', [])
            }
        return {
            'schedule': data.get('schedule', []),
            'schedule_date': data.get('schedule_date', ''),
            'is_next_day': False,
            'has_next_day': data.get('has_next_day', False),
            'off_ranges': data.get('off_ranges', [])
        }

    def get_next_day_indicator(self, data: dict[str, Any]) -> str:
        if data.get('has_next_day'):
            return "Завтра (t - сьогодні)" if self.showing_next_day else "Є розклад на завтра (натисніть t)"
        return ""

    def update_timeline(self, data: dict[str, Any]) -> None:
        now = datetime.now()
        display_data = self.get_schedule_for_display(data)
        schedule = {item['time_range']: item['status'] for item in display_data.get('schedule', [])}
        is_next_day = display_data.get('is_next_day', False)

        on_count = 0
        off_count = 0
        timeline_symbols = []

        for i in range(48):
            hour = i // 2
            minute = 30 if i % 2 == 1 else 0

            end_hour = hour if minute == 0 else hour + 1
            end_minute = 30 if minute == 0 else 0
            if end_hour == 24:
                end_hour = 24

            time_str = f"{hour:02d}:{minute:02d} - {end_hour:02d}:{end_minute:02d}"
            status = schedule.get(time_str, 'on')
            is_current_half = (minute == 0 and now.minute < 30) or (minute == 30 and now.minute >= 30)
            is_current_time = not is_next_day and hour == now.hour and is_current_half

            if status == 'off':
                off_count += 1
                if is_current_time:
                    timeline_symbols.append("[bold yellow]▲[#ff5555]□[/#ff5555][/bold yellow]")
                else:
                    timeline_symbols.append("[#ff5555]□[/#ff5555]")
            else:
                on_count += 1
                if is_current_time:
                    timeline_symbols.append("[bold yellow]▲[#50fa7b]■[/#50fa7b][/bold yellow]")
                else:
                    timeline_symbols.append("[#50fa7b]■[/#50fa7b]")

        timeline_widget = safe_query("timeline-grid", Static, self.app)
        if timeline_widget:
            safe_widget_update(timeline_widget, " ".join(timeline_symbols))

        self._update_timeline_summary(on_count, off_count)

    def update_timer(self, schedule_data: dict[str, Any] | None) -> None:
        if not schedule_data:
            return
        self.update_date_display(schedule_data)
        display_data = self.get_schedule_for_display(schedule_data)
        is_next_day = display_data.get('is_next_day', False)
        now = datetime.now()
        timer_display = safe_query("timer-display", Static, self.app)
        next_change_info = safe_query("next-change-info", Static, self.app)

        if self._is_all_day_light(display_data):
            if is_next_day:
                safe_widget_update(timer_display, STATUS_TEXTS['all_day_tomorrow'])
            else:
                safe_widget_update(timer_display, STATUS_TEXTS['all_day'])
            safe_widget_update(next_change_info, "")
            return

        schedule = display_data.get('schedule', [])
        if is_next_day:
            first_off, first_on = self._find_first_outage_times(schedule)
            if first_off and first_on:
                safe_widget_update(timer_display, f"Завтра перше відключення о {first_off}")
                safe_widget_update(next_change_info, f"Світло з'явиться о {first_on}")
            else:
                safe_widget_update(timer_display, STATUS_TEXTS['no_more_changes'])
                safe_widget_update(next_change_info, "")
            return

        next_day_schedule = schedule_data.get('next_day_schedule')
        next_change, next_status, current_status = self._find_next_change(schedule, now, next_day_schedule)
        if next_change and next_status:
            delta = next_change - now
            total_seconds = max(0, int(delta.total_seconds()))
            time_str = format_time_duration(total_seconds)
            current_has_light = current_status == 'on'

            if current_has_light:
                safe_widget_update(timer_display, f"До вимкнення залишилось: {time_str}")
                safe_widget_update(next_change_info, f"Світло вимкнеться о {next_change.strftime('%H:%M')}")
            else:
                safe_widget_update(timer_display, f"До ввімкнення залишилось: {time_str}")
                safe_widget_update(next_change_info, f"Світло з'явиться о {next_change.strftime('%H:%M')}")
        else:
            safe_widget_update(timer_display, STATUS_TEXTS['no_more_changes'])
            safe_widget_update(next_change_info, "")

    def _find_first_outage_times(self, schedule: list) -> tuple:
        first_off = None
        first_on = None

        for item in schedule:
            status = item['status']
            start_time = item['time_range'].split(' - ')[0]

            if status == 'off' and first_off is None:
                first_off = start_time
            elif status == 'on' and first_off is not None and first_on is None:
                first_on = start_time
                break

        return first_off, first_on

    def _find_next_change(self, schedule: list, now: datetime, next_day_schedule: list | None = None) -> tuple:
        now_time = now.hour * 60 + now.minute
        current_status = None
        next_change = None
        next_status = None
        min_diff = float('inf')

        for item in schedule:
            time_range = item['time_range']
            parts = time_range.split(' - ')
            if len(parts) == 2:
                start_str = parts[0].strip()
                hour = int(start_str.split(':')[0])
                minute = int(start_str.split(':')[1]) if ':' in start_str and len(start_str.split(':')) > 1 else 0
                target_min = hour * 60 + minute
                diff = target_min - now_time

                if diff <= 0:
                    current_status = item['status']
                elif diff > 0 and item['status'] != current_status and diff < min_diff:
                    min_diff = diff
                    target_time = now.replace(minute=minute, second=0, microsecond=0, hour=hour)
                    next_change = target_time
                    next_status = item['status']

        if next_change is None:
            target_schedule = next_day_schedule if next_day_schedule else schedule

            for item in target_schedule:
                time_range = item['time_range']
                parts = time_range.split(' - ')
                if len(parts) == 2:
                    start_str = parts[0].strip()
                    hour = int(start_str.split(':')[0])
                    minute = int(start_str.split(':')[1]) if ':' in start_str and len(start_str.split(':')) > 1 else 0

                    target_min = hour * 60 + minute + 24 * 60
                    diff = target_min - now_time

                    if item['status'] != current_status and diff < min_diff:
                        min_diff = diff
                        from datetime import timedelta
                        target_time = now.replace(minute=minute, second=0, microsecond=0, hour=hour) + timedelta(days=1)
                        next_change = target_time
                        next_status = item['status']

        return next_change, next_status, current_status

    def _is_all_day_light(self, display_data: dict[str, Any]) -> bool:
        off_ranges = display_data.get('off_ranges', [])
        current_status = display_data.get('current_status', '')

        if not off_ranges and 'є' in current_status.lower():
            return True

        schedule = display_data.get('schedule', [])
        all_on = all(item.get('status') == 'on' for item in schedule)
        return not off_ranges and all_on

    def show_notification(self, message: str, duration: int = 10) -> None:
        notification_widget = safe_query("notification-display", Static, self.app)
        safe_widget_update(notification_widget, message)

        # Thread-safe UI clear using Textual set_timer
        if hasattr(self.app, 'set_timer'):
            def clear_notification():
                safe_widget_update(notification_widget, "")
            self.app.set_timer(duration, clear_notification)

        # Also trigger native desktop notification, unless the user opted out
        if desktop_notifications_enabled():
            group = getattr(self.app, 'current_group', '')
            send_desktop_notification(f"Svitlo CLI (Група {group})", message)

    def check_and_show_notifications(self, data: dict[str, Any]) -> None:
        if not data:
            return

        off_ranges = data.get('off_ranges', [])
        if not off_ranges:
            return

        now = datetime.now()
        current_status = data.get('current_status', 'unknown')
        schedule = data.get('schedule', [])

        if not is_light_on(current_status):
            self.show_notification(NOTIFICATIONS['no_light_now'])
            return

        next_change_time = None
        next_change_status = None

        for i, item in enumerate(schedule):
            time_range = item['time_range']
            parts = time_range.split(' - ')
            if len(parts) == 2:
                start_str = parts[0].strip()
                hour = int(start_str.split(':')[0])
                minute = int(start_str.split(':')[1]) if ':' in start_str and len(start_str.split(':')) > 1 else 0
                target_time = now.replace(minute=minute, second=0, microsecond=0, hour=hour)

                if target_time > now:
                    current_item_status = schedule[i-1]['status'] if i > 0 else schedule[0]['status']
                    if item['status'] != current_item_status:
                        next_change_time = target_time
                        next_change_status = item['status']
                        break

        if next_change_time and next_change_status:
            diff = (next_change_time - now).total_seconds() / 60
            if 0 < diff <= NOTIFICATION_THRESHOLD:
                minutes = int(diff)
                key = 'light_coming_soon' if next_change_status == 'on' else 'light_going_soon'
                self.show_notification(NOTIFICATIONS[key].format(minutes))

    def _update_timeline_summary(self, on_count: int, off_count: int) -> None:
        summary_widget = safe_query("timeline-summary", Static, self.app)
        if not summary_widget:
            return
        on_hours = on_count // 2
        on_mins = (on_count % 2) * 30
        off_hours = off_count // 2
        off_mins = (off_count % 2) * 30
        on_text = f"{on_hours}год {on_mins}хв" if on_mins > 0 else f"{on_hours}год"
        off_text = f"{off_hours}год {off_mins}хв" if off_mins > 0 else f"{off_hours}год"
        summary = (
            f"[#50fa7b]■ є: {on_text}[/#50fa7b]  |  "
            f"[#ff5555]□ немає: {off_text}[/#ff5555]  |  "
            "[bold yellow]▲ зараз[/bold yellow]"
        )
        safe_widget_update(summary_widget, summary)
