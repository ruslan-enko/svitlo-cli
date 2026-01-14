import warnings
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings('ignore', category=NotOpenSSLWarning)
except ImportError:
    pass

from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Static, Label, Button, Select
from datetime import datetime
import logging

from schedule_fetcher import ScheduleFetcher
from ui_manager import UIManager
from config import APP_NAME, APP_VERSION, COLORS, AVAILABLE_GROUPS, DEFAULT_GROUP, UPDATE_INTERVAL, DATA_REFRESH_INTERVAL, NOTIFICATION_DURATION
from utils import setup_logging, handle_ui_errors, safe_query
import os

# Load CSS from file
def load_css():
    """Load CSS styles from external file"""
    try:
        css_file = os.path.join(os.path.dirname(__file__), 'styles.css')
        with open(css_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Failed to load CSS: {e}")
        return ""


class SvitloApp(App):
    CSS = load_css()
    
    TITLE = f"{APP_NAME} v{APP_VERSION}"
    BINDINGS = [
        ("r", "refresh", "Оновити"),
        ("t", "toggle_day", "Завтра/Сьогодні"),
        ("q", "quit", "Вихід"),
    ]

    def __init__(self):
        """Initialize the application with required components"""
        super().__init__()
        self.fetcher = ScheduleFetcher()
        self.ui_manager = UIManager(self)
        self.current_group = DEFAULT_GROUP
        self.schedule_data = None
        self.updated = ""
        self.last_notification_time = None
        self.auto_refresh_enabled = True
        self.logger = logging.getLogger(__name__)

    def compose(self) -> ComposeResult:
        """Compose application UI"""
        with Container(id="main-container"):
            with Vertical(id="timeline-container"):
                # ASCII Art Logo
                yield Label(
                    "           _ __  __           ___ ",
                    id="timeline-label-1"
                )
                yield Label(
                    "  ____  __(_) /_/ /__    ____/ (_)",
                    id="timeline-label-2"
                )
                yield Label(
                    " (_-< |/ / / __/ / _ \  / __/ / / ",
                    id="timeline-label-3"
                )
                yield Label(
                    "/___/___/_/\__/_/\___/  \__/_/_/  ",
                    id="timeline-label-4"
                )
                
                # Timeline components
                yield Static("", id="timeline-date")
                yield Static("■ є  |  □ немає  |  * зараз", id="timeline-legend")
                yield Static("", id="timeline-grid")
                yield Static("", id="timeline-summary")

            with Container(id="controls-container"):
                yield Static("Завантаження...", id="timer-display")
                yield Static("", id="next-change-info")
                yield Static("", id="notification-display")

                yield Label("ВИБІР ГРУПИ:")
                yield Select(
                    [(f"Група {g}", g) for g in AVAILABLE_GROUPS],
                    value=DEFAULT_GROUP,
                    id="group-select"
                )
                yield Static("", id="loading-indicator")

            with Container(id="actions-container"):
                yield Button("r: Оновити", id="action-refresh")
                yield Button("q: Вихід", id="action-quit")

            with Container(id="info-container"):
                yield Static(
                    "r: оновити  |  q: вихід",
                    id="info-text"
                )

        self.set_interval(UPDATE_INTERVAL, self.update_timer)
        self.set_interval(DATA_REFRESH_INTERVAL, self._do_auto_refresh)

    @handle_ui_errors
    async def on_mount(self) -> None:
        """Initialize app after mounting"""
        await self.load_schedule()

    async def load_schedule(self):
        """Load schedule data from fetcher"""
        self.ui_manager.show_loading(True)
        try:
            result = await self.fetcher.fetch_group_schedule(self.current_group)

            if result['success']:
                self.schedule_data = result['data']
                self.updated = result.get('updated', '')
                self.update_ui(result['data'], self.updated)
            else:
                self.ui_manager.show_error(result.get('error', 'Unknown error'))
        finally:
            self.ui_manager.show_loading(False)

    @handle_ui_errors
    def update_ui(self, data: dict, updated: str):
        """Update all UI components with new data"""
        self.ui_manager.update_status_display(data)
        self.ui_manager.update_timeline(data)
        self.ui_manager.update_date_display(data)
        self.update_timer()
        self.ui_manager.check_and_show_notifications(data)

    def update_timer(self):
        """Update timer display and check for notifications"""
        if not self.schedule_data:
            return

        # Check for notifications every minute
        current_minute = datetime.now().minute
        if self.last_notification_time != current_minute:
            self.last_notification_time = current_minute
            self.ui_manager.check_and_show_notifications(self.schedule_data)

        self.ui_manager.update_timer(self.schedule_data)

    def _do_auto_refresh(self) -> None:
        """Auto-refresh schedule data if enabled"""
        if self.auto_refresh_enabled and self.schedule_data:
            self.logger.info("Auto-refreshing schedule data...")
            self.run_worker(self.load_schedule())

    @handle_ui_errors
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "action-refresh":
            self.action_refresh()
        elif event.button.id == "action-quit":
            self.exit()

    @handle_ui_errors
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle group selection change"""
        if event.value:
            self.current_group = str(event.value)
            self.run_worker(self.load_schedule())

    def action_refresh(self) -> None:
        """Refresh schedule data"""
        self.run_worker(self.load_schedule())
    
    def action_toggle_day(self) -> None:
        """Toggle between today and next day schedule"""
        if self.schedule_data:
            showing_next = self.ui_manager.toggle_day()
            day_text = "завтра" if showing_next else "сьогодні"
            self.notify(f"Показано розклад на {day_text}", severity="information")
            self.update_ui(self.schedule_data, self.updated)


def main():
    """Main entry point for the application"""
    setup_logging()
    app = SvitloApp()
    app.run()


if __name__ == "__main__":
    main()
