import pytest

from kanban_tui.constants import CONFIG_NAME, DB_NAME
from kanban_tui.config import init_new_config, KanbanTuiConfig
from kanban_tui.database import init_new_db, create_new_task_db, create_new_board_db
from kanban_tui.app import KanbanTui


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
def init_test_db(test_db_full_path, test_app_config: KanbanTuiConfig):
    init_new_db(database=test_db_full_path)
    # Ready 3
    create_new_board_db(name="Test_Board", icon=":bug:", database=test_db_full_path)

    create_new_task_db(
        title="Task_ready_0",
        description="Hallo",
        category="green",
        column=1,
        board_id=test_app_config.active_board,
        database=test_db_full_path,
    )
    create_new_task_db(
        title="Task_ready_1",
        description="Hallo",
        category="blue",
        column=1,
        board_id=test_app_config.active_board,
        database=test_db_full_path,
    )
    create_new_task_db(
        title="Task_ready_2",
        description="Hallo",
        category=None,
        column=1,
        board_id=test_app_config.active_board,
        database=test_db_full_path,
    )

    # Doing 1
    create_new_task_db(
        title="Task_doing_0",
        description="Hallo",
        category="green",
        column=2,
        board_id=test_app_config.active_board,
        database=test_db_full_path,
    )
    # Done 1
    create_new_task_db(
        title="Task_done_0",
        description="Hallo",
        category="red",
        column=3,
        board_id=test_app_config.active_board,
        database=test_db_full_path,
    )


@pytest.fixture
def empty_app(test_config_full_path, test_db_full_path):
    return KanbanTui(config_path=test_config_full_path, database_path=test_db_full_path)


@pytest.fixture
def test_app(test_config_full_path, test_db_full_path, init_test_db, test_app_config):
    # with initialized test_db
    # add categories to config
    cfg = test_app_config
    cfg.add_category(
        category="green",
        color="#00FF00",
    )
    cfg.add_category(
        category="blue",
        color="#0000FF",
    )
    cfg.add_category(
        category="red",
        color="#FF0000",
    )

    return KanbanTui(config_path=test_config_full_path, database_path=test_db_full_path)
