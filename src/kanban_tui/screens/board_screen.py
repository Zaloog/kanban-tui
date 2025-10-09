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
from kanban_tui.views.kanbanboard_tab_view import KanbanBoard


class BoardScreen(Screen):
    app: "KanbanTui"
    active_board: reactive[Board | None] = reactive(None)

    def compose(self) -> Iterable[Widget]:
        yield KanbanBoard()
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        if self.app.demo_mode:
            self.show_demo_notification()

    def watch_active_board(self):
        if self.active_board:
            border_title = Text.from_markup(
                f" [red]Active Board:[/] {self.active_board.full_name}"
            )
            self.query_one(KanbanBoard).border_title = border_title

    def show_demo_notification(self):
        self.title = "Kanban-Tui (Demo Mode)"
        pop_up_msg = "Using a temporary Database and Config. Kanban-Tui will delete those after closing the app when not using [green]--keep[/]."
        if self.app.task_list:
            self.notify(
                title="Demo Mode active",
                message=pop_up_msg
                + " For a clean demo pass the [green]--clean[/] flag",
                severity="warning",
            )
        else:
            self.notify(
                title="Demo Mode active (clean)",
                message=pop_up_msg,
                severity="warning",
            )

    @on(ScreenResume)
    def update_board(self):
        if self.app.config_has_changed:
            self.notify("updated")
            self.query_one(KanbanBoard).refresh_on_board_change()
            self.watch_active_board()
            self.app.config_has_changed = False
