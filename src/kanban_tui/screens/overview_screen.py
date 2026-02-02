from typing import Iterable

from textual import on
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Header
from textual.screen import Screen
from textual.events import ScreenResume

from kanban_tui.widgets.overview_widgets import OverView
from kanban_tui.widgets.custom_widgets import KanbanTuiFooter


class OverViewScreen(Screen):
    BINDINGS = [
        Binding(
            "escape",
            "back_to_board",
            "Back",
            key_display="esc/^j",
            priority=True,
        ),
        Binding("ctrl+j", "back_to_board", "Board", show=False, priority=True),
    ]

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield OverView()
        yield KanbanTuiFooter()

    @on(ScreenResume)
    async def refresh_page(self):
        await self.query_one(OverView).recompose()
        self.app.action_focus_next()

    def action_back_to_board(self) -> None:
        self.app.switch_screen("board")
