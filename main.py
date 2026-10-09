"""Main application module for Svitlo CLI."""

import argparse
import json
import logging
import os
import sys
import warnings
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.events import Resize
from textual.widgets import Button, Label, Static

from core.config import (
    APP_NAME,
    APP_VERSION,
    AVAILABLE_GROUPS,
    BTN_ID_EXPORT,
    BTN_ID_GROUP_SELECT,
    BTN_ID_QUIT,
    BTN_ID_REFRESH,
    BTN_PREFIX_GROUP,
    DATA_REFRESH_INTERVAL,
    DEFAULT_GROUP,
    UPDATE_INTERVAL,
)
from core.exporter import export_to_ics_file
from core.preferences import (
    get_favorites,
    get_saved_group,
    is_first_run,
    save_preferences,
)
from core.schedule_fetcher import ScheduleFetcher
from core.ui_manager import UIManager
from core.utils import handle_ui_errors, parse_group_from_button_id, setup_logging
from layout.layout_manager import LayoutManager, LayoutType
from screens import GroupSelectDialog, GroupSelectionScreen, HelpDialog
from ui.popup_utils import make_button_label


def configure_warnings() -> None:
    """Suppress common SSL-related warnings on macOS environments."""
    warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")
    warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL 1.1.1+.*")
    try:
        from urllib3.exceptions import NotOpenSSLWarning
        warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
    except Exception:
        pass


def load_css() -> str:
    """Load CSS styles from external file."""
    try:
        css_file = os.path.join(os.path.dirname(__file__), 'styles.css')
        with open(css_file, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, OSError) as e:
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
        ("g", "open_group_select", "Група"),
        ("e", "export_ics", "Експорт ICS"),
        ("f", "toggle_favorite", "Favorites"),
        ("h", "show_help", "Довідка"),
        ("question_mark", "show_help", "Довідка"),
        ("up", "scroll_up", "Вгору"),
        ("down", "scroll_down", "Вниз"),
        ("pageup", "page_up", "Сторінка вгору"),
        ("pagedown", "page_down", "Сторінка вниз"),
        ("home", "scroll_home", "На початок"),
        ("end", "scroll_end", "В кінець"),
        ("q", "quit", "Вихід"),
    ]
    
    ENABLE_SCROLLING = True

    def __init__(self, initial_group: str | None = None):
        super().__init__()
        self.fetcher = ScheduleFetcher()
        self.ui_manager = UIManager(self)
        self.current_group = initial_group if initial_group else DEFAULT_GROUP
        self.current_group_index = AVAILABLE_GROUPS.index(self.current_group) if self.current_group in AVAILABLE_GROUPS else 0
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
                    yield Static("■ є  |  □ немає  |  ▲ зараз", id="timeline-legend")
                    yield Static("", id="timeline-grid")
                    yield Static("", id="timeline-summary")

                with Container(id="controls-container"):
                    yield Static("Завантаження...", id="timer-display")
                    yield Static("", id="next-change-info")
                    yield Static("", id="notification-display")
                    yield Static("", id="off-schedule-text")
                    yield Static("", id="loading-indicator")
 
            with Container(id="actions-container"):
                yield Button(make_button_label(f"Група {self.current_group}"), id=BTN_ID_GROUP_SELECT)
                yield Button(make_button_label("Експорт .ics"), id=BTN_ID_EXPORT)
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

    def set_current_group(self, group: str | None) -> None:
        self.current_group = group if group and group in AVAILABLE_GROUPS else DEFAULT_GROUP
        self.current_group_index = AVAILABLE_GROUPS.index(self.current_group)
        save_preferences(self.current_group)

    def on_resize(self, event: Resize) -> None:
        try:
            layout_type = LayoutManager.get_layout_type(event.size.width, event.size.height)
            self._apply_layout(layout_type)
        except Exception as e:
            logging.error(f"Resize error: {e}")

    def _apply_layout(self, layout_type: LayoutType) -> None:
        config = LayoutManager.get_config(layout_type)
        legend = self.query_one("#timeline-legend")
        legend.display = config['show_legend']

    def _create_all_day_light_schedule(self) -> dict:
        """Create a default schedule indicating light is available all day."""
        now = datetime.now()
        schedule = []
        for i in range(48):
            hour = i // 2
            minute = 0 if i % 2 == 0 else 30
            end_hour = hour if minute == 0 else hour + 1
            end_minute = 30 if minute == 0 else 0
            schedule.append({
                'time_range': f"{hour:02d}:{minute:02d} - {end_hour:02d}:{end_minute:02d}",
                'status': 'on'
            })

        from core.config import MONTHS_UA
        date_str = f"{now.day} {MONTHS_UA[now.month - 1]} {now.year}"
        return {
            'schedule': schedule,
            'current_status': 'Світло є',
            'next_event': 'Немає запланованих змін',
            'schedule_date': date_str,
            'update_time': now.strftime("%H:%M %d.%m.%Y"),
            'off_ranges': [],
            'has_next_day': False
        }

    async def _load_schedule(self) -> None:
        self.ui_manager.show_loading(True)
        try:
            result = await self.fetcher.fetch_schedules()
            if not result:
                self.ui_manager.show_error("Не вдалося завантажити дані")
                return
            if result.get('data'):
                self.all_schedules = result['data']
                self.updated = result.get('updated', '')
                self._apply_group_schedule_from_cache(self.current_group)
                if not result.get('success'):
                    self.ui_manager.show_error(result.get('error', 'Кешовані дані'))
            else:
                self.ui_manager.show_error(result.get('error', 'Помилка розкладу'))
        finally:
            self.ui_manager.show_loading(False)

    def _apply_group_schedule_from_cache(self, group: str) -> bool:
        """Apply schedule for a group from loaded cache."""
        if not self.all_schedules or group not in self.all_schedules:
            return False

        self.schedule_data = self.all_schedules[group]
        if not self.schedule_data:
            self.schedule_data = self._create_all_day_light_schedule()
        self._update_ui(self.schedule_data, self.updated)
        return True

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
        elif button_id == BTN_ID_EXPORT:
            self.action_export_ics()
        elif button_id == BTN_ID_QUIT:
            self.exit()
        elif button_id == BTN_ID_GROUP_SELECT:
            self.action_open_group_select()
        elif button_id.startswith(BTN_PREFIX_GROUP):
            group = parse_group_from_button_id(button_id)
            if group:
                self._handle_group_change(group)

    def _handle_group_change(self, group: str) -> None:
        self.set_current_group(group)
        self.update_group_button_label()

        if not self._apply_group_schedule_from_cache(group):
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

    def action_open_group_select(self) -> None:
        self.push_screen(GroupSelectDialog())

    def action_show_help(self) -> None:
        self.push_screen(HelpDialog())

    def action_export_ics(self) -> None:
        if self.schedule_data:
            filepath = export_to_ics_file(self.current_group, self.schedule_data)
            self.ui_manager.show_notification(f"✓ Розклад експортовано у {filepath}")

    def action_toggle_favorite(self) -> None:
        favs = get_favorites()
        if not favs:
            return
        current_idx = favs.index(self.current_group) if self.current_group in favs else -1
        next_idx = (current_idx + 1) % len(favs)
        next_group = favs[next_idx]
        self._handle_group_change(next_group)
        self.ui_manager.show_notification(f"Обрана група: {next_group}")


