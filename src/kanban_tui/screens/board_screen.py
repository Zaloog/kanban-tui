from typing import Iterable, TYPE_CHECKING

from textual.reactive import reactive


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from rich.text import Text
from textual.widget import Widget
from textual.events import ScreenResume
from textual.widgets import Header, Footer
from textual.screen import Screen

from kanban_tui.classes.board import Board
from kanban_tui.widgets.board_widgets import KanbanBoard


class BoardScreen(Screen):
    app: "KanbanTui"
    active_board: reactive[Board | None] = reactive(None, init=False)

    def compose(self) -> Iterable[Widget]:
        yield KanbanBoard()
        yield Header()
        yield Footer()

    def on_mount(self):
        self.set_reactive(BoardScreen.active_board, self.app.active_board)
        if not self.active_board:
            self.query_one(KanbanBoard).action_show_boards()

    def watch_active_board(self):
        if self.active_board:
            border_title = Text.from_markup(
                f" [red]Active Board:[/] {self.active_board.full_name}"
            )
            self.query_one(KanbanBoard).border_title = border_title

    @on(ScreenResume)
    async def update_board(self):
        self.watch_active_board()
        if self.app.config_has_changed:
            self.query_one(KanbanBoard).refresh_on_board_change()
            self.app.config_has_changed = False
