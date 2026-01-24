from __future__ import annotations
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on
from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label, Rule, Button, Input
from textual.containers import Horizontal, VerticalScroll

from kanban_tui.classes.board import Board
from kanban_tui.utils import get_days_left_till_due


class BoardList(ListView):
    app: "KanbanTui"

    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
    ]

    def on_mount(self):
        self.focus()

    def __init__(self) -> None:
        board_listitems = self.get_board_list_items()
        initial_index = self.get_initial_index()
        super().__init__(*board_listitems, initial_index=initial_index, id="board_list")

    async def populate_widget(self, index: int | None = None):
        await self.clear()
        board_listitems = self.get_board_list_items()
        await self.extend(board_listitems)
        self.index = index
        self.refresh_bindings()

    def get_initial_index(self) -> int | None:
        for board_index, board in enumerate(self.app.board_list):
            if board.board_id == self.app.active_board.board_id:
                return board_index
        return None

    def get_board_list_items(self) -> list[BoardListItem]:
        info_dict = {
            board_info["board_id"]: board_info
            for board_info in self.app.backend.get_board_infos()
        }
        return [
            BoardListItem(board=board, info_dict=info_dict[board.board_id])
            for board in self.app.board_list
        ]


class BoardListItem(ListItem):
    app: "KanbanTui"

    def __init__(self, board: Board, info_dict: dict) -> None:
        self.board = board
        self.amount_tasks = info_dict.get("amount_tasks")
        self.amount_columns = info_dict.get("amount_columns")
        self.next_due = get_days_left_till_due(info_dict.get("next_due"))

        super().__init__(id=f"listitem_board_{self.board.board_id}")

    def compose(self) -> Iterable[Widget]:
        if self.board.board_id == self.app.active_board.board_id:
            self.add_class("active")
        with Horizontal():
            yield Label(Text.from_markup(self.board.full_name))
            yield Rule(orientation="vertical")
            yield Label(f"Columns: {self.amount_columns}")
            yield Rule(orientation="vertical")
            yield Label(f"Tasks: {self.amount_tasks}")
            yield Rule(orientation="vertical")
            match self.next_due:
                case 0:
                    due_string = "Tasks [red]Overdue[/]"
                case 1:
                    due_string = "Next Task due tomorrow"
                case None:
                    due_string = "[green]No Due Date here[/]"
                case _:
                    due_string = f"Next Task due in [yellow]{self.next_due}[/] days"
            yield Label(due_string)


class CustomColumnList(VerticalScroll):
    app: "KanbanTui"
    can_focus = False

    async def on_mount(self):
        await self.mount(NewColumnItem())
        self.display = False

    @on(Input.Changed)
    async def add_new_empty_column(self, event: Input.Changed):
        if event.input.value and self.children[-1].column_name:
            await self.mount(NewColumnItem())
            self.scroll_down(animate=False)
        if (not event.input.value) & (not self.children[-1].column_name):
            self.remove_children(self.children[-1:])

    @property
    def column_dict(self):
        return {
            column.column_name: True for column in self.children if column.column_name
        }


class NewColumnItem(Horizontal):
    column_name: reactive[str] = reactive("", init=False)

    def compose(self) -> Iterable[Widget]:
        yield Input(placeholder="Enter New Column Name")
        yield Button("Delete", variant="error", disabled=True)

    def on_input_changed(self, event: Input.Changed):
        self.column_name = event.input.value

    def watch_column_name(self):
        if self.column_name:
            self.query_one(Button).disabled = False
        else:
            self.query_one(Button).disabled = True

    def on_button_pressed(self):
        self.remove()
