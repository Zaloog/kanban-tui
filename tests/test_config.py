from pathlib import Path

from kanban_tui.config import KanbanTuiConfig, init_new_config


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
