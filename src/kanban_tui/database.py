import sqlite3
from pathlib import Path
from datetime import datetime

from kanban_tui.constants import DB_FULL_PATH


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
