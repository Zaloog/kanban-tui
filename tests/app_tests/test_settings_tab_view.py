import pytest
from kanban_tui.app import KanbanTui
from textual.widgets import Input, Switch, Button
from kanban_tui.views.main_view import MainView, SettingsView
from kanban_tui.widgets.settings_widgets import ColumnSelector, AddRule
from kanban_tui.modal.modal_settings import ModalNewColumnScreen
from kanban_tui.modal.modal_task_screen import ModalConfirmScreen


APP_SIZE = (120, 80)


async def test_settings_view_empty(empty_app: KanbanTui, test_db_full_path):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MainView)
        await pilot.click("#input_database_path")
        assert isinstance(pilot.app.focused, Input)
        assert pilot.app.focused.value == test_db_full_path.as_posix()


async def test_settings_view(test_app: KanbanTui, test_db_full_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MainView)
        await pilot.click("#input_database_path")
        assert isinstance(pilot.app.focused, Input)
        assert pilot.app.focused.value == test_db_full_path.as_posix()


async def test_task_expand_switch(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")

        assert not pilot.app.cfg.tasks_always_expanded
        assert not pilot.app.query_exactly_one("#switch_expand_tasks", Switch).value
        assert not pilot.app.query_exactly_one(SettingsView).config_has_changed

        # toggle Switch
        await pilot.click("#switch_expand_tasks")
        assert pilot.app.query_exactly_one("#switch_expand_tasks", Switch).value
        assert pilot.app.cfg.tasks_always_expanded
        assert pilot.app.query_exactly_one(SettingsView).config_has_changed


async def test_column_selector(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)


async def test_column_selector_navigation(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready Item
        await pilot.press(*"jj")
        assert isinstance(pilot.app.focused, ColumnSelector)
        assert pilot.app.focused.highlighted_child.id == "listitem_column_1"

        await pilot.press(*"jj")
        assert pilot.app.focused.highlighted_child.id == "listitem_column_3"


async def test_column_visibility(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready ColumnItem
        await pilot.press(*"jj")
        assert isinstance(pilot.app.focused, ColumnSelector)
        assert pilot.app.focused.highlighted_child.id == "listitem_column_1"

        # toggle visibility
        await pilot.press("space")
        assert pilot.app.visible_column_list == ["Doing", "Done"]

        # Go to Archive ColumnItem
        await pilot.press(*"jjj")
        assert pilot.app.focused.highlighted_child.id == "listitem_column_4"

        await pilot.press("space")
        assert pilot.app.visible_column_list == ["Doing", "Done", "Archive"]


async def test_column_delete_press(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready Item
        await pilot.press(*"jj")
        assert isinstance(pilot.app.focused, ColumnSelector)
        # Delete Column
        await pilot.press("d")
        assert isinstance(pilot.app.screen, ModalConfirmScreen)
        await pilot.press("enter")
        assert isinstance(pilot.app.screen, MainView)
        assert len(pilot.app.column_list) == 3
        assert pilot.app.visible_column_list == ["Doing", "Done"]


async def test_column_delete_click(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready Item
        await pilot.press(*"jj")
        assert isinstance(pilot.app.focused, ColumnSelector)
        # Delete Column
        await pilot.press("d")
        assert isinstance(pilot.app.screen, ModalConfirmScreen)
        await pilot.click("#btn_continue_delete")
        assert isinstance(pilot.app.screen, MainView)
        assert len(pilot.app.column_list) == 3
        assert pilot.app.visible_column_list == ["Doing", "Done"]


@pytest.mark.parametrize(
    "column_name, position, column_list",
    [
        ("Zero", 0, ["Zero", "Ready", "Doing", "Done"]),
        ("One", 1, ["Ready", "One", "Doing", "Done"]),
        ("Two", 2, ["Ready", "Doing", "Two", "Done"]),
    ],
)
async def test_column_creation(test_app: KanbanTui, column_name, position, column_list):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        await pilot.click(pilot.app.query(AddRule)[position].query_exactly_one(Button))
        assert isinstance(pilot.app.screen, ModalNewColumnScreen)

        await pilot.press(*column_name)
        await pilot.click("#btn_continue_new_col")

        assert pilot.app.visible_column_list == column_list


async def test_column_creation_cancel_press(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Click on First Position
        await pilot.click(pilot.app.query(AddRule)[0].query_exactly_one(Button))
        assert isinstance(pilot.app.screen, ModalNewColumnScreen)

        # Cancel Modal View
        await pilot.press("escape")
        assert isinstance(pilot.app.screen, MainView)


async def test_column_creation_cancel_click(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Click on First Position
        await pilot.click(pilot.app.query(AddRule)[0].query_exactly_one(Button))
        assert isinstance(pilot.app.screen, ModalNewColumnScreen)

        # Cancel Modal View
        await pilot.click("#btn_cancel_new_col")
        assert isinstance(pilot.app.screen, MainView)
