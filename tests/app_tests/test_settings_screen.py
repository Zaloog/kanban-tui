import pytest
from kanban_tui.app import KanbanTui
from textual.widgets import Input, Select, Switch, Button
from kanban_tui.config import MovementModes
from kanban_tui.screens.settings_screen import SettingsScreen
from kanban_tui.widgets.board_widgets import KanbanBoard
from kanban_tui.widgets.settings_widgets import (
    ColumnSelector,
    AddRule,
    DataBasePathInput,
    TaskAlwaysExpandedSwitch,
    StatusColumnSelector,
    TaskDefaultColorSelector,
    TaskMovementSelector,
)
from kanban_tui.modal.modal_settings import ModalUpdateColumnScreen
from kanban_tui.modal.modal_task_screen import ModalConfirmScreen


APP_SIZE = (150, 50)


async def test_settings_view_empty(no_task_app: KanbanTui, test_database_path):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SettingsScreen)
        await pilot.click("#input_database_path")
        assert isinstance(pilot.app.focused, Input)
        assert pilot.app.focused.value == test_database_path


async def test_settings_view(test_app: KanbanTui, test_database_path):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SettingsScreen)
        await pilot.click("#input_database_path")
        assert isinstance(pilot.app.focused, Input)
        assert pilot.app.focused.value == test_database_path


