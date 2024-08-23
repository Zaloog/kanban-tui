from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Button, Placeholder
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen


class CategoryColorPicker(ModalScreen):
    app: "KanbanTui"
    color: reactive[str]

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Input(placeholder="Enter Category Name")
            yield Placeholder("Colorpicker")
            with Horizontal(id="horizontal_buttons"):
                yield Button(
                    "Add Category", id="btn_confirm_category", variant="success"
                )
                yield Button("Go Back", id="btn_cancel_category", variant="error")
        return super().compose()

    @on(Button.Pressed, "#btn_confirm_category")
    def create_new_category(self):
        self.app.pop_screen()

    @on(Button.Pressed, "#btn_cancel_category")
    def cancel_new_category(self):
        self.dismiss(result=None)
