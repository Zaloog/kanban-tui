import sqlite3
from pathlib import Path
import datetime

from kanban_tui.constants import DB_FULL_PATH
from kanban_tui.classes.task import Task


def adapt_datetime_iso(val: datetime.datetime) -> str:
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()


sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)


def convert_datetime(val: bytes) -> datetime.datetime:
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())


sqlite3.register_converter("datetime", convert_datetime)


def create_connection(database: Path = DB_FULL_PATH) -> sqlite3.Connection:
    return sqlite3.connect(database=database, detect_types=sqlite3.PARSE_DECLTYPES)


def task_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Task(**{k: v for k, v in zip(fields, row)})


def init_new_db(database: Path = DB_FULL_PATH):
    if database.exists():
        return

    task_db_creation_str = """
    CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    column TEXT NOT NULL,
    category TEXT,
    description TEXT,
    creation_date DATETIME NOT NULL,
    start_date DATETIME,
    finish_date DATETIME,
    due_date DATETIME,
    time_worked_on INTEGER,
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
    column: str = "Ready",  # TODO B
    category: str | None = None,
    description: str | None = None,
    start_date: datetime.datetime | None = None,
    finish_date: datetime.datetime | None = None,
    due_date: datetime.datetime | None = None,
    time_worked_on: int = 0,
    database: Path = DB_FULL_PATH,
) -> str | int:
    task_dict = {
        "title": title,
        "column": column,
        "creation_date": datetime.datetime.now().replace(microsecond=0),
        "start_date": start_date,
        "finish_date": finish_date,
        "category": category,
        "due_date": due_date,
        "description": description,
        "time_worked_on": time_worked_on,
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
        :due_date,
        :time_worked_on
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
) -> list[Task] | None:
    query_str = """
    SELECT *
    FROM tasks;
    """

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            tasks = con.execute(query_str).fetchall()
            return tasks
        except sqlite3.Error as e:
            print(e)
            return None


# After column Movement
def update_task_db(task: Task, database: Path = DB_FULL_PATH) -> int | str:
    new_start_date_dict = {
        "task_id": task.task_id,
        "start_date": task.start_date,
        "column": task.column,
        "finish_date": task.finish_date,
        "time_worked_on": task.time_worked_on,
    }
    transaction_str = """
    UPDATE tasks
    SET start_date = :start_date,
        finish_date = :finish_date,
        column = :column,
        time_worked_on = :time_worked_on
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


# After Editing
def update_task_entry_db(
    task_id: int,
    title: str,
    category: str | None = None,
    description: str | None = None,
    due_date: datetime.datetime | None = None,
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


def delete_task_db(task_id: int, database: Path = DB_FULL_PATH) -> int | str:
    delete_str = """
    DELETE FROM tasks
    WHERE task_id = ?
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(delete_str, (task_id,))
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def get_ordered_tasks_db(
    order_by: str,
    database: Path = DB_FULL_PATH,
) -> list[dict] | None:
    query_str = f"""
    SELECT
        {order_by} as date,
        category,
        COUNT(task_id) as amount
    FROM tasks
    WHERE date IS NOT NULL
    GROUP BY category, date
    ORDER BY date;
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            tasks = con.execute(query_str).fetchall()
            return [dict(task) for task in tasks]
        except sqlite3.Error as e:
            print(e)
            return None
