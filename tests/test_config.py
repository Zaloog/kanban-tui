from kanban_tui.config import KanbanTuiConfig, init_new_config


def test_init_new_config(test_app_config, test_config_full_path, test_db_full_path):
    assert test_config_full_path.exists()

    assert (
        init_new_config(config_path=test_config_full_path, database=test_db_full_path)
        is None
    )

    # Test Sections exist
    assert "database" in test_app_config.config.sections()
    assert "category.colors" in test_app_config.config.sections()
    assert "column.visibility" in test_app_config.config.sections()
    assert "kanban.settings" in test_app_config.config.sections()

    assert test_app_config.database_path == test_db_full_path
    assert test_app_config.tasks_always_expanded is False
    assert test_app_config.category_color_dict == {}
    assert test_app_config.visible_columns == ["Ready", "Doing", "Done"]
    assert test_app_config.columns == ["Ready", "Doing", "Done", "Archive"]
    assert test_app_config.column_dict == {
        "Ready": True,
        "Doing": True,
        "Done": True,
        "Archive": False,
    }
    assert test_app_config.no_category_task_color == "#004578"


def test_KanbanTuiConfig(test_app_config: KanbanTuiConfig, test_config_full_path):
    test_app_config.set_tasks_always_expanded(new_value=True)
    assert test_app_config.tasks_always_expanded is True

    test_app_config.set_no_category_task_color(new_color="#000000")
    assert test_app_config.no_category_task_color == "#000000"

    test_app_config.add_new_column(new_column="TestColumn", position=2)
    assert test_app_config.column_dict["TestColumn"] is True
    assert test_app_config.columns[2] == "TestColumn"

    test_app_config.set_column_dict(column_name="Archive")
    assert test_app_config.column_dict["Archive"] is True

    test_app_config.add_category(category="Test", color="#000000")
    assert test_app_config.category_color_dict["Test"] == "#000000"

    updated_config = KanbanTuiConfig(config_path=test_config_full_path)

    assert updated_config.tasks_always_expanded is True
    assert updated_config.no_category_task_color == "#000000"
    assert updated_config.column_dict["TestColumn"] is True
    assert updated_config.columns[2] == "TestColumn"
    assert updated_config.column_dict["Archive"] is True
    assert updated_config.category_color_dict["Test"] == "#000000"
