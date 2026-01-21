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
from textual.events import Resize
from datetime import datetime
import logging
import os
from typing import Optional

from core.schedule_fetcher import ScheduleFetcher
from core.ui_manager import UIManager
from core.config import (
    APP_NAME, APP_VERSION, COLORS, AVAILABLE_GROUPS, DEFAULT_GROUP,
    MIN_TERMINAL_WIDTH, MIN_TERMINAL_HEIGHT,
    BTN_PREFIX_GROUP, BTN_ID_REFRESH, BTN_ID_QUIT, BTN_ID_GROUP_SELECT,
    NOTIFICATION_DURATION, UPDATE_INTERVAL, DATA_REFRESH_INTERVAL
)
from layout.layout_manager import LayoutManager, LayoutType
from screens import GroupSelectionScreen, GroupSelectDialog
from ui.popup_utils import make_button_label
from core.utils import (
    setup_logging, handle_ui_errors,
    parse_group_from_button_id
)
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


LOGO_LINES = [
    r"           _ __  __           ___ ",
    r"  ____  __(_) /_/ /__    ____/ (_)",
    r" (_-< |/ / / __/ / _ \  / __/ / / ",
    r"/___/___/_/\__/_/\___/  \__/_/_/  ",
]


class SvitloApp(App):
    CSS = load_css()

    TITLE = f"{APP_NAME} v{APP_VERSION}"
    BINDINGS = [
        ("r", "refresh", "Оновити"),
        ("t", "toggle_day", "Завтра/Сьогодні"),
        ("up", "scroll_up", "Вгору"),
        ("down", "scroll_down", "Вниз"),
        ("pageup", "page_up", "Сторінка вгору"),
        ("pagedown", "page_down", "Сторінка вниз"),
        ("home", "scroll_home", "На початок"),
        ("end", "scroll_end", "В кінець"),
        ("q", "quit", "Вихід"),
    ]
    
    # Enable scrolling when content doesn't fit on screen
    ENABLE_SCROLLING = True

    def __init__(self):
        super().__init__()
        self.fetcher = ScheduleFetcher()
        self.ui_manager = UIManager(self)
        self.current_group = DEFAULT_GROUP
        self.current_group_index = AVAILABLE_GROUPS.index(DEFAULT_GROUP)
        self.schedule_data = None
        self.all_schedules = None
        self.updated = ""
        self.last_notification_minute = -1
        self.auto_refresh_enabled = True
        self.logger = logging.getLogger(__name__)

    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            with Container(id="main-content"):
                with Vertical(id="timeline-container"):
                    for i, line in enumerate(LOGO_LINES):
                        yield Label(line, id=f"timeline-label-{i + 1}")
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

            with Container(id="actions-container"):
                yield Button(make_button_label(f"Група {DEFAULT_GROUP}"), id=BTN_ID_GROUP_SELECT)
                yield Button(make_button_label("Оновити"), id=BTN_ID_REFRESH)
                yield Button(make_button_label("Вихід"), id=BTN_ID_QUIT)

        self.set_interval(UPDATE_INTERVAL, self.update_timer)
        self.set_interval(DATA_REFRESH_INTERVAL, self._do_auto_refresh)

    @handle_ui_errors
    async def on_mount(self) -> None:
        await self._init_group()
        self.update_group_button_label()
        self.run_worker(self._load_schedule())

    async def _init_group(self) -> None:
        group = None
        if is_first_run():
            group = await self.push_screen(GroupSelectionScreen())
        else:
            group = get_saved_group()
        self.set_current_group(group)

    def set_current_group(self, group: Optional[str]) -> None:
        self.current_group = group if group else DEFAULT_GROUP
        self.current_group_index = AVAILABLE_GROUPS.index(self.current_group)
        save_preferences(self.current_group)

    def on_resize(self, event: Resize) -> None:
        layout_type = LayoutManager.get_layout_type(event.size.width, event.size.height)
        self._apply_layout(layout_type)

    def _apply_layout(self, layout_type: LayoutType) -> None:
        config = LayoutManager.get_config(layout_type)
        legend = self.query_one("#timeline-legend")
        legend.display = config['show_legend']

    async def _load_schedule(self) -> None:
        self.ui_manager.show_loading(True)
        try:
            result = await self.fetcher.fetch_schedules()
            if result['success']:
                self.all_schedules = result['data']
                self.updated = result.get('updated', '')
                
                # Update current view
                if self.current_group in self.all_schedules:
                    self.schedule_data = self.all_schedules[self.current_group]
                    self._update_ui(self.schedule_data, self.updated)
            else:
                self.ui_manager.show_error(result.get('error', 'Unknown error'))
                # If we have mock data in result, use it
                if 'data' in result:
                    self.all_schedules = result['data']
                    if self.current_group in self.all_schedules:
                        self.schedule_data = self.all_schedules[self.current_group]
                        self._update_ui(self.schedule_data, self.updated)
        finally:
            self.ui_manager.show_loading(False)

    def _update_ui(self, data: dict, updated: str) -> None:
        self.ui_manager.update_status_display(data)
        self.ui_manager.update_timeline(data)
        self.ui_manager.update_date_display(data)
        self.ui_manager.update_off_schedule(data)
        self.update_timer()
        self.ui_manager.check_and_show_notifications(data)

    def update_timer(self) -> None:
        if not self.schedule_data:
            return
        current_minute = datetime.now().minute
        if self.last_notification_minute != current_minute:
            self.last_notification_minute = current_minute
            self.ui_manager.check_and_show_notifications(self.schedule_data)
        self.ui_manager.update_timer(self.schedule_data)

    def _do_auto_refresh(self) -> None:
        if self.auto_refresh_enabled and self.schedule_data:
            self.logger.info("Auto-refreshing schedule data...")
            self.run_worker(self._load_schedule())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if not button_id:
            return

        if button_id == BTN_ID_REFRESH:
            self._action_refresh()
        elif button_id == BTN_ID_QUIT:
            self.exit()
        elif button_id == BTN_ID_GROUP_SELECT:
            self.push_screen(GroupSelectDialog())
        elif button_id.startswith(BTN_PREFIX_GROUP):
            group = parse_group_from_button_id(button_id)
            if group:
                self._handle_group_change(group)

    def _handle_group_change(self, group: str) -> None:
        self.set_current_group(group)
        self.update_group_button_label()
        
        # If we have cached data, update UI immediately
        if self.all_schedules and group in self.all_schedules:
            self.schedule_data = self.all_schedules[group]
            self._update_ui(self.schedule_data, self.updated)
        else:
            self.run_worker(self._load_schedule())

    def update_group_button_label(self) -> None:
        group_button = self.query_one(f"#{BTN_ID_GROUP_SELECT}", Button)
        group_button.label = make_button_label(f"Група {self.current_group}")

    def _action_refresh(self) -> None:
        self.run_worker(self._load_schedule())

    def action_toggle_day(self) -> None:
        self.ui_manager.toggle_day()
        if self.schedule_data:
            self._update_ui(self.schedule_data, self.updated)

    def action_refresh(self) -> None:
        self._action_refresh()


def main() -> None:
    setup_logging()
    app = SvitloApp()
    app.run()
