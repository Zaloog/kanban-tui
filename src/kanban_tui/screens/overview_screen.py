from typing import Iterable

from textual.widget import Widget
from textual.widgets import Header, Footer
from textual.screen import Screen

from kanban_tui.widgets.overview_widgets import OverView


class OverViewScreen(Screen):
    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Footer()
        yield OverView()
