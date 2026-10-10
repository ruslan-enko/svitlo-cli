"""Popup screens for Svitlo CLI application."""

from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from core.address_lookup import search_address
from core.config import (
    AVAILABLE_GROUPS,
    BTN_PREFIX_GROUP,
    BTN_PREFIX_MODAL,
    BTN_PREFIX_THEME,
    DEFAULT_GROUP,
    FIRST_RUN_MESSAGE,
    FIRST_RUN_TITLE,
)
from core.preferences import save_preferences
from core.themes import AVAILABLE_THEMES, DEFAULT_THEME, colors_for
from core.utils import button_id_from_group, parse_group_from_button_id
from layout.layout_manager import LayoutManager
from ui.popup_utils import make_button_label


def theme_colors(app) -> dict[str, str]:
    """Colour tokens of the theme the app is currently using."""
    return colors_for(getattr(app, 'theme_name', DEFAULT_THEME))


def _make_group_button(group: str, prefix: str = BTN_PREFIX_MODAL, colors: dict[str, str] | None = None) -> Button:
    return Button(
        make_button_label(f"Група {group}", colors),
        id=button_id_from_group(group, prefix)
    )


class GroupSelectionScreen(Screen):
    """Screen for group selection on first launch."""

    def compose(self) -> ComposeResult:
        colors = theme_colors(self.app)
        layout_type = LayoutManager.get_layout_type(self.app.size.width, self.app.size.height)
        config = LayoutManager.get_config(layout_type)
        grid_class = f"modal-grid grid-cols-{config['popup_columns']}"

        with Container(classes="modal-container"):
            yield Label(FIRST_RUN_TITLE, classes="modal-title")
            yield Label(FIRST_RUN_MESSAGE, classes="modal-message")
            with Grid(classes=grid_class):
                for g in AVAILABLE_GROUPS:
                    yield _make_group_button(g, BTN_PREFIX_MODAL, colors)
            with Container(classes="modal-back-container"):
                yield Button(make_button_label("Далі", colors), id="btn-continue")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-continue":
            app = self.app
            if hasattr(app, 'current_group') and app.current_group:
                self.dismiss(app.current_group)
            else:
                app.current_group = DEFAULT_GROUP
                app.current_group_index = AVAILABLE_GROUPS.index(DEFAULT_GROUP)
                save_preferences(DEFAULT_GROUP, is_first_run=False)
                self.dismiss(DEFAULT_GROUP)
        elif event.button.id and event.button.id.startswith(BTN_PREFIX_MODAL):
            group = parse_group_from_button_id(event.button.id, BTN_PREFIX_MODAL)
            if group:
                self.app.current_group = group
                save_preferences(group, is_first_run=False)
                self.dismiss(group)


