from typing import Iterable

from textual import on
from textual.widget import Widget
from textual.widgets import Header
from textual.screen import Screen
from textual.events import ScreenResume

from kanban_tui.widgets.overview_widgets import OverView
from kanban_tui.widgets.custom_widgets import KanbanTuiFooter


class OverViewScreen(Screen):
    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield OverView()
        yield KanbanTuiFooter()

    @on(ScreenResume)
    def refresh_page(self):
        self.query_one(OverView).refresh(recompose=True)
