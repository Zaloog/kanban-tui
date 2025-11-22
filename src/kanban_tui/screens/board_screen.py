from typing import Iterable, TYPE_CHECKING

from kanban_tui.config import Backends
from kanban_tui.modal.modal_auth_screen import ModalAuthScreen

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on, work
from textual.reactive import reactive
from textual.widget import Widget
from textual.events import ScreenResume
from textual.widgets import Header
from textual.screen import Screen

from kanban_tui.classes.board import Board
from kanban_tui.widgets.board_widgets import KanbanBoard
from kanban_tui.widgets.custom_widgets import KanbanTuiFooter


class BoardScreen(Screen):
    app: "KanbanTui"
    active_board: reactive[Board | None] = reactive(None, init=False)

    def compose(self) -> Iterable[Widget]:
        yield KanbanBoard()
        yield Header()
        yield KanbanTuiFooter()

    def watch_active_board(self):
        if self.active_board:
            border_title = Text.from_markup(
                f" [red]Active Board:[/] {self.active_board.full_name}"
            )
            self.query_one(KanbanBoard).border_title = border_title

    async def ensure_active_board(self):
        if not self.active_board:
            await self.query_one(KanbanBoard).action_show_boards()

    async def ensure_api_key(self):
        if not self.app.backend.api_key:
            await self.app.push_screen_wait(ModalAuthScreen())

    @work()
    @on(ScreenResume)
    async def load_kanban_board(self, event: ScreenResume | None = None):
        self.set_reactive(BoardScreen.active_board, self.app.active_board)

        match self.app.config.backend.mode:
            case Backends.JIRA:
                await self.ensure_api_key()

        await self.ensure_active_board()

        if self.app.needs_refresh:
            self.app.update_task_list()
            await self.query_one(KanbanBoard).populate_board()
            self.app.needs_refresh = False
