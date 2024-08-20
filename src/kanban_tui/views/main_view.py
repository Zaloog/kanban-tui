from typing import Iterable

from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane, Placeholder
from textual.screen import Screen

from textual.widgets import Header, Footer
from kanban_tui.views.board_view import KanbanBoard


class MainView(Screen):
    BINDINGS = [
        ("ctrl+j", 'show_tab("tab_board")', "Board"),
        ("ctrl+k", 'show_tab("tab_overview")', "Overview"),
        ("ctrl+l", 'show_tab("tab_settings")', "Settings"),
    ]

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Footer()
        with TabbedContent():
            with TabPane("Kanban Board", id="tab_board"):
                yield KanbanBoard()
            with TabPane("Overview", id="tab_overview"):
                yield Placeholder()
            with TabPane("Settings", id="tab_settings"):
                yield Placeholder()
            return super().compose()

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab
        self.app.action_focus_next()
