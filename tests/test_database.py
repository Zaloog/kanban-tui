import sqlite3

import pytest

from kanban_tui.database import (
    init_new_db,
    create_connection,
    task_factory,
    board_factory,
    logevent_factory,
    board_info_factory,
    column_factory,
    create_new_board_db,
    get_all_boards_db,
)
from kanban_tui.classes.task import Task
from kanban_tui.classes.column import Column
from kanban_tui.classes.board import Board
from kanban_tui.classes.logevent import LogEvent


def test_init_new_db(test_db_full_path):
    init_new_db(database=test_db_full_path)

    assert test_db_full_path.exists()
    assert init_new_db(database=test_db_full_path) is None

    with pytest.raises(sqlite3.OperationalError):
        with create_connection(database=test_db_full_path) as con:
            con.execute("CREATE TABLE tasks(test_id );")


def test_task_factory(init_test_db, test_db_full_path):
    with create_connection(database=test_db_full_path) as con:
        con.row_factory = task_factory
        row = con.execute("SELECT * from tasks WHERE task_id = 1").fetchone()
        assert isinstance(row, Task)


def test_column_factory(init_test_db, test_db_full_path):
    with create_connection(database=test_db_full_path) as con:
        con.row_factory = column_factory
        row = con.execute("SELECT * from columns WHERE board_id = 1").fetchone()
        assert isinstance(row, Column)


def test_board_factory(init_test_db, test_db_full_path):
    with create_connection(database=test_db_full_path) as con:
        con.row_factory = board_factory
        row = con.execute("SELECT * from boards WHERE board_id = 1").fetchone()
        assert isinstance(row, Board)


def test_logevent_factory(init_test_db, test_db_full_path):
    with create_connection(database=test_db_full_path) as con:
        con.row_factory = logevent_factory
        row = con.execute("SELECT * from audits WHERE event_id = 1").fetchone()
        assert isinstance(row, LogEvent)

        assert row.object_type == "board"
        assert row.event_type == "CREATE"


def test_board_info_factory(init_test_db, test_db_full_path):
    info_str = """
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
    with create_connection(database=test_db_full_path) as con:
        con.row_factory = board_info_factory
        info_dict = con.execute(info_str).fetchone()
        print(info_dict)
        assert isinstance(info_dict, dict)
        assert info_dict == {
            "board_id": 1,
            "amount_tasks": 5,
            "amount_columns": 4,
            "next_due": None,
        }


def test_create_new_board_db(init_test_db, test_db_full_path):
    for name, icon in zip(["TestDB1", "TestDB2"], [":Icon1:", ":Icon2:"]):
        create_new_board_db(name=name, icon=icon, database=test_db_full_path)

    boards = get_all_boards_db(database=test_db_full_path)
    assert len(boards) == 3
