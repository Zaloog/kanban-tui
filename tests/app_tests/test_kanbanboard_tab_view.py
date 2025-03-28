import pytest
from kanban_tui.app import KanbanTui
from textual.widgets import Input, Button
from kanban_tui.views.main_view import MainView
from kanban_tui.views.kanbanboard_tab_view import KanbanBoard
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
from kanban_tui.modal.modal_board_screen import (
    ModalBoardOverviewScreen,
    ModalNewBoardScreen,
)

from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.widgets.filter_sidebar import FilterOverlay

APP_SIZE = (120, 80)


async def test_empty_kanbanboard(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 0
        assert isinstance(pilot.app.screen, MainView)

        assert isinstance(pilot.app.focused, KanbanBoard)


async def test_kanbanboard_task_creation(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        await pilot.press("n")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)
        assert pilot.app.focused.id == "input_title"
        assert pilot.app.screen.query_one("#input_title", Input).value == ""

        # Enter new task name
        await pilot.press(*"Test Task")
        assert pilot.app.screen.query_one("#input_title").value == "Test Task"

        # save task
        await pilot.click("#btn_continue")
        assert isinstance(pilot.app.screen, MainView)

        assert len(list(pilot.app.screen.query(TaskCard).results())) == 1


async def test_kanbanboard_board_view(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        # open modal to show Boards
        await pilot.press("B")
        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)

        # Open Board Creation Screen
        await pilot.press("n")
        assert isinstance(pilot.app.screen, ModalNewBoardScreen)
        assert pilot.app.focused.id == "input_board_icon"
        assert pilot.app.screen.query_one("#input_board_name", Input).value == ""
        assert pilot.app.screen.query_one("#btn_continue_new_board", Button).disabled

        # Enter new board name
        await pilot.click("#input_board_name")
        await pilot.press(*"Test Board")

        assert pilot.app.screen.query_one("#input_board_name").value == "Test Board"
        assert not pilot.app.screen.query_one(
            "#btn_continue_new_board", Button
        ).disabled

        # save board
        await pilot.click("#btn_continue_new_board")
        await pilot.press("escape")
        assert isinstance(pilot.app.screen, MainView)

        # new Board no tasks
        assert len(list(pilot.app.screen.query(TaskCard).results())) == 0
        assert len(list(pilot.app.board_list)) == 2


# https://github.com/Zaloog/kanban-tui/issues/1
async def test_kanbanboard_movement_empty_app(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        # check if board has focus
        assert isinstance(pilot.app.focused, KanbanBoard)

        # if no card is present, should just return and dont do any movevemt
        await pilot.press("h")

        assert isinstance(pilot.app.focused, KanbanBoard)


async def test_kanbanboard_movement(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0

        # up 0 -> 2
        await pilot.press("k")
        assert pilot.app.focused.task_.title == "Task_ready_2"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 2

        # up 2- > 1
        await pilot.press("k")
        assert pilot.app.focused.task_.title == "Task_ready_1"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 1

        # 2x down 1 -> 0
        await pilot.press("j", "j")
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0

        # right ready -> doing
        await pilot.press("j")
        await pilot.press("l")
        assert pilot.app.focused.task_.title == "Task_doing_0"
        assert pilot.app.focused.task_.column == 2
        assert pilot.app.focused.row == 0

        # 2x right doing -> ready
        await pilot.press("l", "l")
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0

        # left ready -> done
        await pilot.press("k")
        await pilot.press("h")
        assert pilot.app.focused.task_.title == "Task_done_0"
        assert pilot.app.focused.task_.column == 3
        assert pilot.app.focused.row == 0

        # 2x left done -> ready
        await pilot.press("h", "h")
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0

        # delete Done Task
        await pilot.press("l")
        await pilot.press("d")
        await pilot.click("#btn_continue_delete")
        assert pilot.app.focused.task_.title == "Task_ready_2"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 2

        # move right skip done column
        await pilot.press("l")
        assert pilot.app.focused.task_.title == "Task_done_0"
        assert pilot.app.focused.task_.column == 3
        assert pilot.app.focused.row == 0

        # move left skip done column
        await pilot.press("h")
        assert pilot.app.focused.task_.title == "Task_ready_2"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 2


async def test_kanbanboard_card_movement(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0

        # try move card left
        # ready -> ready
        await pilot.press("H")
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0

        await pilot.press("L")
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 2
        assert pilot.app.focused.row == 1

        await pilot.press("h")
        assert pilot.app.focused.task_.title == "Task_ready_2"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 1

        await pilot.press("L")
        assert pilot.app.focused.task_.title == "Task_ready_2"
        assert pilot.app.focused.task_.column == 2
        assert pilot.app.focused.row == 2


@pytest.mark.skip(reason="Filter not implemented yet")
async def test_filter_empty_app(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, KanbanBoard)

        assert "-hidden" in pilot.app.screen.query_one(FilterOverlay).classes
        assert abs(pilot.app.screen.query_one(FilterOverlay).offset[0]) > 0

        # Open Filter
        await pilot.press("f1")
        await pilot.wait_for_animation()
        assert pilot.app.screen.query_one(FilterOverlay).offset[0] == 0
        assert pilot.app.focused.id == "category_filter"
        assert all(task.disabled for task in pilot.app.screen.query(TaskCard))

        # Close Filter
        await pilot.press("f1")
        await pilot.wait_for_animation()
        assert abs(pilot.app.screen.query_one(FilterOverlay).offset[0]) > 0
        assert isinstance(pilot.app.focused, KanbanBoard)


@pytest.mark.skip(reason="Filter not implemented yet")
async def test_filter(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)

        assert "-hidden" in pilot.app.screen.query_one(FilterOverlay).classes
        assert abs(pilot.app.screen.query_one(FilterOverlay).offset[0]) > 0

        # Open Filter
        await pilot.press("f1")
        await pilot.wait_for_animation()
        assert pilot.app.screen.query_one(FilterOverlay).offset[0] == 0
        assert pilot.app.focused.id == "category_filter"
        assert all(task.disabled for task in pilot.app.screen.query(TaskCard))

        # Close Filter
        await pilot.press("f1")
        await pilot.wait_for_animation()
        assert abs(pilot.app.screen.query_one(FilterOverlay).offset[0]) > 0
        assert isinstance(pilot.app.focused, TaskCard)
