import json
import sqlite3
from pathlib import Path
from typing import Any, Generator, Sequence
from contextlib import contextmanager
import datetime

from kanban_tui.classes.category import Category
from kanban_tui.constants import DATABASE_FILE, DEFAULT_COLUMN_DICT
from kanban_tui.classes.task import Task
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column
from kanban_tui.classes.logevent import LogEvent
from kanban_tui.backends.sqlite.migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_migration_v1_to_v2,
    apply_migration_v2_to_v3,
    increment_schema_version,
)


def adapt_datetime_iso(val: datetime.datetime) -> str:
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()


sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)


def convert_datetime(val: bytes) -> datetime.datetime:
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())


sqlite3.register_converter("datetime", convert_datetime)


@contextmanager
def create_connection(
    database: str = DATABASE_FILE.as_posix(),
) -> Generator[sqlite3.Connection, None, None]:
    con = sqlite3.connect(database=Path(database), detect_types=sqlite3.PARSE_DECLTYPES)
    con.execute("PRAGMA foreign_keys = ON")
    yield con
    con.close()


def task_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    data = dict(zip(fields, row))

    # Parse JSON arrays for dependency fields
    if "blocked_by" in data and isinstance(data["blocked_by"], str):
        data["blocked_by"] = json.loads(data["blocked_by"])
    if "blocking" in data and isinstance(data["blocking"], str):
        data["blocking"] = json.loads(data["blocking"])

    # Parse JSON for metadata field
    if "metadata" in data:
        if isinstance(data["metadata"], str):
            data["metadata"] = json.loads(data["metadata"]) if data["metadata"] else {}
        elif data["metadata"] is None:
            data["metadata"] = {}

    return Task(**data)


def board_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Board(**{k: v for k, v in zip(fields, row)})


def category_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Category(**{k: v for k, v in zip(fields, row)})


def column_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return Column(**{k: v for k, v in zip(fields, row)})


def logevent_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return LogEvent(**{k: v for k, v in zip(fields, row)})


def board_info_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {k: v for k, v in zip(fields, row)}


def get_schema_version(database: str = DATABASE_FILE.as_posix()) -> int:
    """Get current schema version from database"""
    with create_connection(database=database) as con:
        try:
            result = con.execute(
                "SELECT version FROM schema_versions ORDER BY version DESC LIMIT 1"
            ).fetchone()
            return result[0] if result else 1
        except sqlite3.OperationalError:
            # schema_version table doesn't exist = version 1 (legacy database)
            return 1


def run_migrations(database: str = DATABASE_FILE.as_posix()):
    current_version = get_schema_version(database)

    if current_version >= CURRENT_SCHEMA_VERSION:
        return

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            # first migration to v2
            if current_version < 2:
                apply_migration_v1_to_v2(con)
                increment_schema_version(con, 2)

            # migration to v3
            if current_version < 3:
                apply_migration_v2_to_v3(con)
                increment_schema_version(con, 3)

            con.commit()

        except sqlite3.Error as e:
            con.rollback()
            raise e


def init_new_db(database: str = DATABASE_FILE.as_posix()):
    if Path(database).exists():
        run_migrations(database)
        return

    task_table_creation_str = """
    CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    column INTEGER NOT NULL,
    category INTEGER,
    description TEXT,
    creation_date DATETIME NOT NULL,
    start_date DATETIME,
    finish_date DATETIME,
    due_date DATETIME,
    FOREIGN KEY (column) REFERENCES columns(column_id),
    FOREIGN KEY (category) REFERENCES categories(category_id),
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
    FOREIGN KEY (reset_column) REFERENCES columns(column_id) ON DELETE SET NULL,
    FOREIGN KEY (start_column) REFERENCES columns(column_id) ON DELETE SET NULL,
    FOREIGN KEY (finish_column) REFERENCES columns(column_id) ON DELETE SET NULL,
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

    category_table_creation_str = """
    CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT NOT NULL,
    CHECK (name <> ""),
    CHECK (color <> "")
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
            con.execute(category_table_creation_str)

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

            # Initialize schema version for new database (already at v3)

            con.commit()

            # con.executescript(indexes_creation_str)
            run_migrations(database)
            # Don't run migrations on brand new database - it's already at current version
        except sqlite3.Error as e:
            con.rollback()
            raise e


# Audit Tables


