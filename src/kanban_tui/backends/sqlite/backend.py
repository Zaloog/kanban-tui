from dataclasses import dataclass
from kanban_tui.backends.base import Backend
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column
from kanban_tui.classes.task import Task
from kanban_tui.config import SqliteBackendSettings
from kanban_tui.backends.sqlite.database import (
    get_all_boards_db,
    get_all_tasks_on_board_db,
    get_all_columns_on_board_db,
)


@dataclass
class SqliteBackend(Backend):
    settings: SqliteBackendSettings

    def get_boards(self) -> list[Board]:
        return get_all_boards_db(database=self.settings.database_path)

    def get_columns(self, board_id: int | None = None) -> list[Column]:
        if board_id is None:
            board_id = self.active_board.board_id
        return get_all_columns_on_board_db(
            database=self.database_path,
            board_id=board_id,
        )

    def get_tasks(self) -> list[Task]:
        return get_all_tasks_on_board_db(
            database=self.database_path,
            board_id=self.active_board.board_id,
        )

    @property
    def active_board(self) -> Board:
        for board in self.get_boards():
            if board.board_id == self.settings.active_board_id:
                return board
        raise Exception("No active Board Found")

    @property
    def database_path(self) -> str:
        return self.settings.database_path