async def handle_cli_mode(args: argparse.Namespace) -> None:
    """Execute non-interactive CLI mode commands."""
    fetcher = ScheduleFetcher()
    result = await fetcher.fetch_schedules()

    if not result or not result.get('data'):
        print(json.dumps({"error": "Failed to fetch schedules"}) if args.json else "Error: Failed to fetch schedules")
        sys.exit(1)

    target_group = args.group if args.group else get_saved_group()
    if not target_group or target_group not in AVAILABLE_GROUPS:
        target_group = DEFAULT_GROUP

    schedule = result['data'].get(target_group, {})

    if args.json:
        print(json.dumps({
            "group": target_group,
            "status": schedule.get('current_status', 'Unknown'),
            "next_event": schedule.get('next_event', ''),
            "off_ranges": schedule.get('off_ranges', []),
            "updated": result.get('updated', '')
        }, ensure_ascii=False, indent=2))
        return

    if args.export_ics:
        filepath = export_to_ics_file(target_group, schedule)
        print(f"Exported .ics calendar to: {filepath}")
        return

    if args.status:
        status = schedule.get('current_status', 'Світло є')
        next_ev = schedule.get('next_event', '')
        print(f"Група {target_group}: {status} ({next_ev})")
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION} - Power outage monitor for Lviv")
    parser.add_argument("--status", action="store_true", help="Print current status in one line and exit")
    parser.add_argument("--json", action="store_true", help="Output full schedule data in JSON format and exit")
    parser.add_argument("--group", "-g", type=str, help="Specify group (e.g. 6.1)")
    parser.add_argument("--export-ics", action="store_true", help="Export schedule to .ics file and exit")
    parser.add_argument("--version", "-v", action="version", version=f"{APP_NAME} v{APP_VERSION}")

    args = parser.parse_args()

    if args.status or args.json or args.export_ics:
        import asyncio
        asyncio.run(handle_cli_mode(args))
        sys.exit(0)

    configure_warnings()
    setup_logging()
    app = SvitloApp(initial_group=args.group)
    app.run()


if __name__ == "__main__":
    main()
