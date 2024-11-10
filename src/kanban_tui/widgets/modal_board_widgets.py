from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label

from kanban_tui.classes.board import Board

# Or use Datatable?


class BoardList(ListView):
    app: "KanbanTui"

    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
    ]

    def __init__(self, boards: list[Board]) -> None:
        children = [BoardListItem(board=board) for board in boards]
        initial_index = self.app.cfg.active_board - 1

        super().__init__(*children, initial_index=initial_index, id="board_list")

    def on_mount(self):
        self.focus()


class BoardListItem(ListItem):
    app: "KanbanTui"

    def __init__(self, board: Board) -> None:
        self.board = board
        super().__init__(id=f"listitem_board_{self.board.board_id}")

    def compose(self) -> Iterable[Widget]:
        if self.board.board_id == self.app.cfg.active_board:
            self.styles.background = "green"
        yield Label(self.board.full_name)

        return super().compose()
