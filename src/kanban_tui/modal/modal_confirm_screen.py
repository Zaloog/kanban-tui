from typing import Iterable

from textual import on
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Label
from textual.widget import Widget

from kanban_tui.widgets.custom_widgets import ButtonRow


class ModalConfirmScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, text: str, button_text: str) -> None:
        self.display_text = text
        self.button_text = button_text
        super().__init__()

    def on_mount(self):
        self.query_one(Button).label = self.button_text

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label(self.display_text)
            yield ButtonRow(id="horizontal_buttons")

    @on(Button.Pressed, "#btn_continue")
    def confirm_delete(self):
        self.dismiss(result=True)

    @on(Button.Pressed, "#btn_cancel")
    def cancel_delete(self):
        self.dismiss(result=False)