def create_new_board_db(
    name: str,
    icon: str | None = None,
    column_dict: dict[str, bool] | None = None,
    database: str = DATABASE_FILE.as_posix(),
) -> Board:
    if column_dict is None:
        column_dict = DEFAULT_COLUMN_DICT
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
        RETURNING *
        ;"""

    transaction_str_cols = """
    INSERT INTO columns
    VALUES (
        NULL,
        :name,
        :visible,
        :position,
        :board_id
        )
        RETURNING column_id
        ;"""
    with create_connection(database=database) as con:
        con.row_factory = board_factory
        try:
            # create Board
            created_board = con.execute(
                transaction_str,
                board_dict,
            ).fetchone()

            # create Columns and track column IDs
            column_ids = []
            con.row_factory = sqlite3.Row  # Switch to Row factory to get column_id
            for position, (column_name, visibility) in enumerate(
                column_dict.items(), start=1
            ):
                transaction_column_dict = {
                    "name": column_name,
                    "visible": visibility,
                    "position": position,
                    "board_id": created_board.board_id,
                }
                result = con.execute(transaction_str_cols, transaction_column_dict)
                column_id = result.fetchone()[0]
                column_ids.append(column_id)

            # Set default status columns if using default column layout
            # DEFAULT_COLUMN_DICT = {"Ready": True, "Doing": True, "Done": True, "Archive": False}
            if column_dict == DEFAULT_COLUMN_DICT:
                update_status_columns_str = """
                UPDATE boards
                SET
                    reset_column = :reset_column,
                    start_column = :start_column,
                    finish_column = :finish_column
                WHERE board_id = :board_id
                """
                status_columns_dict = {
                    "board_id": created_board.board_id,
                    "reset_column": column_ids[0],  # Ready
                    "start_column": column_ids[1],  # Doing
                    "finish_column": column_ids[2],  # Done
                }
                con.execute(update_status_columns_str, status_columns_dict)

                # Update the created_board object to reflect the changes
                created_board.reset_column = status_columns_dict["reset_column"]
                created_board.start_column = status_columns_dict["start_column"]
                created_board.finish_column = status_columns_dict["finish_column"]

            con.commit()
            return created_board
        except sqlite3.Error as e:
            raise e
            con.rollback()


def create_new_task_db(
    title: str,
    column: int,
    category: int | None = None,
    description: str = "",
    start_date: datetime.datetime | None = None,
    finish_date: datetime.datetime | None = None,
    due_date: datetime.datetime | None = None,
    metadata: dict[str, Any] | None = None,
    database: str = DATABASE_FILE.as_posix(),
) -> Task:
    task_dict = {
        "title": title,
        "column": column,
        "creation_date": datetime.datetime.now().replace(microsecond=0),
        "start_date": start_date,
        "finish_date": finish_date,
        "category": category,
        "due_date": due_date,
        "description": description,
        "metadata": json.dumps(metadata if metadata is not None else {}),
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
        :metadata
        )
        RETURNING *
        ;"""

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            new_task = con.execute(transaction_str, task_dict).fetchone()
            con.commit()
            return new_task
        except sqlite3.Error as e:
            raise e
            con.rollback()


def create_new_column_db(
    name: str,
    position: int,
    board_id: int,
    visible: bool = True,
    database: str = DATABASE_FILE.as_posix(),
) -> Column:
    transaction_str_cols = """
    INSERT INTO columns
    VALUES (
        NULL,
        :name,
        :visible,
        :position,
        :board_id
        )
        RETURNING *
        ;"""
    column_dict = {
        "name": name,
        "visible": visible,
        "position": position,
        "board_id": board_id,
    }
    update_other_positions_str = """
    UPDATE columns
    SET
        position = position + 1
    WHERE
        board_id = :board_id
        AND position >= :position
    ;
    """
    with create_connection(database=database) as con:
        con.row_factory = column_factory
        try:
            con.execute(update_other_positions_str, column_dict)
            new_column = con.execute(transaction_str_cols, column_dict).fetchone()
            con.commit()
            return new_column
        except sqlite3.Error as e:
            raise e
            con.rollback()


