from pathlib import Path

from kanban_tui.app import KanbanTui
from kanban_tui.views.main_view import MainView

APP_SIZE = (120, 80)


async def test_empty_app(
    empty_app: KanbanTui, test_config_full_path: Path, test_db_full_path: Path
):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 0
        assert isinstance(pilot.app.screen, MainView)

        assert test_db_full_path.exists()
        assert test_config_full_path.exists()


async def test_app(
    test_app: KanbanTui, test_config_full_path: Path, test_db_full_path: Path
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 5
        assert isinstance(pilot.app.screen, MainView)
        assert all(
            cfg_val == val
            for cfg_val, val in zip(
                sorted(pilot.app.cfg.category_color_dict.keys()),
                sorted(["red", "green", "blue"]),
            )
        )

        assert test_db_full_path.exists()
        assert test_config_full_path.exists()
