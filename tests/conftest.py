import os
from pathlib import Path
from datetime import datetime
from typing_extensions import Generator

import pytest
from freezegun import freeze_time

from kanban_tui.constants import AUTH_NAME, CONFIG_NAME, DATABASE_NAME
from kanban_tui.config import Settings, init_config
from kanban_tui.app import KanbanTui


# Paths
@pytest.fixture
def test_file_location(tmp_path) -> Generator[Path, None, None]:
    yield tmp_path


@pytest.fixture
def test_config_path(test_file_location: Path) -> Generator[str, None, None]:
    yield (test_file_location / CONFIG_NAME).as_posix()


@pytest.fixture
def test_database_path(test_file_location: Path) -> Generator[str, None, None]:
    yield (test_file_location / DATABASE_NAME).as_posix()


@pytest.fixture
def test_auth_path(test_file_location: Path) -> Generator[str, None, None]:
    directory = test_file_location / "auth"
    directory.mkdir(exist_ok=True)

    yield (directory / AUTH_NAME).as_posix()


# Init Config
@pytest.fixture
def test_config(
    test_config_path: str, test_database_path: str
) -> Generator[Settings, None, None]:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = test_config_path
    os.environ["KANBAN_TUI_DATABASE_FILE"] = test_database_path
    init_config(config_path=test_config_path, database=test_database_path)

    cfg = Settings()
    yield cfg


@pytest.fixture
def test_jira_config(
    test_config_path, test_auth_path
) -> Generator[Settings, None, None]:
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
def empty_app(
    test_config_path, test_database_path, test_config
) -> Generator[KanbanTui, None, None]:
    yield KanbanTui(config_path=test_config_path, database_path=test_database_path)


@pytest.fixture
def no_task_app(
    test_config_path, test_database_path, test_config
) -> Generator[KanbanTui, None, None]:
    os.environ["TEXTUAL_ANIMATION"] = "none"
    app = KanbanTui(config_path=test_config_path, database_path=test_database_path)
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        app.backend.create_new_board(
            name="Kanban Board",
            icon=":sparkles:",
        )
    yield app


# Create Testapp and inject test tasks
@pytest.fixture
def test_app(no_task_app: KanbanTui) -> Generator[KanbanTui, None, None]:
    no_task_app.backend.create_new_category(name="red", color="#FF0000")
    no_task_app.backend.create_new_category(name="green", color="#00FF00")
    no_task_app.backend.create_new_category(name="blue", color="#0000FF")

    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        no_task_app.backend.create_new_task(
            title="Task_ready_0",
            description="Hallo",
            category=1,
            column=1,
        )
        no_task_app.backend.create_new_task(
            title="Task_ready_1",
            description="Hallo",
            category=3,
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
            category=2,
            column=2,
        )
        # Done, 1 Task
        no_task_app.backend.create_new_task(
            title="Task_done_0",
            description="Hallo",
            category=1,
            column=3,
        )

    yield no_task_app
