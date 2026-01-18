import sqlite3
from pathlib import Path

import pytest

from kanban_tui.backends.sqlite.database import (
    create_new_category_db,
    get_all_categories_db,
    get_category_by_id_db,
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


async def test_init_new_db(test_database_path):
    init_new_db(database=test_database_path)

    assert Path(test_database_path).exists()
    assert init_new_db(database=test_database_path) is None

    with pytest.raises(sqlite3.OperationalError):
        with create_connection(database=test_database_path) as con:
            try:
                con.execute("CREATE TABLE tasks(test_id );")
            except Exception as e:
                con.rollback()
                con.close()
                raise e


def test_task_factory(test_app, test_database_path):
    with create_connection(database=test_database_path) as con:
        con.row_factory = task_factory
        row = con.execute("SELECT * from tasks WHERE task_id = 1").fetchone()
        assert isinstance(row, Task)


def test_column_factory(test_app, test_database_path):
    with create_connection(database=test_database_path) as con:
        con.row_factory = column_factory
        row = con.execute("SELECT * from columns WHERE board_id = 1").fetchone()
        assert isinstance(row, Column)


def test_board_factory(test_app, test_database_path):
    with create_connection(database=test_database_path) as con:
        con.row_factory = board_factory
        row = con.execute("SELECT * from boards WHERE board_id = 1").fetchone()
        assert isinstance(row, Board)


def test_logevent_factory(test_app, test_database_path):
    with create_connection(database=test_database_path) as con:
        con.row_factory = logevent_factory
        row = con.execute("SELECT * from audits WHERE event_id = 1").fetchone()
        assert isinstance(row, LogEvent)

        assert row.object_type == "board"
        assert row.event_type == "CREATE"


def test_board_info_factory(test_app, test_database_path):
    info_str = """
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
    with create_connection(database=test_database_path) as con:
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


def test_create_new_board_db(test_app, test_database_path):
    for name, icon in zip(["TestDB1", "TestDB2"], [":Icon1:", ":Icon2:"]):
        create_new_board_db(name=name, icon=icon, database=test_database_path)

    boards = get_all_boards_db(database=test_database_path)
    assert len(boards) == 3


def test_create_new_category_db(no_task_app, test_database_path):
    for name, color in zip(["green", "red"], ["#00FF00", "#FF0000"]):
        create_new_category_db(name=name, color=color, database=test_database_path)

    categories = get_all_categories_db(database=test_database_path)
    assert len(categories) == 2


@pytest.mark.parametrize(
    "category_id, name, color",
    [
        (1, "red", "#FF0000"),
        (2, "green", "#00FF00"),
    ],
)
def test_get_category_db(test_app, test_database_path, category_id, name, color):
    category = get_category_by_id_db(
        category_id=category_id, database=test_database_path
    )
    assert category.name == name
    assert category.color == color


def test_create_board_sets_default_status_columns(test_database_path):
    """Test that creating a board with default columns automatically sets status columns"""
    init_new_db(database=test_database_path)

    # Create board with default column layout
    new_board = create_new_board_db(
        name="Test Board", icon=":rocket:", database=test_database_path
    )

    # Verify status columns are set
    assert new_board.reset_column is not None
    assert new_board.start_column is not None
    assert new_board.finish_column is not None

    # Verify they point to the correct columns (Ready, Doing, Done)
    boards = get_all_boards_db(database=test_database_path)
    created_board = [b for b in boards if b.board_id == new_board.board_id][0]

    assert created_board.reset_column == new_board.reset_column
    assert created_board.start_column == new_board.start_column
    assert created_board.finish_column == new_board.finish_column


def test_create_board_with_custom_columns_no_status_columns(test_database_path):
    """Test that custom column layouts don't automatically set status columns"""
    init_new_db(database=test_database_path)

    # Create board with custom columns
    custom_columns = {"Backlog": True, "In Progress": True, "Review": True}
    new_board = create_new_board_db(
        name="Custom Board",
        icon=":gear:",
        column_dict=custom_columns,
        database=test_database_path,
    )

    # Verify status columns are NOT set
    assert new_board.reset_column is None
    assert new_board.start_column is None
    assert new_board.finish_column is None
