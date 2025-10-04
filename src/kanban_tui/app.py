from pathlib import Path

from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import TabbedContent

from kanban_tui.views.main_view import MainView
from kanban_tui.config import (
    init_config,
    SETTINGS,
    Settings,
)
from kanban_tui.backends import SqliteBackend
from kanban_tui.backends.sqlite.database import (
    init_new_db,
    init_first_board,
)
from kanban_tui.classes.task import Task
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")
    BINDINGS = [
        Binding("f5", "refresh", "🔄Refresh", priority=True),
    ]

    SCREENS = {"MainView": MainView}

    task_list: reactive[list[Task]] = reactive([], init=False)
    board_list: reactive[list[Board]] = reactive([], init=False)
    column_list: reactive[list[Column]] = reactive([], init=False)
    active_board: reactive[Board | None] = reactive(None)

    def __init__(
        self,
        config_path: str,
        database_path: str,
        demo_mode: bool = False,
    ) -> None:
        SETTINGS.set(Settings())
        init_config(config_path=config_path, database=database_path)
        self.config = SETTINGS.get()
        self.backend = self.get_backend()
        self.demo_mode = demo_mode

        init_new_db(database=self.config.backend.sqlite_settings.database_path)
        init_first_board(database=self.config.backend.sqlite_settings.database_path)
        super().__init__()

    def get_backend(self):
        match self.config.backend.mode:
            case "sqlite":
                return SqliteBackend(self.config.backend.sqlite_settings)
            case "jira":
                raise NotImplementedError("Jira Backend is not supported yet")
            case _:
                raise NotImplementedError("Only sqlite Backend is supported for now")

    def on_mount(self) -> None:
        self.theme = self.config.board.theme
        self.update_board_list()
        self.push_screen(MainView().data_bind(KanbanTui.active_board))

    def update_board_list(self):
        self.board_list = self.backend.get_boards()

    def watch_board_list(self):
        self.active_board = self.backend.active_board

    def watch_active_board(self):
        if self.active_board:
            self.app.config.set_active_board(
                new_active_board_id=self.active_board.board_id
            )
            self.update_column_list()

    def watch_column_list(self):
        self.update_task_list()

    def watch_theme(self, theme: str):
        self.config.set_theme(theme)

    async def action_refresh(self):
        self.update_board_list()
        self.watch_active_board()
        self.watch_column_list()
        active_tab = self.screen.query_one(TabbedContent).active_pane.id
        await self.screen.refresh_board(event=active_tab)

    def update_task_list(self):
        self.task_list = self.backend.get_tasks_on_active_board()

    def update_column_list(self):
        self.column_list = self.backend.get_columns()

    def get_possible_next_column_id(self, current_id: int) -> int:
        column_id_list = list(self.visible_column_dict.keys())
        if column_id_list[-1] == current_id:
            return current_id
        return column_id_list[column_id_list.index(current_id) + 1]

    def get_possible_previous_column_id(self, current_id: int) -> int:
        column_id_list = list(self.visible_column_dict.keys())
        if column_id_list[0] == current_id:
            return current_id
        return column_id_list[column_id_list.index(current_id) - 1]

    @property
    def visible_column_dict(self) -> dict[int, str]:
        return {col.column_id: col.name for col in self.column_list if col.visible}

    @property
    def visible_task_list(self) -> list[Task]:
        return [
            task for task in self.task_list if task.column in self.visible_column_dict
        ]