def create_new_category_db(
    name: str,
    color: str,
    database: str = DATABASE_FILE.as_posix(),
) -> Category:
    transaction_str_cols = """
    INSERT INTO categories
    VALUES (
        NULL,
        :name,
        :color
        )
        RETURNING *
        ;"""
    category_dict = {
        "name": name,
        "color": color,
    }
    with create_connection(database=database) as con:
        con.row_factory = category_factory
        try:
            new_category = con.execute(transaction_str_cols, category_dict).fetchone()
            con.commit()
            return new_category
        except sqlite3.Error as e:
            con.rollback()
            raise e


def update_category_entry_db(
    category_id: int,
    name: str,
    color: str,
    database: str = DATABASE_FILE.as_posix(),
) -> Category:
    update_category_dict = {
        "category_id": category_id,
        "name": name,
        "color": color,
    }

    transaction_str = """
    UPDATE categories
    SET
        name = :name,
        color = :color
    WHERE category_id = :category_id
    RETURNING *
    ;
    """

    with create_connection(database=database) as con:
        con.row_factory = category_factory
        try:
            updated_category = con.execute(
                transaction_str, update_category_dict
            ).fetchone()
            con.commit()
            return updated_category
        except sqlite3.Error as e:
            con.rollback()
            raise e


def delete_category_db(
    category_id: int, database: str = DATABASE_FILE.as_posix()
) -> int:
    reset_tasks_str = """
    UPDATE tasks
    SET
        category = null
    WHERE category = ?
    """

    delete_category_str = """
    DELETE FROM categories
    WHERE category_id = ?
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(reset_tasks_str, (category_id,))
            con.execute(delete_category_str, (category_id,))

            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            raise e


def get_all_tasks_on_board_db(
    board_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> list[Task]:
    board_id_dict = {"board_id": board_id}

    query_str = """
    SELECT
        t.*,
        COALESCE(
            (SELECT json_group_array(d.depends_on_task_id)
             FROM dependencies d
             WHERE d.task_id = t.task_id),
            '[]'
        ) as blocked_by,
        COALESCE(
            (SELECT json_group_array(d.task_id)
             FROM dependencies d
             WHERE d.depends_on_task_id = t.task_id),
            '[]'
        ) as blocking
    FROM tasks t
    LEFT JOIN columns c ON c.column_id = t.column
    LEFT JOIN boards b ON b.board_id = c.board_id
    WHERE b.board_id = :board_id ;
    """

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            tasks = con.execute(query_str, board_id_dict).fetchall()
            con.commit()
            return tasks
        except sqlite3.Error as e:
            con.rollback()
            raise e


def get_all_columns_on_board_db(
    board_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> list[Column]:
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
            con.commit()
            return columns
        except sqlite3.Error as e:
            con.rollback()
            raise Exception(e)


def update_status_update_columns_db(
    column_prefix: str,
    new_status: int | None,
    board_id: int,
    database: str = DATABASE_FILE.as_posix(),
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
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            raise e


def init_first_board(database: str = DATABASE_FILE.as_posix()) -> None:
    # Check if Boards exist
    if not get_all_boards_db(database=database):
        create_new_board_db(
            name="Kanban Board",
            icon=":sparkles:",
            column_dict=DEFAULT_COLUMN_DICT,
            database=database,
        )


def get_all_boards_db(
    database: str = DATABASE_FILE.as_posix(),
) -> list[Board]:
    query_str = """
    SELECT *
    FROM boards;
    """

    with create_connection(database=database) as con:
        con.row_factory = board_factory
        try:
            boards = con.execute(query_str).fetchall()
            con.commit()
            return boards
        except sqlite3.Error as e:
            con.rollback()
            raise (e)


def get_all_categories_db(
    database: str = DATABASE_FILE.as_posix(),
) -> list[Category]:
    query_str = """
    SELECT *
    FROM categories;
    """

    with create_connection(database=database) as con:
        con.row_factory = category_factory
        try:
            categories = con.execute(query_str).fetchall()
            con.commit()
            return categories
        except sqlite3.Error as e:
            con.rollback()
            raise (e)


def get_category_by_id_db(
    category_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> Category:
    query_str = """
    SELECT *
    FROM categories
    WHERE category_id = :category_id
    ;
    """
    category_id_dict = {"category_id": category_id}

    with create_connection(database=database) as con:
        con.row_factory = category_factory
        try:
            category = con.execute(query_str, category_id_dict).fetchone()
            con.commit()
            return category
        except sqlite3.Error as e:
            con.rollback()
            raise (e)


def get_task_by_id_db(
    task_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> Task | None:
    query_str = """
    SELECT
        t.*,
        COALESCE(
            (SELECT json_group_array(d.depends_on_task_id)
             FROM dependencies d
             WHERE d.task_id = t.task_id),
            '[]'
        ) as blocked_by,
        COALESCE(
            (SELECT json_group_array(d.task_id)
             FROM dependencies d
             WHERE d.depends_on_task_id = t.task_id),
            '[]'
        ) as blocking
    FROM tasks t
    WHERE t.task_id = :task_id
    ;
    """
    task_id_dict = {"task_id": task_id}

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            task = con.execute(query_str, task_id_dict).fetchone()
            con.commit()
            return task
        except sqlite3.Error as e:
            con.rollback()
            raise (e)


def get_tasks_by_ids_db(
    task_ids: list[int],
    database: str = DATABASE_FILE.as_posix(),
) -> list[Task]:
    """Fetch multiple tasks by their IDs in a single query to avoid N+1 queries.

    Args:
        task_ids: List of task IDs to fetch
        database: Database path

    Returns:
        List of Task objects, in the same order as task_ids
    """
    if not task_ids:
        return []

    # Create placeholders for the IN clause
    placeholders = ",".join("?" * len(task_ids))

    query_str = f"""
    SELECT
        t.*,
        COALESCE(
            (SELECT json_group_array(d.depends_on_task_id)
             FROM dependencies d
             WHERE d.task_id = t.task_id),
            '[]'
        ) as blocked_by,
        COALESCE(
            (SELECT json_group_array(d.task_id)
             FROM dependencies d
             WHERE d.depends_on_task_id = t.task_id),
            '[]'
        ) as blocking
    FROM tasks t
    WHERE t.task_id IN ({placeholders})
    ;
    """

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            tasks = con.execute(query_str, task_ids).fetchall()
            con.commit()

            # Create a mapping for fast lookup and preserve order
            task_map = {task.task_id: task for task in tasks}
            return [task_map[task_id] for task_id in task_ids if task_id in task_map]
        except sqlite3.Error as e:
            con.rollback()
            raise (e)


def get_task_by_column_db(
    column_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> list[Task] | None:
    query_str = """
    SELECT
        t.*,
        COALESCE(
            (SELECT json_group_array(d.depends_on_task_id)
             FROM dependencies d
             WHERE d.task_id = t.task_id),
            '[]'
        ) as blocked_by,
        COALESCE(
            (SELECT json_group_array(d.task_id)
             FROM dependencies d
             WHERE d.depends_on_task_id = t.task_id),
            '[]'
        ) as blocking
    FROM tasks t
    WHERE t.column = :column_id
    ;
    """
    column_id_dict = {"column_id": column_id}

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            task = con.execute(query_str, column_id_dict).fetchall()
            con.commit()
            return task
        except sqlite3.Error as e:
            con.rollback()
            raise (e)


def get_column_by_id_db(
    column_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> Column | None:
    query_str = """
    SELECT *
    FROM columns
    WHERE column_id = :column_id
    ;
    """
    column_id_dict = {"column_id": column_id}

    with create_connection(database=database) as con:
        con.row_factory = column_factory
        try:
            column = con.execute(query_str, column_id_dict).fetchone()
            con.commit()
            return column
        except sqlite3.Error as e:
            con.rollback()
            raise (e)


# After column Movement
def update_task_status_db(task: Task, database: str = DATABASE_FILE.as_posix()) -> Task:
    new_start_date_dict = {
        "task_id": task.task_id,
        "start_date": task.start_date,
        "column": task.column,
        "finish_date": task.finish_date,
        "metadata": json.dumps(task.metadata),
    }
    transaction_str = """
    UPDATE tasks
    SET start_date = :start_date,
        finish_date = :finish_date,
        column = :column,
        metadata = :metadata
    WHERE task_id = :task_id
    RETURNING *;
    """
    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            moved_task = con.execute(transaction_str, new_start_date_dict).fetchone()
            con.commit()
            return moved_task
        except sqlite3.Error as e:
            con.rollback()
            raise e


def update_column_visibility_db(
    column_id: int,
    visible: bool,
    database: str = DATABASE_FILE.as_posix(),
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
            raise e


def switch_column_positions_db(
    current_column_id: int,
    other_column_id: int,
    old_position: int,
    new_position: int,
    database: str = DATABASE_FILE.as_posix(),
) -> int:
    update_column_position_dict = {
        "current_column_id": current_column_id,
        "other_column_id": other_column_id,
        "old_position": old_position,
        "new_position": new_position,
    }

    old_position_transaction_str = """
    UPDATE columns
    SET
        position = :old_position
    WHERE
        column_id = :other_column_id
    ;
    """
    new_position_transaction_str = """
    UPDATE columns
    SET
        position = :new_position
    WHERE
        column_id = :current_column_id
    ;
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(old_position_transaction_str, update_column_position_dict)
            con.execute(new_position_transaction_str, update_column_position_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            raise e


def update_column_name_db(
    column_id: int, new_name: str, database: str = DATABASE_FILE.as_posix()
) -> str | int:
    update_column_name_dict = {"column_id": column_id, "new_name": new_name}

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
            raise e


# After Editing
def update_task_entry_db(
    task_id: int,
    title: str,
    category: int | None = None,
    description: str | None = None,
    due_date: datetime.datetime | None = None,
    metadata: dict[str, Any] | None = None,
    database: str = DATABASE_FILE.as_posix(),
) -> Task:
    update_task_dict = {
        "task_id": task_id,
        "title": title,
        "category": category,
        "description": description,
        "due_date": due_date,
        "metadata": json.dumps(metadata) if metadata is not None else None,
    }

    # Only update metadata if explicitly provided
    if metadata is not None:
        transaction_str = """
        UPDATE tasks
        SET
            title = :title,
            category = :category,
            description = :description,
            due_date = :due_date,
            metadata = :metadata
        WHERE task_id = :task_id;
        """
    else:
        transaction_str = """
        UPDATE tasks
        SET
            title = :title,
            category = :category,
            description = :description,
            due_date = :due_date
        WHERE task_id = :task_id;
        """

    # Query to get the updated task with dependencies
    query_str = """
    SELECT
        t.*,
        COALESCE(
            (SELECT json_group_array(d.depends_on_task_id)
             FROM dependencies d
             WHERE d.task_id = t.task_id),
            '[]'
        ) as blocked_by,
        COALESCE(
            (SELECT json_group_array(d.task_id)
             FROM dependencies d
             WHERE d.depends_on_task_id = t.task_id),
            '[]'
        ) as blocking
    FROM tasks t
    WHERE t.task_id = :task_id
    ;
    """

    with create_connection(database=database) as con:
        con.row_factory = task_factory
        try:
            con.execute(transaction_str, update_task_dict)
            updated_task = con.execute(query_str, {"task_id": task_id}).fetchone()
            con.commit()
            return updated_task
        except sqlite3.Error as e:
            con.rollback()
            raise e


def delete_column_db(
    column_id: int,
    position: int,
    board_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> Column:
    delete_str = """
    DELETE FROM columns
    WHERE column_id = :column_id
    RETURNING *
    """
    update_other_positions_str = """
    UPDATE columns
    SET
        position = position - 1
    WHERE
        board_id = :board_id
        AND position > :position
    ;
    """
    parameter_dict = {
        "column_id": column_id,
        "position": position,
        "board_id": board_id,
    }
    with create_connection(database=database) as con:
        con.row_factory = column_factory
        try:
            deleted_column = con.execute(delete_str, parameter_dict).fetchone()
            con.execute(update_other_positions_str, parameter_dict)
            con.commit()
            return deleted_column
        except sqlite3.Error as e:
            con.rollback()
            raise e


def delete_task_db(task_id: int, database: str = DATABASE_FILE.as_posix()) -> int | str:
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
            raise e


# For Plotting
def get_ordered_tasks_db(
    order_by: str,
    database: str = DATABASE_FILE.as_posix(),
) -> list[dict]:
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
            con.commit()
            return [dict(task) for task in tasks]
        except sqlite3.Error as e:
            con.rollback()
            raise e


# Boards Stuff
# After Editing
def update_board_entry_db(
    board_id: int,
    name: str,
    icon: str | None = None,
    database: str = DATABASE_FILE.as_posix(),
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
            raise e


def delete_board_db(board_id: int, database: str = DATABASE_FILE.as_posix()) -> int:
    delete_board_str = """
    DELETE FROM boards
    WHERE board_id = ?
    """

    delete_task_str = """
    DELETE FROM tasks
    WHERE task_id in (
        SELECT t.task_id FROM tasks t
        INNER JOIN columns c ON c.column_id = t.column
        WHERE c.board_id = ?
    )
    """

    delete_column_str = """
    DELETE FROM columns
    WHERE board_id = ?
    """
    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            # Delete in correct order to respect foreign key constraints:
            # 1. Tasks (reference columns)
            # 2. Columns (reference board)
            # 3. Board
            con.execute(delete_task_str, (board_id,))
            con.execute(delete_column_str, (board_id,))
            con.execute(delete_board_str, (board_id,))
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            raise e


def get_board_info_dict(
    database: str = DATABASE_FILE.as_posix(),
) -> list[dict]:
    query_str = """
    SELECT
    b.board_id AS board_id,
    COUNT(DISTINCT t.task_id) AS amount_tasks,
    COUNT(DISTINCT c.column_id) AS amount_columns,
    MIN(t.due_date) AS next_due
    FROM boards b
    LEFT JOIN columns c ON b.board_id = c.board_id
    LEFT JOIN tasks t ON c.column_id = t.column
    GROUP BY b.board_id;
    """

    with create_connection(database=database) as con:
        con.row_factory = board_info_factory
        try:
            board_infos = con.execute(query_str).fetchall()
            con.commit()
            return board_infos
        except sqlite3.Error as e:
            con.rollback()
            raise Exception(e)


def get_filtered_events_db(
    database: str = DATABASE_FILE.as_posix(),
    filter: dict[str, Sequence[Any]] | None = None,
) -> list[LogEvent]:
    if not filter:
        query_str = """
        SELECT
            *
        FROM
            audits;
        """
    else:
        params = *filter["events"], *filter["objects"], filter["time"]
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
            con.commit()
            return events
        except sqlite3.Error as e:
            con.rollback()
            raise Exception(e)


# Task Dependencies Management


def create_task_dependency_db(
    task_id: int,
    depends_on_task_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> int:
    dependency_dict = {
        "task_id": task_id,
        "depends_on_task_id": depends_on_task_id,
    }

    # Check for circular dependencies before inserting
    if would_create_cycle(task_id, depends_on_task_id, database):
        raise ValueError(
            f"Creating dependency from task {task_id} to task {depends_on_task_id} "
            "would create a circular dependency"
        )

    transaction_str = """
    INSERT INTO dependencies
    VALUES (
        NULL,
        :task_id,
        :depends_on_task_id
    )
    RETURNING dependency_id
    ;"""

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            result = con.execute(transaction_str, dependency_dict).fetchone()
            con.commit()
            return result[0]
        except sqlite3.Error as e:
            con.rollback()
            raise e


def delete_task_dependency_db(
    task_id: int,
    depends_on_task_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> int:
    dependency_dict = {
        "task_id": task_id,
        "depends_on_task_id": depends_on_task_id,
    }

    delete_str = """
    DELETE FROM dependencies
    WHERE task_id = :task_id AND depends_on_task_id = :depends_on_task_id
    """

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            con.execute(delete_str, dependency_dict)
            con.commit()
            return 0
        except sqlite3.Error as e:
            con.rollback()
            raise e


def get_task_dependencies_db(
    task_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> list[int]:
    query_str = """
    SELECT depends_on_task_id
    FROM dependencies
    WHERE task_id = :task_id
    ORDER BY depends_on_task_id
    ;
    """
    task_id_dict = {"task_id": task_id}

    with create_connection(database=database) as con:
        con.row_factory = sqlite3.Row
        try:
            results = con.execute(query_str, task_id_dict).fetchall()
            con.commit()
            return [row[0] for row in results]
        except sqlite3.Error as e:
            con.rollback()
            raise e


def would_create_cycle(
    task_id: int,
    depends_on_task_id: int,
    database: str = DATABASE_FILE.as_posix(),
) -> bool:
    # Self-dependency is always a cycle
    if task_id == depends_on_task_id:
        return True

    # Check if depends_on_task_id eventually depends on task_id
    # If so, creating task_id -> depends_on_task_id would create a cycle
    visited = set()
    stack = [depends_on_task_id]

    while stack:
        current = stack.pop()
        if current == task_id:
            return True

        if current in visited:
            continue

        visited.add(current)

        # Get all tasks that current depends on
        dependencies = get_task_dependencies_db(current, database)
        stack.extend(dependencies)

    return False
