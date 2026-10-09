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
    DEFAULT_GROUP,
    FIRST_RUN_MESSAGE,
    FIRST_RUN_TITLE,
)
from core.preferences import save_preferences
from core.utils import button_id_from_group, parse_group_from_button_id
from layout.layout_manager import LayoutManager
from ui.popup_utils import make_button_label


def _make_group_button(group: str, prefix: str = BTN_PREFIX_MODAL) -> Button:
    return Button(
        make_button_label(f"Група {group}"),
        id=button_id_from_group(group, prefix)
    )


class GroupSelectionScreen(Screen):
    """Screen for group selection on first launch."""

    CSS = """
    GroupSelectionScreen {
        align: center middle;
    }

    .modal-container {
        width: auto;
        height: auto;
        border: solid #D96800;
        background: #1a1a1a;
        padding: 1;
        align: center middle;
    }

    .modal-title {
        text-style: bold;
        color: #D96800;
        margin-bottom: 1;
        align: center middle;
    }

    .modal-message {
        color: #888;
        margin-bottom: 1;
        align: center middle;
    }

    .modal-back-container {
        layout: horizontal;
        align: center middle;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        layout_type = LayoutManager.get_layout_type(self.app.size.width, self.app.size.height)
        config = LayoutManager.get_config(layout_type)
        grid_class = f"modal-grid grid-cols-{config['popup_columns']}"

        with Container(classes="modal-container"):
            yield Label(FIRST_RUN_TITLE, classes="modal-title")
            yield Label(FIRST_RUN_MESSAGE, classes="modal-message")
            with Grid(classes=grid_class):
                for g in AVAILABLE_GROUPS:
                    yield _make_group_button(g, BTN_PREFIX_MODAL)
            with Container(classes="modal-back-container"):
                yield Button(make_button_label("Далі"), id="btn-continue")

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

    CSS = """
    GroupSelectDialog {
        align: center middle;
    }

    .dialog-overlay {
        background: rgba(0, 0, 0, 0.8);
    }

    .dialog-container {
        width: auto;
        height: auto;
        border: solid #D96800;
        background: #1a1a1a;
        padding: 1;
        align: center middle;
    }

    .dialog-title {
        text-style: bold;
        color: #D96800;
        margin-bottom: 1;
        align: center middle;
    }

    .dialog-back-container {
        layout: horizontal;
        align: center middle;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        layout_type = LayoutManager.get_layout_type(self.app.size.width, self.app.size.height)
        config = LayoutManager.get_config(layout_type)
        grid_class = f"dialog-grid grid-cols-{config['popup_columns']}"

        with Container(classes="dialog-container"):
            yield Label("Оберіть групу", classes="dialog-title")
            with Grid(classes=grid_class):
                for g in AVAILABLE_GROUPS:
                    yield _make_group_button(g, BTN_PREFIX_GROUP)
            with Container(classes="dialog-back-container"):
                yield Button(make_button_label("Пошук за адресою"), id="btn-address-search")
                yield Button(make_button_label("Назад"), id="btn-back")

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

    CSS = """
    AddressLookupDialog {
        align: center middle;
    }

    .lookup-container {
        width: 60;
        height: auto;
        border: solid #D96800;
        background: #1a1a1a;
        padding: 1;
    }

    .lookup-title {
        text-style: bold;
        color: #D96800;
        margin-bottom: 1;
        align: center middle;
    }

    #street-input {
        margin-bottom: 1;
    }

    #results-area {
        height: 8;
        border: solid #333;
        margin-bottom: 1;
        padding: 1;
    }

    .lookup-actions {
        layout: horizontal;
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(classes="lookup-container"):
            yield Label("Пошук групи за вулицею / районом", classes="lookup-title")
            yield Input(placeholder="Введіть назву вулиці (напр. Стрийська)...", id="street-input")
            yield Static("Введіть назву вулиці для пошуку відповідної групи...", id="results-area")
            with Container(classes="lookup-actions"):
                yield Button(make_button_label("Закрити"), id="btn-close-lookup")

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value
        results = search_address(query)
        results_widget = self.query_one("#results-area", Static)
        if not query:
            results_widget.update("Введіть назву вулиці для пошуку відповідної групи...")
        elif not results:
            results_widget.update(f"За запитом '{query}' груп не знайдено.")
        else:
            lines = [f"[bold]{r['street']}[/bold] ({r['district']} р-н) -> [bold yellow]Група {r['group']}[/bold yellow]" for r in results]
            results_widget.update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-lookup":
            self.dismiss()


class HelpDialog(Screen):
    """Dialog showing keyboard shortcuts and app guide."""

    CSS = """
    HelpDialog {
        align: center middle;
    }

    .help-container {
        width: 60;
        height: auto;
        border: solid #D96800;
        background: #1a1a1a;
        padding: 1;
    }

    .help-title {
        text-style: bold;
        color: #D96800;
        margin-bottom: 1;
        align: center middle;
    }

    .help-text {
        color: #ccc;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        help_content = (
            "[bold #D96800]Гарячі клавіші:[/bold #D96800]\n"
            "  [bold]r[/bold] - Оновити дані з сайту\n"
            "  [bold]t[/bold] - Переключити розклад (Сьогодні / Завтра)\n"
            "  [bold]g[/bold] - Відкрити вибір групи\n"
            "  [bold]e[/bold] - Експортувати розклад в календар (.ics)\n"
            "  [bold]f[/bold] - Переключити обрану групу (Favorites)\n"
            "  [bold]?[/bold] або [bold]h[/bold] - Довідка\n"
            "  [bold]q[/bold] - Вийти з програми\n\n"
            "[bold #D96800]Позначення:[/bold #D96800]\n"
            "  [#50fa7b]■[/#50fa7b] - Світло є\n"
            "  [#ff5555]□[/#ff5555] - Світла немає\n"
            "  [bold yellow]▲[/#bold yellow] - Поточний час"
        )
        with Container(classes="help-container"):
            yield Label("Довідка Svitlo CLI", classes="help-title")
            yield Static(help_content, classes="help-text")
            yield Button(make_button_label("Зрозуміло"), id="btn-close-help")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-help":
            self.dismiss()
