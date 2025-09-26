from dataclasses import dataclass
from kanban_tui.backends import Backend
from kanban_tui.config import SqliteBackendSettings
from kanban_tui.backends.sqlite.database import get_all_boards_db


@dataclass
class SqliteBackend(Backend):
    settings: SqliteBackendSettings

    def get_boards(self):
        boards = get_all_boards_db(database=self.settings.database_path)
        return boards

    def get_columns(self):
        return

    def get_tasks(self):
        return
