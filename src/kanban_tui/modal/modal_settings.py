from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.widgets.settings_widgets import AddRule


from textual import on
from textual.widget import Widget
from textual.screen import ModalScreen
from textual.widgets import Input, Button
from textual.containers import Horizontal, Vertical


class ModalNewColumnScreen(ModalScreen):
    def __init__(self, event: "AddRule.Pressed") -> None:
        self.event = event
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Input(placeholder="New Column Name")
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Create Column", id="btn_continue_delete", variant="success"
                )
                yield Button("Cancel", id="btn_cancel_delete", variant="error")
            return super().compose()

    @on(Button.Pressed, "#btn_continue_delete")
    def confirm_new_column(self):
        self.dismiss(result=(self.event, self.query_one(Input).value))

    @on(Button.Pressed, "#btn_cancel_delete")
    def cancel_new_column(self):
        self.dismiss(result=(self.event, None))
