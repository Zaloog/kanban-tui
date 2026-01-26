import os
from pathlib import Path

from kanban_tui.backends.jira.backend import JiraBackend
from kanban_tui.config import Settings, init_config
from kanban_tui.constants import AUTH_FILE


def test_read_sample_theme_from_env() -> None:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = (
        Path(__file__).parent / "sample-configs/new_theme.toml"
    ).as_posix()
    config = Settings()
    assert config.board.theme == "test_theme"


def test_read_sample_jira_backend_from_env(
    test_jira_config: Settings, test_auth_path
) -> None:
    assert test_jira_config.backend.mode == "jira"
    assert test_jira_config.backend.jira_settings.base_url == "http://localhost:8080"
    assert test_jira_config.backend.jira_settings.auth_file_path == test_auth_path


def test_read_sample_sqlite_backend_from_env() -> None:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = (
        Path(__file__).parent / "sample-configs/sqlite_backend.toml"
    ).as_posix()
    config = Settings()
    assert config.backend.mode == "sqlite"
    assert config.backend.sqlite_settings.database_path == "/home/kanban_tui.db"
    assert config.backend.sqlite_settings.active_board_id == 2


def test_config_theme_update(test_config: Settings) -> None:
    test_config.set_theme("monokai")
    assert test_config.board.theme == "monokai"

    updated_config = Settings()
    assert updated_config.board.theme == "monokai"


def test_config_creation(
    test_config: Settings,
    test_config_path: str,
    test_database_path: str,
) -> None:
    assert Path(test_config_path).exists()

    assert (
        init_config(config_path=test_config_path, database=test_database_path)
        == "Config Exists"
    )


def test_auth_dir_creation(test_jira_config: Settings, test_auth_path) -> None:
    os.environ["KANBAN_TUI_AUTH_FILE"] = test_auth_path

    backend = JiraBackend(settings=test_jira_config.backend.jira_settings)
    assert backend.settings.base_url == "http://localhost:8080"
    assert backend.settings.auth_file_path == test_auth_path
    assert Path(test_auth_path).exists()


def test_default_config(test_config: Settings, test_database_path: str) -> None:
    settings_dict = test_config.model_dump()  # serialize_as_any=True)
    default_settings = {
        "board": {
            "theme": "dracula",
            "columns_in_view": 3,
        },
        "task": {
            "always_expanded": False,
            "default_color": "#004578",
            "movement_mode": "adjacent",
        },
        "backend": {
            "mode": "sqlite",
            "sqlite_settings": {
                "database_path": test_database_path,
                "active_board_id": 1,
            },
            "claude_settings": {
                "active_session_id": "",
                "tasks_base_path": "~/.claude/tasks",
            },
            "jira_settings": {
                "base_url": "",
                "auth_file_path": AUTH_FILE.as_posix(),
                "jqls": [],
                "status_to_column_map": {
                    "Done": 3,
                    "In Progress": 2,
                    "To Do": 1,
                },
                "active_jql": 1,
            },
        },
    }
    assert settings_dict == default_settings
