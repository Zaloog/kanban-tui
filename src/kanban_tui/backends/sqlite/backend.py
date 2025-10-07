from dataclasses import dataclass
from datetime import datetime

from kanban_tui.backends.base import Backend
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column
from kanban_tui.classes.task import Task
from kanban_tui.classes.logevent import LogEvent
from kanban_tui.config import SqliteBackendSettings
from kanban_tui.backends.sqlite.database import (
    create_new_board_db,
    create_new_task_db,
    delete_board_db,
    delete_task_db,
    get_all_boards_db,
    get_all_tasks_on_board_db,
    get_all_columns_on_board_db,
    init_new_db,
    update_board_entry_db,
    update_task_entry_db,
    update_task_status_db,
    get_board_info_dict,
    get_ordered_tasks_db,
    get_filtered_events_db,
)


@dataclass
class SqliteBackend(Backend):
    settings: SqliteBackendSettings

    # Queries
    def get_boards(self) -> list[Board]:
        return get_all_boards_db(database=self.settings.database_path)

    def get_columns(self, board_id: int | None = None) -> list[Column]:
        if board_id is None:
            board_id = self.active_board.board_id
        return get_all_columns_on_board_db(
            database=self.database_path,
            board_id=board_id,
        )

    def get_tasks_on_active_board(self) -> list[Task]:
        return get_all_tasks_on_board_db(
            database=self.database_path,
            board_id=self.active_board.board_id,
        )

    # Board Management
    def create_new_board(
        self,
        name: str,
        icon: str | None = None,
        column_dict: dict[str, bool] | None = None,
    ):
        create_new_board_db(
            name=name,
            icon=icon,
            column_dict=column_dict,
            database=self.database_path,
        )

    def delete_board(self, board_id: int):
        delete_board_db(board_id=board_id, database=self.database_path)

    def update_board(self, board_id: int, name: str, icon: str):
        update_board_entry_db(
            board_id=board_id,
            name=name,
            icon=icon,
            database=self.database_path,
        )

    def get_board_infos(self):
        return get_board_info_dict(database=self.database_path)

    # Task Management
    def create_new_task(
        self,
        title: str,
        description: str,
        column: int,
        category: str | None = None,
        due_date: datetime | None = None,
    ) -> Task:
        return create_new_task_db(
            title=title,
            description=description,
            column=column,
            category=category,
            due_date=due_date,
            board_id=self.settings.active_board_id,
            database=self.database_path,
        )

    def update_task_status(self, new_task: Task):
        update_task_status_db(
            task=new_task,
            database=self.database_path,
        )

    def update_task_entry(
        self,
        task_id: int,
        title: str,
        description: str,
        category: str,
        due_date: datetime,
    ) -> Task:
        return update_task_entry_db(
            task_id=task_id,
            title=title,
            description=description,
            category=category,
            due_date=due_date,
            database=self.database_path,
        )

    def delete_task(self, task_id: int):
        delete_task_db(
            task_id=task_id,
            database=self.database_path,
        )

    # Plotting
    def get_ordered_tasks(
        self,
        order_by: str,
    ) -> list[dict]:
        return get_ordered_tasks_db(
            order_by=order_by,
            database=self.database_path,
        )

    def get_filtered_events(self, filter: dict) -> list[LogEvent]:
        return get_filtered_events_db(
            filter=filter,
            database=self.database_path,
        )

    def create_database(self):
        """Creates database if not exists"""
        init_new_db(database=self.database_path)

    @property
    def active_board(self) -> Board:
        for board in self.get_boards():
            if board.board_id == self.settings.active_board_id:
                return board
        raise Exception("No active Board Found")

    @property
    def database_path(self) -> str:
        return self.settings.database_path
