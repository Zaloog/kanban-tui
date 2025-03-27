import sqlite3
from pathlib import Path
from typing import Literal
import datetime

from kanban_tui.constants import DB_FULL_PATH, DEFAULT_COLUMN_DICT
from kanban_tui.classes.task import Task
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column
from kanban_tui.classes.logevent import LogEvent


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


def board_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Board(**{k: v for k, v in zip(fields, row)})


def column_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Column(**{k: v for k, v in zip(fields, row)})


def logevent_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return LogEvent(**{k: v for k, v in zip(fields, row)})


def board_info_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {k: v for k, v in zip(fields, row)}


def init_new_db(database: Path = DB_FULL_PATH):
    if database.exists():
        return

    task_table_creation_str = """
    CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    column INTEGER NOT NULL,
    category TEXT,
    description TEXT,
    creation_date DATETIME NOT NULL,
    start_date DATETIME,
    finish_date DATETIME,
    due_date DATETIME,
    time_worked_on INTEGER,
    board_id INTEGER,
    FOREIGN KEY (board_id) REFERENCES boards(board_id),
    FOREIGN KEY (column) REFERENCES columns(column_id),
    CHECK (title <> "")
    );
    """

    board_table_creation_str = """
    CREATE TABLE IF NOT EXISTS boards (
    board_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    creation_date DATETIME NOT NULL,
    reset_column INTEGER DEFAULT NULL,
    start_column INTEGER DEFAULT NULL,
    finish_column INTEGER DEFAULT NULL,
    FOREIGN KEY (reset_column) REFERENCES columns(column_id),
    FOREIGN KEY (start_column) REFERENCES columns(column_id),
    FOREIGN KEY (finish_column) REFERENCES columns(column_id),
    CHECK (name <> "")
    );
    """
    column_table_creation_str = """
    CREATE TABLE IF NOT EXISTS columns (
    column_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    visible BOOLEAN,
    position INTEGER,
    board_id INTEGER,
    FOREIGN KEY (board_id) REFERENCES boards(board_id),
    CHECK (name <> "")
    );
    """

    audit_table_creation_str = """
    CREATE TABLE IF NOT EXISTS audits (
    event_id INTEGER PRIMARY KEY,
    event_timestamp DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id INTEGER NOT NULL,
    object_field TEXT,
    value_old TEXT,
    value_new TEXT
    );
    """

    board_create_trigger_str = """
    CREATE TRIGGER board_creation
    AFTER INSERT on boards
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id
            )
        VALUES (
            datetime('now'),
            'CREATE',
            'board',
            NEW.board_id
        );
    END;
    """

    board_delete_trigger_str = """
    CREATE TRIGGER board_deletion
    AFTER DELETE on boards
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id
            )
        VALUES (
            datetime('now'),
            'DELETE',
            'board',
            OLD.board_id
        );
    END;
    """

    board_update_trigger_str = """
    CREATE TRIGGER board_update
    AFTER UPDATE on boards
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'board',
            OLD.board_id,
            'name',
            OLD.name,
            NEW.name
        WHERE OLD.name IS NOT NEW.name;

        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'board',
            OLD.board_id,
            'icon',
            OLD.icon,
            NEW.icon
        WHERE OLD.icon IS NOT NEW.icon;

        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'board',
            OLD.board_id,
            'reset_column',
            OLD.reset_column,
            NEW.reset_column
        WHERE OLD.reset_column IS NOT NEW.reset_column;

        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'board',
            OLD.board_id,
            'start_column',
            OLD.start_column,
            NEW.start_column
        WHERE OLD.start_column IS NOT NEW.start_column;

        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'board',
            OLD.board_id,
            'finish_column',
            OLD.finish_column,
            NEW.finish_column
        WHERE OLD.finish_column IS NOT NEW.finish_column;
    END;
    """

    column_create_trigger_str = """
    CREATE TRIGGER column_creation
    AFTER INSERT on columns
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id
            )
        VALUES (
            datetime('now'),
            'CREATE',
            'column',
            NEW.column_id
        );
    END;
    """

    column_delete_trigger_str = """
    CREATE TRIGGER column_deletion
    AFTER DELETE on columns
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id
            )
        VALUES (
            datetime('now'),
            'DELETE',
            'column',
            OLD.column_id
        );
    END;
    """

    column_update_trigger_str = """
    CREATE TRIGGER column_update
    AFTER UPDATE on columns
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'column',
            OLD.column_id,
            'name',
            OLD.name,
            NEW.name

        WHERE OLD.name IS NOT NEW.name;
    END;
    """

    task_create_trigger_str = """
    CREATE TRIGGER task_creation
    AFTER INSERT on tasks
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id
            )
        VALUES (
            datetime('now'),
            'CREATE',
            'task',
            NEW.task_id
        );
    END;
    """

    task_delete_trigger_str = """
    CREATE TRIGGER task_deletion
    AFTER DELETE on tasks
    FOR EACH ROW
    BEGIN
        INSERT into audits (
            event_timestamp,
            event_type,
            object_type,
            object_id
            )
        VALUES (
            datetime('now'),
            'DELETE',
            'task',
            OLD.task_id
        );
    END;
    """

    task_update_trigger_str = """
    CREATE TRIGGER task_update
    AFTER UPDATE ON tasks
    FOR EACH ROW
    BEGIN
        INSERT INTO audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'task',
            OLD.task_id,
            'title',
            OLD.title,
            NEW.title
        WHERE OLD.title IS NOT NEW.title;

        INSERT INTO audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'task',
            OLD.task_id,
            'description',
            OLD.description,
            NEW.description
        WHERE OLD.description IS NOT NEW.description;

        INSERT INTO audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'task',
            OLD.task_id,
            'due_date',
            OLD.due_date,
            NEW.due_date
        WHERE OLD.due_date IS NOT NEW.due_date;

        INSERT INTO audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'task',
            OLD.task_id,
            'start_date',
            OLD.start_date,
            NEW.start_date
        WHERE OLD.start_date IS NOT NEW.start_date;

        INSERT INTO audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'task',
            OLD.task_id,
            'finish_date',
            OLD.finish_date,
            NEW.finish_date
        WHERE OLD.finish_date IS NOT NEW.finish_date;

        INSERT INTO audits (
            event_timestamp,
            event_type,
            object_type,
            object_id,
            object_field,
            value_old,
            value_new
            )
        SELECT
            datetime('now'),
            'UPDATE',
            'task',
            OLD.task_id,
            'column',
            OLD.column,
            NEW.column
        WHERE OLD.column IS NOT NEW.column;
    END;
    """

    # indexes_creation_str = """
    # CREATE INDEX IF NOT EXISTS idx_task_title ON tasks(title);
    # CREATE INDEX IF NOT EXISTS idx_board_name ON boards(name);
    # CREATE INDEX IF NOT EXISTS idx_column_name ON boards(name);
    # """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(audit_table_creation_str)

            con.execute(task_table_creation_str)
            con.execute(task_create_trigger_str)
            con.execute(task_delete_trigger_str)
            con.execute(task_update_trigger_str)

            con.execute(board_table_creation_str)
            con.execute(board_create_trigger_str)
            con.execute(board_delete_trigger_str)
            con.execute(board_update_trigger_str)

            con.execute(column_table_creation_str)
            con.execute(column_create_trigger_str)
            con.execute(column_delete_trigger_str)
            con.execute(column_update_trigger_str)

            con.commit()

            # con.executescript(indexes_creation_str)
        except sqlite3.Error as e:
            con.rollback()
            raise e


