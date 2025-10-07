from pathlib import Path

from kanban_tui.app import KanbanTui
from kanban_tui.backends.sqlite.backend import SqliteBackend
from kanban_tui.views.kanbanboard_tab_view import KanbanBoard
from kanban_tui.views.main_view import MainView

APP_SIZE = (150, 50)


async def test_empty_app(
    empty_app: KanbanTui, test_config_path: str, test_database_path: str
):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 0
        assert isinstance(pilot.app.screen, MainView)

        assert Path(test_database_path).exists()
        assert Path(test_config_path).exists()


async def test_app(test_app: KanbanTui, test_config_path: str, test_database_path: str):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 5
        assert isinstance(pilot.app.screen, MainView)

        assert Path(test_database_path).exists()
        assert Path(test_config_path).exists()


async def test_app_no_visible_tasks(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 5

        # delete only task in doing column
        await pilot.press("l")
        await pilot.press("d")
        await pilot.click("#btn_continue_delete")

        # Only make doing col visible
        await pilot.press("ctrl+l")
        await pilot.press("ctrl+c")
        await pilot.press("j")
        await pilot.press("space")
        await pilot.press(*"jj")
        await pilot.press("space")
        await pilot.press("ctrl+j")

        assert isinstance(pilot.app.focused, KanbanBoard)


async def test_app_properties(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 5

        assert pilot.app.visible_column_dict == {1: "Ready", 2: "Doing", 3: "Done"}

        assert not pilot.app.demo_mode
        assert pilot.app.backend.active_board.board_id == 1


async def test_app_correct_backend_type(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert isinstance(pilot.app.backend, SqliteBackend)


async def test_app_correct_backend_settings(
    test_app: KanbanTui, test_database_path: str
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert pilot.app.backend.settings.database_path == test_database_path
        assert pilot.app.backend.settings.active_board_id == 1


async def test_app_backend_settings_change(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert pilot.app.backend.settings.active_board_id == 1

        pilot.app.config.set_active_board(2)
        assert pilot.app.backend.settings.active_board_id == 2


async def test_app_refresh(
    test_app: KanbanTui, test_config_path: str, test_database_path: str
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 5
        assert isinstance(pilot.app.screen, MainView)

        pilot.app.backend.delete_task(task_id=1)
        assert len(pilot.app.task_list) == 5

        # refresh app
        await pilot.press("f5")
        assert len(pilot.app.task_list) == 4
