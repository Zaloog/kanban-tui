from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Button, Label, DataTable
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen

# https://github.com/1dancook/tailwind-color-picker/blob/master/src/tailwind_cp/main.py#L20-L43


class ModalCategoryManageScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
    ]

    app: "KanbanTui"
    color: reactive[str] = reactive("transparent")

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield TitleInput(placeholder="Enter Category Name")
            yield Label("Pick your Category Color")
            with Horizontal(id="horizontal_buttons"):
                yield Button(
                    "Add Category", id="btn_confirm_category", variant="success"
                )
                yield Button("Go Back", id="btn_cancel_category", variant="error")
        return super().compose()

    @on(Button.Pressed, "#btn_confirm_category")
    def create_new_category(self):
        self.dismiss(result=(self.query_one(TitleInput).value, self.color))

    @on(Button.Pressed, "#btn_cancel_category")
    def cancel_new_category(self):
        self.dismiss(result=None)

    @on(DataTable.CellHighlighted)
    def update_input_background(self, event: DataTable.CellHighlighted):
        self.color = event.data_table.get_cell_at(event.coordinate).color_value

    def watch_color(self):
        self.query_one(TitleInput).background = self.color


class TitleInput(Input):
    background: reactive[str] = reactive("black", recompose=True)

    def watch_background(self):
        self.set_styles(f"background:{self.background};")