# Audit Tables


def create_new_board_db(
    name: str,
    icon: str | None = None,
    column_dict: dict[str, bool] = DEFAULT_COLUMN_DICT,
    database: Path = DB_FULL_PATH,
) -> str | int:
    board_dict = {
        "name": name,
        "icon": icon,
        "creation_date": datetime.datetime.now().replace(microsecond=0),
    }
    transaction_str = """
    INSERT INTO boards
    VALUES (
        NULL,
        :name,
        :icon,
        :creation_date,
        NULL,
        NULL,
        NULL
        )
        RETURNING board_id
        ;"""

    transaction_str_cols = """
    INSERT INTO columns
    VALUES (
        NULL,
        :name,
        :visible,
        :position,
        :board_id
        );"""
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            # create Board
            (created_board_id,) = con.execute(
                transaction_str,
                board_dict,
            ).fetchone()

            # create Columns
            for position, (column_name, visibility) in enumerate(
                column_dict.items(), start=1
            ):
                transaction_column_dict = {
                    "name": column_name,
                    "visible": visibility,
                    "position": position,
                    "board_id": created_board_id,
                }
                con.execute(transaction_str_cols, transaction_column_dict)
            con.commit()
            return created_board_id
        except sqlite3.Error as e:
            con.rollback()
            raise e


