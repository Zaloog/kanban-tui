import pytest

from kanban_tui.database import init_new_db, create_connection
from sqlite3 import OperationalError


def test_init_new_db(test_db_full_path):
    init_new_db(database=test_db_full_path)

    assert test_db_full_path.exists()
    assert init_new_db(database=test_db_full_path) is None

    with pytest.raises(OperationalError):
        with create_connection(database=test_db_full_path) as con:
            con.execute("CREATE TABLE tasks(test_id );")
