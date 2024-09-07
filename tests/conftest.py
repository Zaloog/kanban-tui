import pytest

from kanban_tui.constants import CONFIG_NAME, DB_NAME
from kanban_tui.config import init_new_config, KanbanTuiConfig
from kanban_tui.database import init_new_db, create_new_task_db


# Paths
@pytest.fixture
def test_file_location(tmp_path):
    return tmp_path


@pytest.fixture
def test_config_full_path(test_file_location):
    return test_file_location / CONFIG_NAME


@pytest.fixture
def test_db_full_path(test_file_location):
    return test_file_location / DB_NAME


# Init Config and DB
@pytest.fixture
def test_app_config(test_config_full_path, test_db_full_path) -> KanbanTuiConfig:
    init_new_config(config_path=test_config_full_path, database=test_db_full_path)

    cfg = KanbanTuiConfig(config_path=test_config_full_path)
    return cfg


@pytest.fixture
def init_test_db(test_db_full_path):
    init_new_db(database=test_db_full_path)


@pytest.fixture
def seed_db(test_db_full_path):
    # Ready
    create_new_task_db(
        title="Task_green_ready",
        description="Hallo",
        category="green",
        column="Ready",
        database=test_db_full_path,
    )
    create_new_task_db(
        title="Task_blue_ready",
        description="Hallo",
        category="blue",
        column="Ready",
        database=test_db_full_path,
    )
    create_new_task_db(
        title="Task_none_ready",
        description="Hallo",
        category=None,
        column="Ready",
        database=test_db_full_path,
    )

    # Doing
    create_new_task_db(
        title="Task_green_doing",
        description="Hallo",
        category="green",
        column="Doing",
        database=test_db_full_path,
    )
    # Done
    create_new_task_db(
        title="Task_red_done",
        description="Hallo",
        category="red",
        column="Done",
        database=test_db_full_path,
    )
