from typing import Iterable

from textual import on
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label
from textual.widget import Widget


class ModalConfirmScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, text: str) -> None:
        self.display_text = text
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label(self.display_text)
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Confirm Delete", id="btn_continue_delete", variant="success"
                )
                yield Button("Cancel Delete", id="btn_cancel_delete", variant="error")

    @on(Button.Pressed, "#btn_continue_delete")
    def confirm_delete(self):
        self.dismiss(result=True)

    @on(Button.Pressed, "#btn_cancel_delete")
    def cancel_delete(self):
        self.dismiss(result=False)
