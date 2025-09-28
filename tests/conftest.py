import os
from pathlib import Path

import pytest

from kanban_tui.constants import CONFIG_NAME, DATABASE_NAME
from kanban_tui.config import Settings, init_config
from kanban_tui.backends.sqlite.database import (
    init_new_db,
    create_new_task_db,
    create_new_board_db,
)
from kanban_tui.app import KanbanTui


# Paths
@pytest.fixture
def test_file_location(tmp_path) -> Path:
    yield tmp_path


@pytest.fixture
def test_config_path(test_file_location: Path) -> str:
    yield (test_file_location / CONFIG_NAME).as_posix()


@pytest.fixture
def test_database_path(test_file_location: Path) -> str:
    yield (test_file_location / DATABASE_NAME).as_posix()


# Init Config and DB
@pytest.fixture
def test_config(test_config_path: str, test_database_path: str) -> Settings:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = test_config_path
    init_config(config_path=test_config_path, database=test_database_path)

    cfg = Settings()
    yield cfg


@pytest.fixture
def init_test_db(test_database_path: str, test_config: Settings):
    init_new_db(database=test_database_path)
    # Ready 3
    create_new_board_db(name="Test_Board", icon=":bug:", database=test_database_path)

    create_new_task_db(
        title="Task_ready_0",
        description="Hallo",
        # category="green",
        column=1,
        board_id=test_config.backend.sqlite_settings.active_board_id,
        database=test_database_path,
    )
    create_new_task_db(
        title="Task_ready_1",
        description="Hallo",
        # category="blue",
        column=1,
        board_id=test_config.backend.sqlite_settings.active_board_id,
        database=test_database_path,
    )
    create_new_task_db(
        title="Task_ready_2",
        description="Hallo",
        category=None,
        column=1,
        board_id=test_config.backend.sqlite_settings.active_board_id,
        database=test_database_path,
    )

    # Doing 1
    create_new_task_db(
        title="Task_doing_0",
        description="Hallo",
        # category="green",
        column=2,
        board_id=test_config.backend.sqlite_settings.active_board_id,
        database=test_database_path,
    )
    # Done 1
    create_new_task_db(
        title="Task_done_0",
        description="Hallo",
        # category="red",
        column=3,
        board_id=test_config.backend.sqlite_settings.active_board_id,
        database=test_database_path,
    )


@pytest.fixture
def empty_app(test_config_path, test_database_path, test_config):
    yield KanbanTui(config_path=test_config_path, database_path=test_database_path)


@pytest.fixture
def test_app(test_config_path, test_database_path, init_test_db, test_config: Settings):
    # with initialized test_db
    # add categories to config
    # cfg = test_config
    # cfg.add_category(
    #     category="green",
    #     color="#00FF00",
    # )
    # cfg.add_category(
    #     category="blue",
    #     color="#0000FF",
    # )
    # cfg.add_category(
    #     category="red",
    #     color="#FF0000",
    # )

    yield KanbanTui(config_path=test_config_path, database_path=test_database_path)
