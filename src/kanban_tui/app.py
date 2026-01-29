from __future__ import annotations
from pathlib import Path
from importlib.metadata import version

from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Select

from kanban_tui.modal.modal_auth_screen import ModalAuthScreen
from kanban_tui.screens.board_screen import BoardScreen
from kanban_tui.screens.overview_screen import OverViewScreen
from kanban_tui.screens.settings_screen import SettingsScreen
from kanban_tui.config import (
    Backends,
    init_config,
    SETTINGS,
    Settings,
)
from kanban_tui.backends import SqliteBackend
from kanban_tui.classes.task import Task
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column
from kanban_tui.widgets.custom_widgets import KanbanTuiFooter


class KanbanTui(App[str | None]):
    CSS_PATH = Path("assets/style.tcss")
    BINDINGS = [
        Binding("r", "refresh", "🔄Refresh", priority=True),
        Binding("ctrl+j", 'switch_screen("board")', "Board"),
        Binding("ctrl+k", 'switch_screen("overview")', "Overview"),
        Binding("ctrl+l", 'switch_screen("settings")', "Settings"),
        Binding("C", "show_backend_selector", show=False, priority=True),
    ]

    SCREENS = {
        "board": BoardScreen,
        "overview": OverViewScreen,
        "settings": SettingsScreen,
    }
    TITLE = "kanban-tui"

    SUB_TITLE = f"v{version('kanban_tui')}"

    needs_refresh: reactive[bool] = reactive(False, init=False)
    task_list: reactive[list[Task]] = reactive([], init=False)
    board_list: reactive[list[Board]] = reactive([], init=False)
    column_list: reactive[list[Column]] = reactive([], init=False)
    active_board: reactive[Board | None] = reactive(None, init=False)

    def __init__(
        self,
        config_path: str,
        database_path: str,
        demo_mode: bool = False,
        auth_only: bool = False,
        *args,
        **kwargs,
    ) -> None:
        init_config(config_path=config_path, database=database_path)
        SETTINGS.set(Settings())
        super().__init__(*args, **kwargs)
        self.config = SETTINGS.get()
        self.demo_mode = demo_mode
        self.auth_only = auth_only
        self.backend = self.get_backend()

    def get_backend(self):
        match self.config.backend.mode:
            case Backends.SQLITE:
                backend = SqliteBackend(self.config.backend.sqlite_settings)
            case Backends.JIRA:
                from kanban_tui.backends.jira.backend import JiraBackend

                backend = JiraBackend(self.config.backend.jira_settings)
            case Backends.CLAUDE:
                from kanban_tui.backends.claude.backend import ClaudeBackend

                backend = ClaudeBackend(self.config.backend.claude_settings)
            case _:
                raise NotImplementedError(
                    "Only sqlite, jira, and claude backends are supported"
                )

        return backend

    @work()
    async def on_mount(self) -> None:
        # self.set_interval(10, self.action_refresh)
        self.theme = self.config.board.theme

        if self.auth_only:
            await self.show_auth_screen_only()
            return

        if self.demo_mode:
            self.show_demo_notification()

        self.update_board_list()

        screen = self.get_screen("board").data_bind(KanbanTui.active_board)
        await self.push_screen(screen)

    async def show_auth_screen_only(self):
        await self.push_screen_wait(ModalAuthScreen())
        self.exit(self.backend.api_key)

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
        backend_value = event.value.split(" ")[-1].strip()
        match backend_value:
            case Backends.SQLITE:
                # self.config.set_backend(new_backend=event.value)
                self.config.set_backend(new_backend=backend_value)
            case Backends.JIRA:
                try:
                    version("atlassian-python-api")
                except ImportError:
                    self.notify(
                        title="Optional Jira dependency required",
                        message='Can be installed with: [$warning]uv tool install "kanban-tui\\[jira]"[/]',
                        # markup=False,
                        severity="warning",
                    )
                    with self.prevent(Select.Changed):
                        event.select.value = f"✔  {self.app.config.backend.mode}"  # self.config.backend.mode
                    self.action_focus_next()
                    return
                self.config.set_backend(new_backend=backend_value)

            case Backends.CLAUDE:
                # Check if Claude tasks directory exists
                claude_path = Path(
                    self.config.backend.claude_settings.tasks_base_path
                ).expanduser()
                if not claude_path.exists() or not any(claude_path.iterdir()):
                    self.notify(
                        title="Claude backend not available",
                        message="No Claude Code tasks found in ~/.claude/tasks/",
                        severity="warning",
                    )
                    with self.prevent(Select.Changed):
                        # event.select.value = self.config.backend.mode
                        event.select.value = f"✔  {self.app.config.backend.mode}"  # self.config.backend.mode
                    self.action_focus_next()
                    return
                # self.config.set_backend(new_backend=event.value)
                self.config.set_backend(new_backend=backend_value)
                self.notify(
                    title="Claude backend activated",
                    message="Read-only mode: viewing Claude Code tasks from ~/.claude/tasks/",
                    severity="information",
                )
        self.backend = self.get_backend()
        # This make the checkmark on the new backend
        event.select.update_values()
        self.action_refresh()

    def update_board_list(self):
        self.board_list = self.backend.get_boards()

    def watch_board_list(self):
        self.active_board = self.backend.active_board

    def watch_active_board(self, old_board: Board | None, new_board: Board):
        if self.active_board:
            match self.config.backend.mode:
                case Backends.SQLITE:
                    self.config.set_active_board(
                        new_active_board_id=self.active_board.board_id
                    )
                case Backends.CLAUDE:
                    self.config.set_active_claude_session(
                        new_session_id=self.active_board.name
                    )
                case Backends.JIRA:
                    self.config.set_active_jql(new_jql=self.active_board.board_id)

        self.update_column_list()
        # If updating Board, refresh setting screen
        if old_board:
            self.get_screen("settings", SettingsScreen).needs_refresh = True

    def watch_column_list(self):
        self.update_task_list()

    def watch_theme(self, new_theme: str):
        self.config.set_theme(new_theme)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        match action:
            case "refresh":
                if not isinstance(self.screen, BoardScreen):
                    return False
            case "show_backend_selector":
                if not isinstance(self.screen, tuple(self.SCREENS.values())):
                    return False
            case "switch_screen":
                if self.config.backend.mode != Backends.SQLITE:
                    return False
        return True

    def action_show_backend_selector(self):
        self.screen.query_one(KanbanTuiFooter).toggle_show()

    def action_refresh(self):
        self.update_board_list()
        self.watch_column_list()
        # used a worker here, so no await
        self.needs_refresh = True
        self.get_screen("board", BoardScreen).load_kanban_board()

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
