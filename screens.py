"""Popup screens for Svitlo CLI application"""

__version__ = "0.44"

from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.widgets import Label, Button
from textual.screen import Screen

from core.config import (
    FIRST_RUN_TITLE, FIRST_RUN_MESSAGE, AVAILABLE_GROUPS
)
from layout.layout_manager import LayoutManager
from ui.popup_utils import make_button_label


class GroupSelectionScreen(Screen):
    """Screen for group selection on first launch"""
    
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
                    yield Button(
                        make_button_label(f"Група {g}"),
                        id=f"btn-modal-{g.replace('.', '_')}"
                    )
            with Container(classes="modal-back-container"):
                yield Button(make_button_label("Назад"), id="btn-continue")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-continue":
            from core.preferences import save_preferences, is_first_run
            from core.config import DEFAULT_GROUP
            from main import SvitloApp
            app = self.app
            
            if hasattr(app, 'current_group') and app.current_group:
                self.dismiss(app.current_group)
            elif is_first_run():
                app.current_group = DEFAULT_GROUP
                app.current_group_index = AVAILABLE_GROUPS.index(DEFAULT_GROUP)
                save_preferences(DEFAULT_GROUP, is_first_run=False)
                self.dismiss(DEFAULT_GROUP)
            else:
                self.dismiss()


class GroupSelectDialog(Screen):
    """Dialog for group selection"""
    
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
                    yield Button(
                        make_button_label(f"Група {g}"),
                        id=f"btn-group-{g.replace('.', '_')}"
                    )
            with Container(classes="dialog-back-container"):
                yield Button(make_button_label("Назад"), id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.dismiss()
        elif event.button.id and event.button.id.startswith("btn-group-"):
            group = event.button.id.replace("btn-group-", "").replace("_", ".")
            app = self.app
            if hasattr(app, 'current_group'):
                app.current_group = group
                app.current_group_index = AVAILABLE_GROUPS.index(group)
                from core.preferences import save_preferences
                save_preferences(group)
                if hasattr(app, 'update_group_button_label'):
                    app.update_group_button_label()
            self.dismiss()
