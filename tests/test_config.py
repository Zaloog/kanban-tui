import os
from pathlib import Path

from kanban_tui.config import KanbanTuiConfig, Settings, init_new_config, init_config


def test_KanbanTuiConfig(
    test_app_config: KanbanTuiConfig, test_config_full_path: Path
) -> None:
    test_app_config.set_tasks_always_expanded(new_value=True)
    assert test_app_config.tasks_always_expanded is True

    test_app_config.set_no_category_task_color(new_color="#000000")
    assert test_app_config.no_category_task_color == "#000000"

    test_app_config.set_active_board(new_active_board=2)
    assert test_app_config.active_board == 2

    test_app_config.add_category(category="Test", color="#000000")
    assert test_app_config.category_color_dict["Test"] == "#000000"

    test_app_config.set_work_hour_dict(entry="start_hour", new_value="08")
    assert test_app_config.work_hour_dict["start_hour"] == "08"

    updated_config = KanbanTuiConfig(config_path=test_config_full_path)

    assert updated_config.tasks_always_expanded is True
    assert updated_config.no_category_task_color == "#000000"
    assert updated_config.category_color_dict["Test"] == "#000000"
    assert test_app_config.work_hour_dict["start_hour"] == "08"


def test_init_new_config(
    test_app_config: KanbanTuiConfig,
    test_config_full_path: Path,
    test_db_full_path: Path,
) -> None:
    assert test_config_full_path.exists()

    assert (
        init_new_config(config_path=test_config_full_path, database=test_db_full_path)
        == "Config Exists"
    )

    # Test Sections exist
    assert "database" in test_app_config.config
    assert "category.colors" in test_app_config.config
    assert "kanban.settings" in test_app_config.config

    assert test_app_config.database_path == test_db_full_path
    assert test_app_config.tasks_always_expanded is False
    assert test_app_config.category_color_dict == {}
    assert test_app_config.active_board == 1
    assert test_app_config.no_category_task_color == "#004578"
    assert test_app_config.work_hour_dict == {
        "start_hour": "00",
        "start_min": "00",
        "end_hour": "00",
        "end_min": "00",
    }


def test_default_theme_is_loaded(test_app_config: KanbanTuiConfig) -> None:
    assert test_app_config.theme == "dracula"


def test_theme_update_is_saved(
    test_app_config: KanbanTuiConfig, test_config_full_path: Path
) -> None:
    test_app_config.set_theme("monokai")
    assert test_app_config.theme == "monokai"

    updated_config = KanbanTuiConfig(config_path=test_config_full_path)
    assert updated_config.theme == "monokai"


def test_read_sample_theme_from_env() -> None:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = (
        Path(__file__).parent / "sample-configs/new_theme.toml"
    ).as_posix()
    config = Settings()
    assert config.board.theme == "test_theme"


def test_read_sample_jira_backend_from_env() -> None:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = (
        Path(__file__).parent / "sample-configs/jira_backend.toml"
    ).as_posix()
    config = Settings()
    assert config.backend.mode == "jira"
    assert config.backend.jira_settings.url == "www.test-url.com"
    assert config.backend.jira_settings.user == "Zaloog"
    assert config.backend.jira_settings.api_token == "1337"


def test_read_sample_sqlite_backend_from_env() -> None:
    os.environ["KANBAN_TUI_CONFIG_FILE"] = (
        Path(__file__).parent / "sample-configs/sqlite_backend.toml"
    ).as_posix()
    config = Settings()
    assert config.backend.mode == "sqlite"
    assert config.backend.sqlite_settings.database_path == "/home/kanban_tui.db"
    assert config.backend.sqlite_settings.active_board_id == 2


def test_config_theme_update(test_config: Settings, test_config_path: Path) -> None:
    test_config.set_theme("monokai")
    assert test_config.board.theme == "monokai"

    updated_config = Settings()
    assert updated_config.board.theme == "monokai"


def test_config_creation(
    test_config: Settings,
    test_config_path: Path,
    test_db_full_path: Path,
) -> None:
    assert test_config_path.exists()

    assert (
        init_config(config_path=test_config_path, database=test_db_full_path)
        == "Config Exists"
    )


def test_default_config(test_config: Settings, test_db_full_path) -> None:
    settings_dict = test_config.model_dump(serialize_as_any=True)
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
                "database_path": test_db_full_path.as_posix(),
                "active_board_id": 1,
            },
            "jira_settings": {
                "user": "",
                "api_token": "",
                "url": "",
            },
        },
    }
    assert settings_dict == default_settings
