from typing import Iterable
from datetime import datetime

from textual import on
from textual.widget import Widget
from textual.binding import Binding
from textual.events import Mount
from textual.validation import Validator, ValidationResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Static, Label, Footer
from textual.containers import Horizontal, Vertical

from kanban_tui.classes.board import Board
from kanban_tui.widgets.modal_board_widgets import BoardList


class ModalNewBoardScreen(ModalScreen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, board: Board | None = None) -> None:
        self.kanban_board = board
        super().__init__()

    def _on_mount(self, event: Mount) -> None:
        if self.kanban_board:
            self.query_one("#btn_continue_new_board", Button).label = "Edit Board"
            self.query_one("#label_header", Label).update("Edit Board")

        self.query_one("#input_board_icon", Input).border_title = "Icon"
        self.query_one("#input_board_name", Input).border_title = "Board Name"
        self.query_one("#static_preview_icon", Static).border_title = "Preview"
        # self.read_values_from_board()
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Create New Board", id="label_header")
            with Horizontal():
                yield Input(
                    placeholder="e.g. books",
                    value="",
                    id="input_board_icon",
                )
                yield Static(":books:", id="static_preview_icon")
                yield Input(
                    placeholder="Enter Board Name",
                    validate_on=["changed"],
                    validators=[ValidBoard()],
                    id="input_board_name",
                )
            yield Label(
                f"Board created at: {datetime.now().replace(microsecond=0)}",
                id="label_create_date",
            )
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
                "[gray]No Icon[/]"
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


class ModalBoardOverviewScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("n", "new_board", "New Board", show=True, priority=True),
        Binding("e", "edit_board", "Edit Board", show=True, priority=True),
    ]

    def _on_mount(self, event: Mount) -> None:
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Your Boards", id="label_header")
            yield BoardList()
            yield Button(
                "New Board",
                id="btn_create_board",
                variant="success",
            )

            yield Footer(show_command_palette=False)
        return super().compose()

    @on(Button.Pressed, "#btn_create_board")
    def action_new_board(self) -> None:
        self.app.push_screen(ModalNewBoardScreen(), callback=None)

    def action_edit_board(self) -> None:
        highlighted_board = self.query_one(BoardList).highlighted_child.board
        self.app.push_screen(
            ModalNewBoardScreen(board=highlighted_board), callback=None
        )
