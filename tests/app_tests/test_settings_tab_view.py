from kanban_tui.app import KanbanTui
from textual.widgets import Input, Switch
from kanban_tui.views.main_view import MainView


APP_SIZE = (120, 80)


async def test_settings_view_empty(empty_app: KanbanTui, test_db_full_path):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        assert isinstance(pilot.app.screen, MainView)
        assert isinstance(pilot.app.focused, Input)
        assert pilot.app.focused.value == test_db_full_path.as_posix()


async def test_settings_view(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        assert isinstance(pilot.app.screen, MainView)
        assert isinstance(pilot.app.focused, Input)
        assert pilot.app.focused.value == test_db_full_path.as_posix()


async def test_task_expand_switch(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        assert isinstance(pilot.app.focused, Input)
        # toggle Switch
        assert not pilot.app.cfg.tasks_always_expanded
        assert not pilot.app.query_exactly_one("#switch_expand_tasks", Switch).value
        await pilot.click("#switch_expand_tasks")
        assert pilot.app.query_exactly_one("#switch_expand_tasks", Switch).value
        assert pilot.app.cfg.tasks_always_expanded
