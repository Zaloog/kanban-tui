from typing import Iterable
from pathlib import Path

from textual.app import App
from textual.widget import Widget
from textual.widgets import Header, Footer

from kanban_tui.views.board_view import KanbanBoard


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield KanbanBoard()
        yield Footer()
        return super().compose()
