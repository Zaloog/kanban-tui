import os
from pathlib import Path

import pytest

from kanban_tui.constants import AUTH_NAME, CONFIG_NAME, DATABASE_NAME
from kanban_tui.config import Settings, init_config
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


@pytest.fixture
def test_auth_path(test_file_location: Path) -> str:
    directory = test_file_location / "auth"
    directory.mkdir(exist_ok=True)
    yield (directory / AUTH_NAME).as_posix()


# Init Config
@pytest.fixture
def test_config(test_config_path: str, test_database_path: str) -> Settings:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = test_config_path
    init_config(config_path=test_config_path, database=test_database_path)

    cfg = Settings()
    yield cfg


@pytest.fixture
def test_jira_config(test_config_path, test_auth_path) -> Settings:
    config_path = Path(__file__).parent / "sample-configs/jira_backend.toml"
    os.environ["KANBAN_TUI_CONFIG_FILE"] = config_path.as_posix()

    cfg = Settings()
    cfg.backend.jira_settings.auth_file_path = test_auth_path
    yield cfg


@pytest.fixture
def test_auth_file():
    config_path = Path(__file__).parent / "sample-configs/sample_auth.toml"
    os.environ["KANBAN_TUI_AUTH_FILE"] = config_path.as_posix()


@pytest.fixture
def empty_app(test_config_path, test_database_path, test_config):
    yield KanbanTui(config_path=test_config_path, database_path=test_database_path)


@pytest.fixture
def no_task_app(test_config_path, test_database_path, test_config):
    app = KanbanTui(config_path=test_config_path, database_path=test_database_path)
    app.backend.create_new_board(
        name="Kanban Board",
        icon=":sparkles:",
    )

    yield app


# Create Testapp and inject test tasks
@pytest.fixture
# def test_app(test_config_path, test_database_path, test_config: Settings):
def test_app(no_task_app):
    # TODO
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
    # app = KanbanTui(config_path=test_config_path, database_path=test_database_path)

    no_task_app.backend.create_new_task(
        title="Task_ready_0",
        description="Hallo",
        # category="green",
        column=1,
    )
    no_task_app.backend.create_new_task(
        title="Task_ready_1",
        description="Hallo",
        # category="blue",
        column=1,
    )
    no_task_app.backend.create_new_task(
        title="Task_ready_2",
        description="Hallo",
        category=None,
        column=1,
    )

    # Doing, 1 Task
    no_task_app.backend.create_new_task(
        title="Task_doing_0",
        description="Hallo",
        # category="green",
        column=2,
    )
    # Done, 1 Task
    no_task_app.backend.create_new_task(
        title="Task_done_0",
        description="Hallo",
        # category="red",
        column=3,
    )

    yield no_task_app
