from dataclasses import dataclass
from datetime import datetime

from kanban_tui.backends.base import Backend
from kanban_tui.classes.board import Board
from kanban_tui.classes.category import Category
from kanban_tui.classes.column import Column
from kanban_tui.classes.task import Task
from kanban_tui.classes.logevent import LogEvent
from kanban_tui.config import SqliteBackendSettings
from kanban_tui.backends.sqlite.database import (
    create_new_board_db,
    create_new_category_db,
    create_new_column_db,
    create_new_task_db,
    delete_board_db,
    delete_category_db,
    delete_column_db,
    delete_task_db,
    get_all_boards_db,
    get_all_categories_db,
    get_all_tasks_on_board_db,
    get_all_columns_on_board_db,
    get_category_by_id_db,
    get_task_by_id_db,
    get_tasks_by_ids_db,
    get_task_by_column_db,
    get_column_by_id_db,
    init_new_db,
    update_board_entry_db,
    update_column_name_db,
    update_category_entry_db,
    update_column_visibility_db,
    update_task_entry_db,
    update_task_status_db,
    get_board_info_dict,
    get_ordered_tasks_db,
    get_filtered_events_db,
    create_task_dependency_db,
    delete_task_dependency_db,
    would_create_cycle,
    get_task_dependencies_db,
)


@dataclass
class SqliteBackend(Backend):
    settings: SqliteBackendSettings

    def __post_init__(self):
        self.create_database()

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

    def get_tasks_by_board(self, board_id: int) -> list[Task]:
        return get_all_tasks_on_board_db(
            database=self.database_path,
            board_id=board_id,
        )

    # Board Management
    def create_new_board(
        self,
        name: str,
        icon: str | None = None,
        column_dict: dict[str, bool] | None = None,
    ) -> Board:
        return create_new_board_db(
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
        category: int | None = None,
        due_date: datetime | None = None,
    ) -> Task:
        return create_new_task_db(
            title=title,
            description=description,
            column=column,
            category=category,
            due_date=due_date,
            database=self.database_path,
        )

    def update_task_status(self, new_task: Task) -> Task:
        return update_task_status_db(
            task=new_task,
            database=self.database_path,
        )

    def update_task_entry(
        self,
        task_id: int,
        title: str,
        description: str,
        category: int,
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

    # Category Management
    def create_new_category(self, name: str, color: str) -> Category:
        return create_new_category_db(
            name=name, color=color, database=self.database_path
        )

    def update_category(self, category_id: int, name: str, color: str) -> Category:
        return update_category_entry_db(
            category_id=category_id, name=name, color=color, database=self.database_path
        )

    def delete_category(self, category_id: int):
        return delete_category_db(category_id=category_id, database=self.database_path)

    def get_all_categories(self) -> list[Category]:
        return get_all_categories_db(database=self.database_path)

    def get_category_by_id(self, category_id: int) -> Category:
        category = get_category_by_id_db(
            category_id=category_id, database=self.database_path
        )
        return category

    def get_task_by_id(self, task_id: int) -> Task | None:
        task = get_task_by_id_db(task_id=task_id, database=self.database_path)
        return task

    def get_tasks_by_ids(self, task_ids: list[int]) -> list[Task]:
        """Fetch multiple tasks by their IDs in a single query.

        Args:
            task_ids: List of task IDs to fetch

        Returns:
            List of Task objects
        """
        return get_tasks_by_ids_db(task_ids=task_ids, database=self.database_path)

    def get_tasks_by_column(self, column_id: int) -> list[Task] | None:
        tasks = get_task_by_column_db(column_id=column_id, database=self.database_path)
        return tasks

    def get_column_by_id(self, column_id: int) -> Column | None:
        column = get_column_by_id_db(column_id=column_id, database=self.database_path)
        return column

    # Column Management
    def update_column_visibility(self, column_id: int, visible: bool):
        update_column_visibility_db(
            column_id=column_id, visible=visible, database=self.database_path
        )

    def update_column_name(self, column_id: int, new_name: str):
        update_column_name_db(
            column_id=column_id, new_name=new_name, database=self.database_path
        )

    def delete_column(self, column_id: int, position: int, board_id: int) -> Column:
        return delete_column_db(
            column_id=column_id,
            position=position,
            board_id=board_id,
            database=self.database_path,
        )

    def create_new_column(self, board_id: int, position: int, name: str):
        return create_new_column_db(
            board_id=board_id,
            position=position,
            name=name,
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

    # Task Dependencies Management
    def create_task_dependency(self, task_id: int, depends_on_task_id: int) -> int:
        """Create a dependency between tasks.

        Args:
            task_id: The task that depends on another
            depends_on_task_id: The task it depends on

        Returns:
            dependency_id: The ID of the created dependency
        """
        return create_task_dependency_db(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            database=self.database_path,
        )

    def delete_task_dependency(self, task_id: int, depends_on_task_id: int) -> int:
        """Delete a dependency between tasks.

        Args:
            task_id: The dependent task
            depends_on_task_id: The task it depends on

        Returns:
            0 on success
        """
        return delete_task_dependency_db(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            database=self.database_path,
        )

    def get_task_dependencies(self, task_id: int) -> list[int]:
        """Get all tasks that the given task depends on.

        Args:
            task_id: The task ID

        Returns:
            List of task IDs this task depends on
        """
        return get_task_dependencies_db(
            task_id=task_id,
            database=self.database_path,
        )

    def would_create_dependency_cycle(
        self, task_id: int, depends_on_task_id: int
    ) -> bool:
        """Check if adding a dependency would create a circular dependency.

        Args:
            task_id: The task that would depend on another task
            depends_on_task_id: The task that would be depended upon

        Returns:
            True if adding this dependency would create a cycle, False otherwise
        """
        return would_create_cycle(task_id, depends_on_task_id, self.database_path)
