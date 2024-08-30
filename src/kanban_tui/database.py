import sqlite3
from pathlib import Path
from datetime import datetime

from kanban_tui.constants import DB_FULL_PATH
from kanban_tui.classes.task import Task


def create_connection(database: Path = DB_FULL_PATH) -> sqlite3.Connection:
    return sqlite3.connect(database=database)


def init_new_db(database: Path = DB_FULL_PATH):
    if database.exists():
        return

    task_db_creation_str = """
    CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    column INTEGER NOT NULL,
    category TEXT,
    description TEXT,
    creation_date TIMESTAMP NOT NULL,
    start_date TIMESTAMP,
    finish_date TIMESTAMP,
    due_date TIMESTAMP,
    CHECK (title <> "")
    );
    """

    indexes_creation_str = """
    CREATE INDEX IF NOT EXISTS idx_task_title ON tasks(title);
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(task_db_creation_str)
            con.execute(indexes_creation_str)

            return 0
        except sqlite3.Error as e:
            print(e)
            con.rollback()
            return 1


def create_new_task_db(
    title: str,
    column: int = 0,
    category: str | None = None,
    description: str | None = None,
    start_date: datetime | None = None,
    finish_date: datetime | None = None,
    due_date: datetime | None = None,
    database: Path = DB_FULL_PATH,
) -> str | int:
    task_dict = {
        "title": title,
        "column": column,
        "creation_date": datetime.now().replace(microsecond=0),
        "start_date": start_date,
        "finish_date": finish_date,
        "category": category,
        "due_date": due_date,
        "description": description,
    }

    transaction_str = """
    INSERT INTO tasks
    VALUES (
        NULL,
        :title,
        :column,
        :category,
        :description,
        :creation_date,
        :start_date,
        :finish_date,
        :due_date
        );"""

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, task_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_CHECK:
                return "please provide a character name"
            elif e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                return "character name already taken"
            return e.sqlite_errorname


def get_all_tasks_db(
    database: Path = DB_FULL_PATH,
) -> list[dict] | None:
    query_str = """
    SELECT *
    FROM tasks;
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            tasks = con.execute(query_str).fetchall()
            return [dict(task) for task in tasks]
        except sqlite3.Error as e:
            print(e)
            return None


def update_task_column_db(
    task_id: int, column: int, database: Path = DB_FULL_PATH
) -> None:
    new_column_dict = {"task_id": task_id, "column": column}
    transaction_str = """
    UPDATE tasks
    SET column = :column
    WHERE task_id = :task_id
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, new_column_dict)
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def update_task_db(task: Task, database: Path = DB_FULL_PATH) -> None:
    new_start_date_dict = {
        "task_id": task.task_id,
        "start_date": task.start_date,
        "column": task.column,
        "finish_date": task.finish_date,
    }
    transaction_str = """
    UPDATE tasks
    SET start_date = :start_date,
        finish_date = :finish_date,
        column = :column
    WHERE task_id = :task_id
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, new_start_date_dict)
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def update_task_start_task_db(
    task_id: int, start_date: int, database: Path = DB_FULL_PATH
) -> None:
    new_start_date_dict = {"task_id": task_id, "start_date": start_date, "column": 1}
    transaction_str = """
    UPDATE tasks
    SET start_date = :start_date,
        column = :column
    WHERE task_id = :task_id
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, new_start_date_dict)
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def update_task_finish_task_db(
    task_id: int, finish_date: int, database: Path = DB_FULL_PATH
) -> None:
    new_finish_date_dict = {"task_id": task_id, "start_date": finish_date, "column": 2}
    transaction_str = """
    UPDATE tasks
    SET finish_date = :finish_date,
        column = :column
    WHERE task_id = :task_id
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, new_finish_date_dict)
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def update_task_entry_db(
    task_id: int,
    title: str,
    category: str | None = None,
    description: str | None = None,
    due_date: datetime | None = None,
    database: Path = DB_FULL_PATH,
) -> str | int:
    update_task_dict = {
        "task_id": task_id,
        "title": title,
        "category": category,
        "description": description,
        "due_date": due_date,
    }

    transaction_str = """
    UPDATE tasks
    SET
        title = :title,
        category = :category,
        description = :description,
        due_date = :due_date
    WHERE task_id = :task_id;
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, update_task_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname
