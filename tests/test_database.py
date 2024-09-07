import pytest

from kanban_tui.database import init_new_db, create_connection, task_factory
from kanban_tui.classes.task import Task
import sqlite3


def test_init_new_db(test_db_full_path):
    init_new_db(database=test_db_full_path)

    assert test_db_full_path.exists()
    assert init_new_db(database=test_db_full_path) is None

    with pytest.raises(sqlite3.OperationalError):
        with create_connection(database=test_db_full_path) as con:
            con.execute("CREATE TABLE tasks(test_id );")


def test_task_factory(test_db, test_db_full_path):
    with create_connection(database=test_db_full_path) as con:
        con.row_factory = task_factory
        row = con.execute("SELECT * from tasks WHERE task_id = 1").fetchone()
        assert isinstance(row, Task)
