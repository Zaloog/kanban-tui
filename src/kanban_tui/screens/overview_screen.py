from typing import Iterable

from textual.widget import Widget
from textual.widgets import Header
from textual.screen import Screen

from kanban_tui.widgets.overview_widgets import OverView
from kanban_tui.widgets.custom_widgets import KanbanTuiFooter


class OverViewScreen(Screen):
    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield KanbanTuiFooter()
        yield OverView()
