from typing import Iterable

from textual.events import Mount
from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane, Header, Footer
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets.tabbed_content import ContentTabs

from kanban_tui.views.kanbanboard_tab_view import KanbanBoard
from kanban_tui.views.overview_tab_view import OverView
from kanban_tui.views.settings_tab_view import SettingsView


class MainView(Screen):
    BINDINGS = [
        Binding("ctrl+j", 'show_tab("tab_board")', "Board"),
        Binding("ctrl+k", 'show_tab("tab_overview")', "Overview"),
        Binding("ctrl+l", 'show_tab("tab_settings")', "Settings"),
    ]

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Footer()
        with TabbedContent():
            with TabPane("Kanban Board", id="tab_board"):
                yield KanbanBoard()
            with TabPane("Overview", id="tab_overview"):
                yield OverView()
            with TabPane("Settings", id="tab_settings"):
                yield SettingsView()
            return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one(ContentTabs).can_focus = False
        return super()._on_mount(event)

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab
        # self.app.action_focus_next()
