from dataclasses import dataclass

from kanban_tui.backends.auth import AuthSettings
from kanban_tui.backends.base import Backend
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column
from kanban_tui.classes.task import Task
from kanban_tui.config import JiraBackendSettings
from kanban_tui.backends.auth import init_auth_file


@dataclass
class JiraBackend(Backend):
    settings: JiraBackendSettings

    def __post_init__(self):
        init_auth_file(self.settings.auth_file_path)
        self.auth = AuthSettings()

    # Queries
    def get_boards(self) -> list[Board]:
        return []

    def get_columns(self, board_id: int | None = None) -> list[Column]:
        return []

    def get_tasks_on_active_board(self) -> list[Task]:
        return []

    @property
    def active_board(self) -> Board | None: ...

    @property
    def api_key(self) -> str | None:
        return self.auth.jira.api_key
