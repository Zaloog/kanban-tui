from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label

from kanban_tui.classes.board import Board

# Or use Datatable?


class BoardList(VerticalScroll):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.id = "board_list"

        yield ListView(
            *[BoardListItem(board=board) for board in self.app.board_list],
        )

        return super().compose()

    def on_mount(self):
        self.query_one(ListView).index = None


class BoardListItem(ListItem):
    def __init__(self, board: Board) -> None:
        self.board = board
        super().__init__(id=f"listitem_board_{self.board.board_id}")

    def compose(self) -> Iterable[Widget]:
        yield Label(self.board.name)

        return super().compose()
