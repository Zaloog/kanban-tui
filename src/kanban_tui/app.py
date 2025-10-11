from pathlib import Path
from importlib.metadata import version

from textual import on
from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Select

from kanban_tui.backends.jira.backend import JiraBackend
from kanban_tui.screens.board_screen import BoardScreen
from kanban_tui.screens.overview_screen import OverViewScreen
from kanban_tui.screens.settings_screen import SettingsScreen
from kanban_tui.config import (
    init_config,
    SETTINGS,
    Settings,
)
from kanban_tui.backends import SqliteBackend
from kanban_tui.classes.task import Task
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")
    BINDINGS = [
        Binding("f5", "refresh", "🔄Refresh", priority=True),
        Binding("ctrl+j", 'switch_screen("board")', "Board"),
        Binding("ctrl+k", 'switch_screen("overview")', "Overview"),
        Binding("ctrl+l", 'switch_screen("settings")', "Settings"),
    ]

    SCREENS = {
        "board": BoardScreen,
        "overview": OverViewScreen,
        "settings": SettingsScreen,
    }
    TITLE = f"KanbanTui v{version('kanban_tui')}"

    config_has_changed: reactive[bool] = reactive(False, init=False)
    task_list: reactive[list[Task]] = reactive([], init=False)
    board_list: reactive[list[Board]] = reactive([], init=False)
    column_list: reactive[list[Column]] = reactive([], init=False)
    active_board: reactive[Board | None] = reactive(None, init=False)

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

        self.backend.create_database()
        super().__init__()

    def get_backend(self):
        match self.config.backend.mode:
            case "sqlite":
                return SqliteBackend(self.config.backend.sqlite_settings)
            case "jira":
                return JiraBackend(self.config.backend.jira_settings)
            case _:
                raise NotImplementedError("Only sqlite Backend is supported for now")

    async def on_mount(self) -> None:
        self.theme = self.config.board.theme
        self.update_board_list()

        screen = self.get_screen("board").data_bind(KanbanTui.active_board)
        await self.push_screen(screen)

        if self.demo_mode:
            self.show_demo_notification()

    def show_demo_notification(self):
        self.title = f"{self.TITLE} (Demo Mode)"
        pop_up_msg = "Using a temporary Database and Config. Kanban-Tui will delete those after closing the app when not using [green]--keep[/]."
        if self.task_list:
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

    @on(Select.Changed, "#select_backend_mode")
    def update_backend(self, event: Select.Changed):
        self.backend = self.get_backend()
        self.update_board_list()
        self.get_screen("board", BoardScreen).refresh(recompose=True)

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
        await self.screen.update_board()

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

    def watch_config_has_changed(self):
        self.notify(f"config changed: {self.config_has_changed}")

    @property
    def visible_column_dict(self) -> dict[int, str]:
        return {col.column_id: col.name for col in self.column_list if col.visible}

    @property
    def visible_task_list(self) -> list[Task]:
        return [
            task for task in self.task_list if task.column in self.visible_column_dict
        ]
