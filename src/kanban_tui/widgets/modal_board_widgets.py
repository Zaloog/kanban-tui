from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import ListView, ListItem, Label, Rule
from textual.containers import Horizontal

from kanban_tui.classes.board import Board
from kanban_tui.database import get_all_board_infos
from kanban_tui.utils import get_days_left_till_due


class BoardList(ListView):
    app: "KanbanTui"

    BINDINGS = [
        Binding(key="j", action="cursor_down", show=False),
        Binding(key="k", action="cursor_up", show=False),
    ]

    def __init__(self, boards: list[Board]) -> None:
        self.info_dict = {
            board["board_id"]: board
            for board in get_all_board_infos(database=self.app.cfg.database_path)
        }
        children = [
            BoardListItem(board=board, info_dict=self.info_dict[board.board_id])
            for board in boards
        ]

        # get index of active board to set as active index
        for board_index, board in enumerate(self.app.board_list):
            if board.board_id == self.app.cfg.active_board:
                initial_index = board_index

        super().__init__(*children, initial_index=initial_index, id="board_list")

    def on_mount(self):
        self.focus()


class BoardListItem(ListItem):
    app: "KanbanTui"

    def __init__(self, board: Board, info_dict: dict) -> None:
        self.board = board
        self.amount_tasks = info_dict.get("amount_tasks")
        self.next_due = get_days_left_till_due(info_dict.get("next_due"))

        super().__init__(id=f"listitem_board_{self.board.board_id}")

    def compose(self) -> Iterable[Widget]:
        if self.board.board_id == self.app.cfg.active_board:
            self.styles.background = "green"
        with Horizontal():
            yield Label(self.board.full_name)
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

        return super().compose()