async def test_task_expand_switch(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")

        assert not pilot.app.config.task.always_expanded
        assert not pilot.app.screen.query_exactly_one(
            "#switch_expand_tasks", Switch
        ).value
        assert not pilot.app.config_has_changed

        # toggle Switch
        await pilot.click("#switch_expand_tasks")
        assert pilot.app.screen.query_exactly_one("#switch_expand_tasks", Switch).value
        assert pilot.app.config.task.always_expanded
        assert pilot.app.config_has_changed


async def test_task_movement_mode(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")

        assert pilot.app.config.task.movement_mode == MovementModes.ADJACENT
        assert (
            pilot.app.screen.query_exactly_one("#select_movement_mode", Select).value
            == MovementModes.ADJACENT
        )

        # change Value
        await pilot.click("#select_movement_mode")
        await pilot.press("down")
        await pilot.press("enter")
        assert pilot.app.config.task.movement_mode == MovementModes.JUMP
        assert (
            pilot.app.screen.query_exactly_one("#select_movement_mode", Select).value
            == MovementModes.JUMP
        )
        assert pilot.app.config_has_changed


async def test_board_columns_in_view(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert not pilot.app.screen.query_one(KanbanBoard).scrollbars_enabled[1]
        await pilot.press("ctrl+l")

        assert pilot.app.config.board.columns_in_view == 3
        assert (
            pilot.app.screen.query_exactly_one("#select_columns_in_view", Select).value
            == 3
        )

        # change Value to 2 columns
        await pilot.click("#select_columns_in_view")
        await pilot.press("up")
        await pilot.press("enter")
        assert pilot.app.config.board.columns_in_view == 2
        assert (
            pilot.app.screen.query_exactly_one("#select_columns_in_view", Select).value
            == 2
        )
        assert pilot.app.config_has_changed

        # check columns in view
        await pilot.press("ctrl+j")
        assert pilot.app.screen.query_one(KanbanBoard).scrollbars_enabled[1]


async def test_column_selector(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)


async def test_column_selector_navigation(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready Item
        await pilot.press("j")
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
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready ColumnItem
        await pilot.press("j")
        assert isinstance(pilot.app.focused, ColumnSelector)
        assert pilot.app.focused.highlighted_child.id == "listitem_column_1"

        # toggle visibility
        await pilot.press("space")
        assert pilot.app.visible_column_dict == {2: "Doing", 3: "Done"}

        # Go to Archive ColumnItem
        await pilot.press(*"jjj")
        assert pilot.app.focused.highlighted_child.id == "listitem_column_4"

        await pilot.press("space")
        assert pilot.app.visible_column_dict == {2: "Doing", 3: "Done", 4: "Archive"}


async def test_column_delete_press(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready Item
        await pilot.press("j")
        assert isinstance(pilot.app.focused, ColumnSelector)
        # Delete Column
        await pilot.press("d")
        assert isinstance(pilot.app.screen, ModalConfirmScreen)
        await pilot.press("enter")
        assert isinstance(pilot.app.screen, SettingsScreen)
        assert len(pilot.app.column_list) == 3
        assert pilot.app.visible_column_dict == {2: "Doing", 3: "Done"}


async def test_column_delete_click(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Go to Ready Item
        await pilot.press("j")
        assert isinstance(pilot.app.focused, ColumnSelector)
        # Delete Column
        await pilot.press("d")
        assert isinstance(pilot.app.screen, ModalConfirmScreen)
        await pilot.click("#btn_continue_delete")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SettingsScreen)
        assert len(pilot.app.column_list) == 3
        assert pilot.app.visible_column_dict == {2: "Doing", 3: "Done"}


@pytest.mark.parametrize(
    "column_name, position, visible_column_dict",
    [
        ("Zero", 0, {5: "Zero", 1: "Ready", 2: "Doing", 3: "Done"}),
        ("First Position", 1, {1: "Ready", 5: "First Position", 2: "Doing", 3: "Done"}),
        ("Second Column", 2, {1: "Ready", 2: "Doing", 5: "Second Column", 3: "Done"}),
    ],
)
async def test_column_creation(
    test_app: KanbanTui, column_name, position, visible_column_dict
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        await pilot.click(
            pilot.app.screen.query(AddRule)[position].query_exactly_one(Button)
        )
        assert isinstance(pilot.app.screen, ModalUpdateColumnScreen)

        await pilot.press(*column_name)
        await pilot.click("#btn_continue_new_col")
        await pilot.pause()

        assert pilot.app.visible_column_dict == visible_column_dict


async def test_column_creation_cancel_press(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Click on First Position
        await pilot.click(pilot.app.screen.query(AddRule)[0].query_exactly_one(Button))
        assert isinstance(pilot.app.screen, ModalUpdateColumnScreen)

        # Cancel Modal View
        await pilot.press("escape")
        assert isinstance(pilot.app.screen, SettingsScreen)


async def test_column_creation_cancel_click(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Click on First Position
        await pilot.click(pilot.app.screen.query(AddRule)[0].query_exactly_one(Button))
        assert isinstance(pilot.app.screen, ModalUpdateColumnScreen)

        # Cancel Modal View
        await pilot.click("#btn_cancel_new_col")
        await pilot.pause()
        assert isinstance(pilot.app.screen, SettingsScreen)


async def test_column_creation_column_name_present(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Click on First Position
        await pilot.click(pilot.app.screen.query(AddRule)[0].query_exactly_one(Button))
        assert isinstance(pilot.app.screen, ModalUpdateColumnScreen)

        # Cancel Modal View
        await pilot.press(*"Ready")
        assert pilot.app.screen.query_exactly_one("#btn_continue_new_col").disabled


async def test_column_rename(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()
        # focus selector
        # await pilot.press("shift+tab")
        pilot.app.screen.query_exactly_one(ColumnSelector).focus()
        await pilot.pause()
        assert isinstance(pilot.app.focused, ColumnSelector)

        # Navigate to First ColumnListItem
        await pilot.press("j")
        assert pilot.app.focused.highlighted_child.column.name == "Ready"

        # Rename
        await pilot.press("r")
        assert isinstance(pilot.app.screen, ModalUpdateColumnScreen)
        assert pilot.app.focused.placeholder == "Current column name: 'Ready'"
        assert pilot.app.focused.value == ""
        assert pilot.app.screen.query_exactly_one("#btn_continue_new_col").disabled

        await pilot.press("r")
        await pilot.press("backspace")
        assert pilot.app.screen.query_exactly_one("#btn_continue_new_col").disabled

        await pilot.press(*"New Name!")
        await pilot.click("#btn_continue_new_col")
        await pilot.pause()
        assert pilot.app.focused.highlighted_child.column.name == "New Name!"
        assert pilot.app.column_list[0].name == "New Name!"

        await pilot.press("ctrl+j")
        assert pilot.app.screen.query_one("#column_1").title == "New Name!"


async def test_setting_shortcuts(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()

        assert pilot.app.screen.query_exactly_one(DataBasePathInput).has_focus_within

        await pilot.press("ctrl+e")
        assert pilot.app.screen.query_exactly_one(
            TaskAlwaysExpandedSwitch
        ).has_focus_within

        await pilot.press("ctrl+d")
        assert pilot.app.screen.query_exactly_one(DataBasePathInput).has_focus_within

        await pilot.press("ctrl+c")
        assert pilot.app.screen.query_exactly_one(ColumnSelector).has_focus_within

        await pilot.press("ctrl+n")
        assert pilot.app.screen.query_exactly_one(TaskMovementSelector).has_focus_within

        await pilot.press("ctrl+g")
        assert pilot.app.screen.query_exactly_one(
            TaskDefaultColorSelector
        ).has_focus_within

        await pilot.press("ctrl+s")
        assert pilot.app.screen.query_exactly_one(StatusColumnSelector).has_focus_within


async def test_status_column_selector(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")
        await pilot.pause()

        assert pilot.app.screen.query_exactly_one(DataBasePathInput).has_focus_within

        await pilot.press("ctrl+s")
        assert pilot.app.screen.query_exactly_one(StatusColumnSelector).has_focus_within

        assert str(pilot.app.focused.value) == "Select.BLANK"

        await pilot.click(pilot.app.focused)
        await pilot.press(*"jj")
        await pilot.press("enter")

        assert pilot.app.focused.value == 1
        assert pilot.app.active_board.reset_column == 1

        await pilot.click(pilot.app.screen.query_one("#select_start"))
        await pilot.press(*"jj")
        await pilot.press("enter")
        assert pilot.app.active_board.reset_column is None
        assert pilot.app.active_board.start_column == 1


async def test_status_update_task_in_start_column(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("ctrl+l")

        await pilot.press("ctrl+s")
        assert pilot.app.screen.query_exactly_one(StatusColumnSelector).has_focus_within
        # Go to Start Select
        await pilot.press("j")
        assert str(pilot.app.focused.value) == "Select.BLANK"

        # Select Ready
        await pilot.press("enter")
        await pilot.press("j")
        await pilot.press("enter")

        assert pilot.app.focused.value == 1
        assert pilot.app.active_board.start_column == 1

        # go to finish select
        await pilot.press("j")
        await pilot.press("enter")
        await pilot.press(*"jj")
        await pilot.press("enter")
        assert pilot.app.active_board.finish_column == 2

        await pilot.press("ctrl+j")
        await pilot.press("L")
        assert (
            pilot.app.focused.task_.creation_date == pilot.app.focused.task_.start_date
        )
