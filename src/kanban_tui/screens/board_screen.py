from typing import Iterable, TYPE_CHECKING

from textual.reactive import reactive

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from rich.text import Text
from textual.widget import Widget
from textual.widgets import Header, Footer
from textual.screen import Screen
from textual.binding import Binding

from kanban_tui.classes.board import Board
from kanban_tui.views.kanbanboard_tab_view import KanbanBoard


class BoardScreen(Screen):
    app: "KanbanTui"
    active_board: reactive[Board | None] = reactive(None)

    BINDINGS = [
        Binding("ctrl+j", 'show_tab("tab_board")', "Board", priority=True),
        Binding("ctrl+k", 'show_tab("tab_overview")', "Overview", priority=True),
        Binding("ctrl+l", 'show_tab("tab_settings")', "Settings", priority=True),
    ]

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield KanbanBoard()
        yield Footer()

    def on_mount(self) -> None:
        if self.app.demo_mode:
            self.show_demo_notification()

    def watch_active_board(self):
        if self.active_board:
            border_title = Text.from_markup(
                f" [red]Active Board:[/] {self.active_board.full_name}"
            )
            self.query_one(KanbanBoard).border_title = border_title

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

    # @on(TabbedContent.TabActivated)
    # async def refresh_board(self, event: TabbedContent.TabActivated | str):
    #     # force refresh on manual refresh
    #     if isinstance(event, str):
    #         self.query_one(SettingsView).config_has_changed = True
    #         active_tab_id = event
    #     else:
    #         active_tab_id = event.tabbed_content.active
    #
    #     match active_tab_id:
    #         case "tab_board":
    #             if self.query_one(SettingsView).config_has_changed:
    #                 self.query_one(KanbanBoard).refresh(recompose=True)
    #                 self.set_timer(delay=0.15, callback=self.app.action_focus_next)
    #             self.query_one(SettingsView).config_has_changed = False
    #         case "tab_overview":
    #             if (
    #                 self.query_one("#tabbed_content_overview", TabbedContent).active
    #                 == "tab_plot"
    #             ):
    #                 await self.query_one(OverViewPlot).update_plot_by_filters()
    #                 self.query_one("#switch_plot_category_detail", Switch).focus()
    #             else:
    #                 overview_log = self.query_one(OverViewLog)
    #                 self.query_one(LogTable).load_events(
    #                     objects=overview_log.active_object_types,
    #                     events=overview_log.active_event_types,
    #                     time=overview_log.active_timestamp,
    #                 )
    #
    #                 self.query_one("#select_logdate_filter", Select).focus()
    #         case "tab_settings":
    #             self.query_one(SettingsView).refresh(recompose=True)
    #             self.set_timer(delay=0.15, callback=self.app.action_focus_next)