def create_new_task_db(
    title: str,
    board_id: int,
    column: int,
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
        "board_id": board_id,
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
        :time_worked_on,
        :board_id
        );"""

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, task_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            raise e
            return e.sqlite_errorname


def create_new_column_db(
    name: str,
    position: int,
    board_id: int,
    visible: bool = True,
    database: Path = DB_FULL_PATH,
):
    transaction_str_cols = """
    INSERT INTO columns
    VALUES (
        NULL,
        :name,
        :visible,
        :position,
        :board_id
        );"""
    column_dict = {
        "name": name,
        "visible": visible,
        "position": position,
        "board_id": board_id,
    }
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str_cols, column_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            raise e
            return e.sqlite_errorname


def get_all_tasks_on_board_db(
    board_id: int,
    database: Path = DB_FULL_PATH,
) -> list[Task] | None:
    board_id_dict = {"board_id": board_id}

    query_str = """
    SELECT *
    FROM tasks
    WHERE board_id = :board_id ;
    """

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            tasks = con.execute(query_str, board_id_dict).fetchall()
            return tasks
        except sqlite3.Error as e:
            print(e)
            raise e
            return None


def get_all_columns_on_board_db(
    board_id: int,
    database: Path = DB_FULL_PATH,
) -> list[Column] | None:
    board_id_dict = {"board_id": board_id}

    query_str = """
    SELECT *
    FROM columns
    WHERE board_id = :board_id
    ORDER BY position;
    """

    with create_connection(database=database) as con:
        con.row_factory = column_factory
        try:
            columns = con.execute(query_str, board_id_dict).fetchall()
            return columns
        except sqlite3.Error as e:
            print(e)
            raise e
            return None


def update_status_update_columns_db(
    column_prefix: Literal["reset", "start", "finish"],
    new_status: int | None,
    board_id: int,
    database: Path = DB_FULL_PATH,
) -> int | str:
    update_dict = {"board_id": board_id, "new_status": new_status}

    transaction_str = f"""
    UPDATE boards
    SET
        {column_prefix}_column = :new_status
    WHERE
        board_id = :board_id
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, update_dict)
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def init_first_board(database: Path = DB_FULL_PATH) -> None:
    # Check if Boards exist
    if not get_all_boards_db(database=database):
        create_new_board_db(
            name="Kanban Board",
            icon=":sparkles:",
            column_dict=DEFAULT_COLUMN_DICT,
            database=database,
        )


def get_all_boards_db(
    database: Path = DB_FULL_PATH,
) -> list[Board] | None:
    query_str = """
    SELECT *
    FROM boards;
    """

    with create_connection(database=database) as con:
        con.row_factory = board_factory
        try:
            boards = con.execute(query_str).fetchall()
            return boards
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


