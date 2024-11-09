from typing import Iterable

from textual import on
from textual.widget import Widget
from textual.binding import Binding
from textual.events import Mount
from textual.validation import Validator, ValidationResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Static, Label
from textual.containers import Horizontal, Vertical

from kanban_tui.classes.board import Board
from kanban_tui.widgets.modal_task_widgets import CreationDateInfo


class ModalNewBoardScreen(ModalScreen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, board: Board | None = None) -> None:
        self.kanban_board = board
        super().__init__()

    def _on_mount(self, event: Mount) -> None:
        if self.kanban_board:
            self.query_one("#btn_continue_new_board", Button).label = "Edit Board"
            self.query_one("#label_header", Label).update("Edit Board")
            self.read_values_from_task()
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Create New Board", id="label_header")
            with Horizontal():
                yield Input(
                    placeholder="Icon",
                    value="books",
                    # validate_on=["changed"],
                    # validators=[ValidBoard()],
                    id="input_board_icon",
                )
                yield Static(id="static_preview_icon")
                yield Input(
                    placeholder="New Board Name",
                    validate_on=["changed"],
                    validators=[ValidBoard()],
                    id="input_board_name",
                )
            yield CreationDateInfo()
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Create Board",
                    id="btn_continue_new_board",
                    variant="success",
                    disabled=True,
                )
                yield Button("Cancel", id="btn_cancel_new_board", variant="error")
            return super().compose()

    @on(Button.Pressed, "#btn_continue_new_board")
    def confirm_new_board(self):
        self.dismiss(result=(self.query_one(Input).value))

    @on(Button.Pressed, "#btn_cancel_new_board")
    def cancel_new_board(self):
        self.dismiss(result=None)

    @on(Input.Changed, "#input_board_name")
    def check_if_board_name_valid(self, event: Input.Changed):
        self.query_exactly_one(
            "#btn_continue_new_board", Button
        ).disabled = not event.validation_result.is_valid

    @on(Input.Changed, "#input_board_icon")
    def check_if_board_icon_can_is_empty(self, event: Input.Changed):
        if event.value:
            self.query_exactly_one("#static_preview_icon", Static).update(
                f":{event.value}:"
            )
        else:
            self.query_exactly_one("#static_preview_icon", Static).update(
                "[gray]Preview[/]"
            )


class ValidBoard(Validator):
    def validate(self, value: str) -> ValidationResult:
        """Check if string is not empty"""
        if self.is_empty(value=value):
            return self.failure("Empty board names are not allowed")
        return self.success()

    @staticmethod
    def is_empty(value: str) -> bool:
        return value == ""
