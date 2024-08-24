from typing import Iterable

from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane
from textual.screen import Screen

from textual.widgets import Header, Footer
from textual.binding import Binding
from kanban_tui.views.kanbanboard_tab_view import KanbanBoard
from kanban_tui.views.overview_tab_view import OverView
from kanban_tui.views.settings_tab_view import SettingsView
from kanban_tui.widgets.filter_sidebar import FilterOverlay


class MainView(Screen):
    BINDINGS = [
        Binding("ctrl+j", 'show_tab("tab_board")', "Board"),
        Binding("ctrl+k", 'show_tab("tab_overview")', "Overview"),
        Binding("ctrl+l", 'show_tab("tab_settings")', "Settings"),
        Binding("f1", "toggle_filter", "Filter"),
    ]

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Footer()
        yield FilterOverlay(classes="-hidden")
        with TabbedContent():
            with TabPane("Kanban Board", id="tab_board"):
                yield KanbanBoard()
            with TabPane("Overview", id="tab_overview"):
                yield OverView()
            with TabPane("Settings", id="tab_settings"):
                yield SettingsView()
            return super().compose()

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab
        # self.app.action_focus_next()

    def action_toggle_filter(self) -> None:
        filter = self.query_one(FilterOverlay)
        self.set_focus(None)
        if filter.has_class("-hidden"):
            filter.remove_class("-hidden")
        else:
            if filter.query("*:focus"):
                self.screen.set_focus(None)
            filter.add_class("-hidden")
