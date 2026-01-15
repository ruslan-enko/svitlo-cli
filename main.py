"""Main application module for Svitlo CLI"""

import warnings
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings('ignore', category=NotOpenSSLWarning)
except ImportError:
    pass

from textual.app import App, ComposeResult
from textual.containers import Vertical, Container
from textual.widgets import Static, Label, Button
from textual import events
from datetime import datetime
import logging
import os

from core.schedule_fetcher import ScheduleFetcher
from core.ui_manager import UIManager
from core.config import (
    APP_NAME, APP_VERSION, COLORS, AVAILABLE_GROUPS, DEFAULT_GROUP,
    UPDATE_INTERVAL, DATA_REFRESH_INTERVAL, NOTIFICATION_DURATION,
    MIN_TERMINAL_WIDTH, MIN_TERMINAL_HEIGHT
)
from layout.layout_manager import LayoutManager, LayoutType
from screens import GroupSelectionScreen, GroupSelectDialog
from ui.popup_utils import make_button_label
from core.utils import setup_logging, handle_ui_errors
from core.preferences import save_preferences, load_preferences, is_first_run, get_saved_group


def load_css() -> str:
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
        self.current_group_index = AVAILABLE_GROUPS.index(DEFAULT_GROUP)
        self.schedule_data = None
        self.updated = ""
        self.last_notification_time = None
        self.auto_refresh_enabled = True
        self.logger = logging.getLogger(__name__)

    def compose(self) -> ComposeResult:
        """Compose application UI"""
        with Container(id="main-container"):
            with Container(id="main-content"):
                with Vertical(id="timeline-container"):
                    # ASCII Art Logo
                    yield Label(
                        r"           _ __  __           ___ ",
                        id="timeline-label-1"
                    )
                    yield Label(
                        r"  ____  __(_) /_/ /__    ____/ (_)",
                        id="timeline-label-2"
                    )
                    yield Label(
                        r" (_-< |/ / / __/ / _ \  / __/ / / ",
                        id="timeline-label-3"
                    )
                    yield Label(
                        r"/___/___/_/\__/_/\___/  \__/_/_/  ",
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

                    yield Static("", id="off-schedule-text")

                    yield Static("", id="loading-indicator")

            # Actions container at the bottom
            with Container(id="actions-container"):
                yield Button(make_button_label("Група 6.1"), id="btn-group-select")
                yield Button(make_button_label("Оновити"), id="action-refresh")
                yield Button(make_button_label("Вихід"), id="action-quit")

        self.set_interval(UPDATE_INTERVAL, self.update_timer)
        self.set_interval(DATA_REFRESH_INTERVAL, self._do_auto_refresh)

    @handle_ui_errors
    async def on_mount(self) -> None:
        """Initialize app after mounting"""
        if is_first_run():
            group = await self.push_screen(GroupSelectionScreen())
            if group:
                self.current_group = str(group)
                self.current_group_index = AVAILABLE_GROUPS.index(self.current_group)
                save_preferences(group, is_first_run=False)
            else:
                self.current_group = DEFAULT_GROUP
                self.current_group_index = AVAILABLE_GROUPS.index(DEFAULT_GROUP)
        else:
            saved_group = get_saved_group()
            if saved_group:
                self.current_group = saved_group
                self.current_group_index = AVAILABLE_GROUPS.index(self.current_group)
            else:
                self.current_group = DEFAULT_GROUP
                self.current_group_index = AVAILABLE_GROUPS.index(DEFAULT_GROUP)

        self.update_group_button_label()
        await self.load_schedule()

    def on_resize(self, event: events.Resize) -> None:
        """Adaptive layout on terminal resize"""
        layout_type = LayoutManager.get_layout_type(event.size.width, event.size.height)
        self.apply_layout(layout_type)
        
        self._current_layout_type = layout_type

    def apply_layout(self, layout_type: LayoutType) -> None:
        """Apply layout configuration"""
        config = LayoutManager.get_config(layout_type)

        legend = self.query_one("#timeline-legend")
        legend.display = config['show_legend']

    async def load_schedule(self) -> None:
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
    def update_ui(self, data: dict, updated: str) -> None:
        """Update all UI components with new data"""
        self.ui_manager.update_status_display(data)
        self.ui_manager.update_timeline(data)
        self.ui_manager.update_date_display(data)
        self.ui_manager.update_off_schedule(data)
        self.update_timer()
        self.ui_manager.check_and_show_notifications(data)

    def update_timer(self) -> None:
        """Update timer display and check for notifications"""
        if not self.schedule_data:
            return

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
        elif event.button.id == "btn-group-select":
            self.push_screen(GroupSelectDialog())
        elif event.button.id and event.button.id.startswith("btn-group-"):
            group = event.button.id.replace("btn-group-", "").replace("_", ".")
            self.current_group = group
            self.current_group_index = AVAILABLE_GROUPS.index(group)
            save_preferences(self.current_group)
            self.update_group_button_label()
            self.run_worker(self.load_schedule())

    def update_group_button_label(self) -> None:
        """Update the group selection button label"""
        group_button = self.query_one("#btn-group-select", Button)
        group_button.label = make_button_label(f"Група {self.current_group}")

    def action_refresh(self) -> None:
        """Refresh schedule data"""
        self.run_worker(self.load_schedule())

    def action_toggle_day(self) -> None:
        """Toggle between today and tomorrow schedule"""
        self.ui_manager.toggle_day()
        if self.schedule_data:
            self.update_ui(self.schedule_data, self.updated)


def main() -> None:
    """Main entry point for the application"""
    setup_logging()
    app = SvitloApp()
    app.run()