def update_column_visibility_db(
    column_id: int,
    visible: bool,
    database: Path = DB_FULL_PATH,
) -> str | int:
    update_column_dict = {
        "column_id": column_id,
        "visible": visible,
    }

    transaction_str = """
    UPDATE columns
    SET
        visible = :visible
    WHERE
        column_id = :column_id;
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, update_column_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def update_column_positions_db(
    board_id: int, new_position: int, database: Path = DB_FULL_PATH
) -> str | int:
    update_column_position_dict = {"board_id": board_id, "new_position": new_position}

    transaction_str = """
    UPDATE columns
    SET
        position = position + 1
    WHERE
        board_id = :board_id
        AND position > :new_position
    ;
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, update_column_position_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def update_column_name_db(
    column_id: int, new_column_name: str, database: Path = DB_FULL_PATH
) -> str | int:
    update_column_name_dict = {"column_id": column_id, "new_name": new_column_name}

    transaction_str = """
    UPDATE columns
    SET
        name = :new_name
    WHERE
        column_id = :column_id
    ;
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, update_column_name_dict)
            con.commit()
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


def delete_column_db(column_id: int, database: Path = DB_FULL_PATH) -> int | str:
    delete_str = """
    DELETE FROM columns
    WHERE column_id = ?
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(delete_str, (column_id,))
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
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


# For Plotting
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


# Boards Stuff
# After Editing
def update_board_entry_db(
    board_id: int,
    name: str,
    icon: str | None = None,
    database: Path = DB_FULL_PATH,
) -> str | int:
    update_board_dict = {
        "board_id": board_id,
        "name": name,
        "icon": icon,
    }

    transaction_str = """
    UPDATE boards
    SET
        name = :name,
        icon = :icon
    WHERE board_id = :board_id;
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(transaction_str, update_board_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def delete_board_db(board_id: int, database: Path = DB_FULL_PATH) -> int | str:
    delete_board_str = """
    DELETE FROM boards
    WHERE board_id = ?
    """

    delete_task_str = """
    DELETE FROM tasks
    WHERE board_id = ?
    """

    delete_column_str = """
    DELETE FROM columns
    WHERE board_id = ?
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(delete_board_str, (board_id,))
            con.execute(delete_task_str, (board_id,))
            con.execute(delete_column_str, (board_id,))
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            print(e.sqlite_errorname)
            return e.sqlite_errorname


def get_all_board_infos(
    database: Path = DB_FULL_PATH,
) -> list[dict] | None:
    query_str = """
    SELECT
    b.board_id AS board_id,
    COUNT(DISTINCT t.task_id) AS amount_tasks,
    COUNT(DISTINCT c.column_id) AS amount_columns,
    MIN(t.due_date) AS next_due
    FROM boards b
    LEFT JOIN tasks t ON b.board_id = t.board_id
    LEFT JOIN columns c ON b.board_id = c.board_id
    GROUP BY b.board_id;
    """

    with create_connection(database=database) as con:
        con.row_factory = board_info_factory
        try:
            board_infos = con.execute(query_str).fetchall()
            return board_infos
        except sqlite3.Error as e:
            print(e)
            return None


def get_filtered_events_db(
    database: Path = DB_FULL_PATH, filter: dict[str, list] | None = None
) -> list[LogEvent] | None:
    if not filter:
        query_str = """
        SELECT
            *
        FROM
            audits;
        """
    else:
        params = filter["events"] + filter["objects"] + [filter["time"]]
        events_placeholder = ",".join(["?"] * len(filter["events"]))
        objects_placeholder = ",".join(["?"] * len(filter["objects"]))
        query_str = f"""
        SELECT
            *
        FROM
            audits
        WHERE
            event_type in ({events_placeholder})
            AND
            object_type in ({objects_placeholder})
            AND
            event_timestamp >= ?
            ;
        """

    with create_connection(database=database) as con:
        con.row_factory = logevent_factory
        try:
            events = con.execute(query_str, params).fetchall()
            return events
        except sqlite3.Error as e:
            print(e)
            raise e
            return None
