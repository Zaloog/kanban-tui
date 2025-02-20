from datetime import datetime
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on
from textual.widget import Widget
from textual.binding import Binding
from textual.events import Mount
from textual.validation import Validator, ValidationResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Static, Label, Footer, Switch
from textual.containers import Horizontal, Vertical

from kanban_tui.classes.board import Board
from kanban_tui.widgets.modal_board_widgets import BoardList, CustomColumnList
from kanban_tui.modal.modal_task_screen import ModalConfirmScreen
from kanban_tui.database import (
    update_board_entry_db,
    get_all_columns_on_board_db,
    create_new_board_db,
    delete_board_db,
)


class ModalNewBoardScreen(ModalScreen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]
    app: "KanbanTui"

    def __init__(self, board: Board | None = None) -> None:
        self.kanban_board = board
        super().__init__()

    def _on_mount(self, event: Mount) -> None:
        # Change Names Based on Editing/ Creating a Board
        if self.kanban_board:
            self.query_exactly_one(
                "#btn_continue_new_board", Button
            ).label = "Edit Board"
            self.query_exactly_one("#label_header", Label).update("Edit Board")
            self.query_exactly_one(
                "#input_board_name", Input
            ).value = self.kanban_board.name
            self.query_exactly_one(
                "#input_board_icon", Input
            ).value = self.kanban_board.icon.strip(":")

        self.query_exactly_one("#input_board_icon", Input).border_title = "Icon"
        self.query_exactly_one("#input_board_name", Input).border_title = "Board Name"
        self.query_exactly_one("#static_preview_icon", Static).border_title = "Preview"
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
                yield Static(Text.from_markup(":books:"), id="static_preview_icon")
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
            # For later
            # initializing columns on new board
            if not self.kanban_board:
                with Horizontal(id="horizontal_custom_columns"):
                    yield Label("Use default Columns", id="label_new_column_switch")
                    yield Switch(value=True, id="switch_use_default_columns")

            yield CustomColumnList()

            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Create Board",
                    id="btn_continue_new_board",
                    variant="success",
                    disabled=True,
                )
                yield Button("Cancel", id="btn_cancel_new_board", variant="error")
            return super().compose()

    def on_switch_changed(self):
        if self.query_one(Switch).value:
            self.query_one(CustomColumnList).add_class("hidden")
        else:
            self.query_one(CustomColumnList).remove_class("hidden")
            self.due_date = None

    @on(Button.Pressed, "#btn_continue_new_board")
    def confirm_new_board(self):
        if self.kanban_board:
            self.kanban_board.name = self.query_exactly_one(
                "#input_board_name", Input
            ).value
            self.kanban_board.icon = (
                f":{self.query_exactly_one('#input_board_icon', Input).value}:"
            )
            update_board_entry_db(
                board_id=self.kanban_board.board_id,
                name=self.kanban_board.name,
                icon=self.kanban_board.icon,
                database=self.app.cfg.database_path,
            )
        else:
            new_board_name = self.query_exactly_one("#input_board_name", Input).value
            new_board_icon = self.query_exactly_one("#input_board_icon", Input).value
            if new_board_icon:
                new_board_icon = f":{new_board_icon}:"

            if self.query_exactly_one("#switch_use_default_columns").value:
                create_new_board_db(
                    name=new_board_name,
                    icon=new_board_icon,
                    database=self.app.cfg.database_path,
                )
            else:
                custom_columns = self.query_exactly_one(CustomColumnList).children
                create_new_board_db(
                    name=new_board_name,
                    icon=new_board_icon,
                    column_dict={
                        col.column_name: True
                        for col in custom_columns
                        if col.column_name
                    },
                    database=self.app.cfg.database_path,
                )

            self.app.update_board_list()
        self.dismiss(result=None)

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
                Text.from_markup(f":{event.value}:")
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
    app: "KanbanTui"
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("n", "new_board", "New Board", show=True, priority=True),
        Binding("e", "edit_board", "Edit Board", show=True, priority=True),
        Binding("d", "delete_board", "Delete Board", show=True, priority=True),
        Binding("c", "copy_board", "Copy Board", show=True, priority=True),
    ]

    def _on_mount(self, event: Mount) -> None:
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Your Boards", id="label_header")
            yield BoardList(boards=self.app.board_list)
            yield Button(
                "New Board",
                id="btn_create_board",
                variant="success",
            )

            yield Footer(show_command_palette=False)
        return super().compose()

    @on(Button.Pressed, "#btn_create_board")
    def action_new_board(self) -> None:
        self.app.push_screen(ModalNewBoardScreen(), callback=self.update_board_listview)

    def action_edit_board(self) -> None:
        highlighted_board = self.query_one(BoardList).highlighted_child.board
        self.app.push_screen(
            ModalNewBoardScreen(board=highlighted_board),
            callback=self.update_board_listview,
        )

    def action_copy_board(self) -> None:
        highlighted_board = self.query_one(BoardList).highlighted_child.board
        highlighted_board_cols = get_all_columns_on_board_db(
            board_id=highlighted_board.board_id, database=self.app.cfg.database_path
        )
        create_new_board_db(
            name=f"{highlighted_board.name}_copy",
            icon=highlighted_board.icon,
            column_dict={col.name: col.visible for col in highlighted_board_cols},
            database=self.app.cfg.database_path,
        )

        self.app.update_board_list()
        self.update_board_listview()

    def action_delete_board(self) -> None:
        highlighted_board = self.query_exactly_one(BoardList).highlighted_child.board
        if highlighted_board.board_id == self.app.cfg.active_board:
            self.notify(
                title="Can not delete the active board",
                severity="error",
                message="Please activate a different board first",
            )
            return

        self.app.push_screen(
            ModalConfirmScreen(
                text=f"Delete [blue]{highlighted_board.full_name}[/] and all its tasks?"
            ),
            callback=self.from_modal_delete_board,
        )

    def from_modal_delete_board(self, delete_yn: bool) -> None:
        highlighted_board = self.query_exactly_one(BoardList).highlighted_child.board
        if delete_yn:
            delete_board_db(
                board_id=highlighted_board.board_id, database=self.app.cfg.database_path
            )
            self.app.update_board_list()
            self.refresh(recompose=True)

    @on(BoardList.Selected)
    def activate_board(self, event: BoardList.Selected):
        active_board_id = self.app.board_list[event.list_view.index].board_id
        self.app.cfg.set_active_board(new_active_board=active_board_id)
        self.app.update_board_list()
        self.dismiss(True)

    def update_board_listview(self, result: None = None):
        self.refresh(recompose=True)

    # def action_close_boards(self):
    #     self.dismiss(True)
