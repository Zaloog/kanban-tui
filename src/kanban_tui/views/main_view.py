from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
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
    app: "KanbanTui"
    BINDINGS = [
        Binding("ctrl+j", 'show_tab("tab_board")', "Board", priority=True),
        Binding("ctrl+k", 'show_tab("tab_overview")', "Overview", priority=True),
        Binding("ctrl+l", 'show_tab("tab_settings")', "Settings", priority=True),
    ]

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Footer()
        with TabbedContent(initial="tab_board"):
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
        self.app.action_focus_next()

    @on(TabbedContent.TabActivated)
    async def refresh_board(self, event: TabbedContent.TabActivated):
        if event.tab.id == "--content-tab-tab_board":
            if self.query_one(SettingsView).config_has_changed:
                self.query_one(KanbanBoard).refresh(recompose=True)
                self.set_timer(delay=0.2, callback=self.app.action_focus_next)
            self.query_one(SettingsView).config_has_changed = False
        elif event.tab.id == "--content-tab-tab_overview":
            await self.query_one(OverView).update_plot_by_filters()
