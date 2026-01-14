"""UI management module for Svitlo CLI application"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from textual.containers import Container
from textual.widgets import Static, Label, Select
from config import COLORS, NOTIFICATIONS, STATUS_TEXTS
from utils import safe_widget_update, safe_query, format_time_duration, parse_time_to_minutes


class UIManager:
    """Manages UI updates and state for the application"""
    
    def __init__(self, app):
        """Initialize UI manager with app reference"""
        self.app = app
        self.logger = logging.getLogger(__name__)
    
    def show_loading(self, is_loading: bool) -> None:
        """Show/hide loading indicators and update UI accordingly"""
        loading_text = STATUS_TEXTS['loading'] if is_loading else ""
        updating_text = STATUS_TEXTS['updating'] if is_loading else ""
        
        loading_indicator = safe_query("loading-indicator", Static, self.app)
        timer_display = safe_query("timer-display", Static, self.app)
        
        safe_widget_update(loading_indicator, f"◌ {loading_text}")
        safe_widget_update(timer_display, f"◌ {updating_text}")
    
    def show_error(self, error: str) -> None:
        """Display error message to the user"""
        timer_display = safe_query("timer-display", Static, self.app)
        safe_widget_update(timer_display, f"[□] Помилка: {error}")
        self.logger.error(f"Error displayed: {error}")
    
    def update_status_display(self, data: Dict[str, Any]) -> None:
        """Update main status display with current power status"""
        status = data.get('current_status', 'unknown')
        data_source = "REAL" if not data.get('is_mock') else "MOCK"
        
        timer_display = safe_query("timer-display", Static, self.app)
        
        if self._is_light_on(status):
            safe_widget_update(timer_display, f"[■] {status} ({data_source})")
            if timer_display:
                timer_display.remove_class("status-indicator-off")
                timer_display.add_class("status-indicator-on")
        else:
            safe_widget_update(timer_display, f"[□] {status} ({data_source})")
            if timer_display:
                timer_display.remove_class("status-indicator-on")
                timer_display.add_class("status-indicator-off")
    
    def update_date_display(self, data: Dict[str, Any]) -> None:
        """Update schedule date display"""
        schedule_date = data.get('schedule_date', '')
        if schedule_date:
            date_widget = safe_query("timeline-date", Static, self.app)
            safe_widget_update(date_widget, f"Дата: {schedule_date}")
    
    def update_group_display(self, group: str) -> None:
        """Update current group display"""
        group_display = safe_query("current-group-display", Static, self.app)
        safe_widget_update(group_display, f"Поточна група: {group}")
    
    def update_timeline(self, data: Dict[str, Any]) -> None:
        """Update timeline visualization"""
        now = datetime.now()
        schedule = {item['time_range']: item['status'] for item in data.get('schedule', [])}
        
        on_count = 0
        off_count = 0
        
        for i in range(48):
            block_widget = safe_query(f"halfhour-{i}", Static, self.app)
            if not block_widget:
                continue
            
            hour = i // 2
            minute = 30 if i % 2 == 1 else 0
            time_str = f"{hour:02d}:{minute:02d} - {hour:02d}:{minute:02d}"
            
            status = schedule.get(time_str, 'on')
            
            if status == 'on':
                on_count += 1
            else:
                off_count += 1
            
            self._update_hour_block(block_widget, status, now, hour, minute)
        
        self._update_timeline_summary(on_count, off_count)
    
    def update_timer(self, schedule_data: Optional[Dict[str, Any]]) -> None:
        """Update timer display with next change info"""
        if not schedule_data:
            return
        
        now = datetime.now()
        schedule = schedule_data.get('schedule', [])
        
        next_change, next_status = self._find_next_change(schedule, now)
        
        timer_display = safe_query("timer-display", Static, self.app)
        next_change_info = safe_query("next-change-info", Static, self.app)
        
        if next_change and next_status:
            delta = next_change - now
            total_seconds = max(0, int(delta.total_seconds()))
            time_str = format_time_duration(total_seconds)
            
            if next_status == 'on':
                timer_text = f"Наступне ВВІМКНЕННЯ через: {time_str}"
                next_text = NOTIFICATIONS['next_on'].format(next_change.strftime('%H:%M'))
            else:
                timer_text = f"Наступне ВИМКНЕННЯ через: {time_str}"
                next_text = NOTIFICATIONS['next_off'].format(next_change.strftime('%H:%M'))
            
            safe_widget_update(timer_display, timer_text)
            safe_widget_update(next_change_info, next_text)
        else:
            safe_widget_update(timer_display, STATUS_TEXTS['no_more_changes'])
            safe_widget_update(next_change_info, "")
    
    def show_notification(self, message: str, duration: int = 10) -> None:
        """Show temporary notification"""
        notification_widget = safe_query("notification-display", Static, self.app)
        safe_widget_update(notification_widget, message)
        
        def clear_notification():
            safe_widget_update(notification_widget, "")
        
        from threading import Timer
        timer = Timer(duration, clear_notification)
        timer.daemon = True
        timer.start()
    
    def check_and_show_notifications(self, data: Dict[str, Any]) -> None:
        """Check for and show relevant notifications"""
        if not data:
            return
        
        now = datetime.now()
        current_status = data.get('current_status', 'unknown')
        schedule = data.get('schedule', [])
        
        # Check if currently no power
        if not self._is_light_on(current_status):
            self.show_notification(NOTIFICATIONS['no_light_now'])
            return
        
        # Find the next change in schedule
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
                
                # If this time is in the future
                if target_time > now:
                    # Check if this is a status change from current
                    current_item_status = schedule[i-1]['status'] if i > 0 else 'off'
                    if item['status'] != current_item_status:
                        next_change_time = target_time
                        next_change_status = item['status']
                        break
        
        # Show notification if next change is within threshold
        if next_change_time and next_change_status:
            diff = (next_change_time - now).total_seconds() / 60  # minutes
            
            if 0 < diff <= 30:  # Within next 30 minutes
                minutes = int(diff)
                if next_change_status == 'on':
                    msg = NOTIFICATIONS['light_coming_soon'].format(minutes)
                else:
                    msg = NOTIFICATIONS['light_going_soon'].format(minutes)
                self.show_notification(msg)
    
    def _update_hour_block(self, widget: Static, status: str, now: datetime, hour: int, minute: int) -> None:
        """Update individual hour block widget"""
        is_current = (hour == now.hour and 
                     ((minute == 0 and now.minute < 30) or 
                      (minute == 30 and now.minute >= 30)))
        
        # Update current state class
        if is_current:
            widget.add_class("current")
        else:
            widget.remove_class("current")
        
        # Update status classes
        widget.remove_class("light-on")
        widget.remove_class("light-off")
        
        if status == 'off':
            widget.add_class("light-off")
        else:
            widget.add_class("light-on")
        
        safe_widget_update(widget, "")
    
    def _update_timeline_summary(self, on_count: int, off_count: int) -> None:
        """Update timeline summary statistics"""
        summary_widget = safe_query("timeline-summary", Static, self.app)
        if not summary_widget:
            return
        
        on_hours = on_count // 2
        on_mins = (on_count % 2) * 30
        off_hours = off_count // 2
        off_mins = (off_count % 2) * 30
        
        on_text = f"{on_hours}год {on_mins}хв" if on_mins > 0 else f"{on_hours}год"
        off_text = f"{off_hours}год {off_mins}хв" if off_mins > 0 else f"{off_hours}год"
        
        summary = f"[■] є: {on_text}  |  [□] немає: {off_text}"
        safe_widget_update(summary_widget, summary)
        
        # Add color styling to the summary
        if summary_widget:
            summary_widget.remove_class("status-indicator-off")
            summary_widget.add_class("status-indicator-on")
    
    def _find_next_change(self, schedule: list, now: datetime) -> tuple:
        """Find next schedule change"""
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
                target_time = now.replace(minute=0, second=0, microsecond=0, hour=hour)
                target_min = hour * 60
                
                diff = target_min - now_time
                
                if diff <= 0:
                    current_status = item['status']
                elif diff > 0 and item['status'] != current_status and diff < min_diff:
                    min_diff = diff
                    next_change = target_time
                    next_status = item['status']
        
        return next_change, next_status
    
    def _is_light_on(self, status_text: str) -> bool:
        """Check if status indicates light is on"""
        status_lower = status_text.lower()
        return any(keyword in status_lower for keyword in ['світло', 'є', 'on'])