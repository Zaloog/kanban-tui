from dataclasses import dataclass

from kanban_tui.backends.auth import AuthSettings
from kanban_tui.backends.base import Backend
from kanban_tui.classes.board import Board
from kanban_tui.classes.category import Category
from kanban_tui.classes.column import Column
from kanban_tui.classes.task import Task
from kanban_tui.config import JiraBackendSettings
from kanban_tui.backends.auth import init_auth_file
from kanban_tui.backends.jira.jira_api import (
    get_jql,
    authenticate_to_jira,
    api,
)


@dataclass
class JiraBackend(Backend):
    settings: JiraBackendSettings

    def __post_init__(self):
        init_auth_file(self.settings.auth_file_path)
        self.auth_settings = AuthSettings()
        self.auth = authenticate_to_jira(
            self.settings.base_url, self.api_key, self.cert_path
        )

    # Queries
    def get_boards(self) -> list[Board]:
        return []

    def get_all_categories(self) -> list[Category]:
        return []

    def get_board_infos(self) -> list[Board]:
        return []

    def get_columns(self, board_id: int | None = None) -> list[Column]:
        return []

    def get_tasks_on_active_board(self) -> list[Task]:
        return []

    def api(self):
        return api(auth=self.auth)

    def jql(self):
        # resp = [i["fields"]["status"]["name"] for i in get_all_issues(self.auth, "KTUI")]

        JQL = "project = KTUI AND key = KTUI-2 ORDER BY Rank ASC"
        resp = {k: v for k, v in get_jql(self.auth, jql=JQL).items()}
        # resp = get_project(self.auth, "KTUI")
        return resp

    @property
    def active_board(self) -> Board | None: ...

    @property
    def api_key(self) -> str | None:
        return self.auth_settings.jira.api_key

    @property
    def cert_path(self) -> str | None:
        return self.auth_settings.jira.cert_path