class GroupSelectDialog(Screen):
    """Dialog for group selection."""

    def compose(self) -> ComposeResult:
        colors = theme_colors(self.app)
        layout_type = LayoutManager.get_layout_type(self.app.size.width, self.app.size.height)
        config = LayoutManager.get_config(layout_type)
        grid_class = f"dialog-grid grid-cols-{config['popup_columns']}"

        with Container(classes="dialog-container"):
            yield Label("Оберіть групу", classes="dialog-title")
            with Grid(classes=grid_class):
                for g in AVAILABLE_GROUPS:
                    yield _make_group_button(g, BTN_PREFIX_GROUP, colors)
            with Container(classes="dialog-back-container"):
                yield Button(make_button_label("Пошук за адресою", colors), id="btn-address-search")
                yield Button(make_button_label("Назад", colors), id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-back":
            self.dismiss()
        elif button_id == "btn-address-search":
            self.dismiss()
            self.app.push_screen(AddressLookupDialog())
        elif button_id and button_id.startswith(BTN_PREFIX_GROUP):
            group = parse_group_from_button_id(button_id, BTN_PREFIX_GROUP)
            if group:
                app = self.app
                if hasattr(app, 'set_current_group'):
                    app.set_current_group(group)
                    if hasattr(app, 'update_group_button_label'):
                        app.update_group_button_label()
                    if hasattr(app, '_apply_group_schedule_from_cache'):
                        app._apply_group_schedule_from_cache(group)
                self.dismiss()


class AddressLookupDialog(Screen):
    """Dialog to lookup group by street address."""

    def compose(self) -> ComposeResult:
        colors = theme_colors(self.app)
        with Container(classes="lookup-container"):
            yield Label("Пошук групи за вулицею / районом", classes="lookup-title")
            yield Input(placeholder="Введіть назву вулиці (напр. Стрийська)...", id="street-input")
            yield Static("Введіть назву вулиці для пошуку відповідної групи...", id="results-area")
            with Container(classes="lookup-actions"):
                yield Button(make_button_label("Закрити", colors), id="btn-close-lookup")

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value
        results = search_address(query)
        results_widget = self.query_one("#results-area", Static)
        if not query:
            results_widget.update("Введіть назву вулиці для пошуку відповідної групи...")
        elif not results:
            results_widget.update(f"За запитом '{query}' груп не знайдено.")
        else:
            lines = [
                f"[bold]{r['street']}[/bold] ({r['district']} р-н) -> [bold yellow]Група {r['group']}[/bold yellow]"
                for r in results
            ]
            results_widget.update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-lookup":
            self.dismiss()


class HelpDialog(Screen):
    """Dialog showing keyboard shortcuts and app guide."""

    def compose(self) -> ComposeResult:
        colors = theme_colors(self.app)
        accent, on_color, off_color, now_color = (
            colors['accent'], colors['on'], colors['off'], colors['now']
        )
        help_content = (
            f"[bold {accent}]Гарячі клавіші:[/bold {accent}]\n"
            "  [bold]r[/bold] - Оновити дані з сайту\n"
            "  [bold]t[/bold] - Переключити розклад (Сьогодні / Завтра)\n"
            "  [bold]g[/bold] - Відкрити вибір групи\n"
            "  [bold]e[/bold] - Експортувати розклад в календар (.ics)\n"
            "  [bold]f[/bold] - Переключити обрану групу (Favorites)\n"
            "  [bold]T[/bold] - Змінити тему оформлення\n"
            "  [bold]n[/bold] - Увімкнути / вимкнути системні сповіщення\n"
            "  [bold]?[/bold] або [bold]h[/bold] - Довідка\n"
            "  [bold]q[/bold] - Вийти з програми\n\n"
            f"[bold {accent}]Позначення:[/bold {accent}]\n"
            f"  [{on_color}]■[/{on_color}] - Світло є\n"
            f"  [{off_color}]□[/{off_color}] - Світла немає\n"
            f"  [{now_color}]▲[/{now_color}] - Поточний час"
        )
        with Container(classes="help-container"):
            yield Label("Довідка Svitlo CLI", classes="help-title")
            yield Static(help_content, classes="help-text")
            yield Button(make_button_label("Зрозуміло", colors), id="btn-close-help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-help":
            self.dismiss()


class ThemeDialog(Screen):
    """Dialog for picking a colour theme."""

    def compose(self) -> ComposeResult:
        colors = theme_colors(self.app)
        current = getattr(self.app, 'theme_name', DEFAULT_THEME)
        with Container(classes="theme-container"):
            yield Label("Тема оформлення", classes="theme-title")
            for name in AVAILABLE_THEMES:
                suffix = " (зараз)" if name == current else ""
                yield Button(
                    make_button_label(f"{name}{suffix}", colors),
                    id=f"{BTN_PREFIX_THEME}{name}",
                )
            with Container(classes="dialog-back-container"):
                yield Button(make_button_label("Назад", colors), id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "btn-back":
            self.dismiss()
            return
        if button_id and button_id.startswith(BTN_PREFIX_THEME):
            theme = button_id[len(BTN_PREFIX_THEME):]
            if theme in AVAILABLE_THEMES:
                self.app.set_theme(theme)
                self.dismiss()
