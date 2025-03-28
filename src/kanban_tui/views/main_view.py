from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane, Header, Footer
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets.tabbed_content import ContentTabs

from kanban_tui.views.kanbanboard_tab_view import KanbanBoard
from kanban_tui.views.overview_tab_view import (
    OverView,
    OverViewLog,
    OverViewPlot,
    LogTable,
)
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
        with TabbedContent(initial="tab_board", id="tabbed_content_boards"):
            with TabPane("Kanban Board [yellow on black]^j[/]", id="tab_board"):
                yield KanbanBoard()
            with TabPane("Overview [yellow on black]^k[/]", id="tab_overview"):
                yield OverView()
            with TabPane("Settings [yellow on black]^l[/]", id="tab_settings"):
                yield SettingsView()
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one(ContentTabs).can_focus = False
        if self.app.demo_mode:
            self.show_demo_notification()
        self.app.screen.query_one(
            "#tabbed_content_boards"
        ).border_title = Text.from_markup(
            f" [red]Active Board:[/] {self.app.active_board.full_name}"
        )
        return super()._on_mount(event)

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab
        self.app.action_focus_next()

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

    @on(TabbedContent.TabActivated)
    async def refresh_board(self, event: TabbedContent.TabActivated | str):
        # force refresh on manual refresh
        if isinstance(event, str):
            self.query_one(SettingsView).config_has_changed = True
            active_tab_id = event
        else:
            active_tab_id = event.tabbed_content.active

        match active_tab_id:
            case "tab_board":
                if self.query_one(SettingsView).config_has_changed:
                    self.query_one(KanbanBoard).refresh(recompose=True)
                    self.set_timer(delay=0.15, callback=self.app.action_focus_next)
                self.query_one(SettingsView).config_has_changed = False
            case "tab_overview":
                if self.query_one("#tabbed_content_overview").active == "tab_plot":
                    await self.query_one(OverViewPlot).update_plot_by_filters()
                    self.query_one("#switch_plot_category_detail").focus()
                else:
                    overview_log = self.query_one(OverViewLog)
                    self.query_one(LogTable).load_events(
                        objects=overview_log.active_object_types,
                        events=overview_log.active_event_types,
                        time=overview_log.active_timestamp,
                    )

                    self.query_one("#select_logdate_filter").focus()
            case "tab_settings":
                self.query_one(SettingsView).refresh(recompose=True)
                self.set_timer(delay=0.25, callback=self.app.action_focus_next)
