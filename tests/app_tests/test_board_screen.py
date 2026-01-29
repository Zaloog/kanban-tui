import sys

import pytest

from kanban_tui.app import KanbanTui
from textual.widgets import Input, Button
from kanban_tui.config import Backends, MovementModes
from kanban_tui.screens.board_screen import BoardScreen
from kanban_tui.widgets.board_widgets import KanbanBoard
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
from kanban_tui.modal.modal_board_screen import (
    ModalBoardOverviewScreen,
    ModalNewBoardScreen,
)

from kanban_tui.widgets.modal_task_widgets import VimSelect
from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.widgets.task_column import Column

APP_SIZE = (150, 50)


async def test_no_task_kanbanboard(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        assert len(pilot.app.task_list) == 0
        assert isinstance(pilot.app.screen, BoardScreen)

        assert isinstance(pilot.app.focused, KanbanBoard)


async def test_kanbanboard_task_creation(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
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
        assert isinstance(pilot.app.screen, BoardScreen)

        assert len(list(pilot.app.screen.query(TaskCard).results())) == 1


async def test_kanbanboard_board_view(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
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
        assert isinstance(pilot.app.screen, BoardScreen)

        # new Board no tasks
        assert len(list(pilot.app.screen.query(TaskCard).results())) == 0
        assert len(list(pilot.app.board_list)) == 2


# https://github.com/Zaloog/kanban-tui/issues/1
async def test_kanbanboard_movement_no_task_app(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
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
        await pilot.click("#btn_continue")
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


async def test_kanbanboard_card_movement_adjacent(test_app: KanbanTui):
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


async def test_kanbanboard_card_movement_jump(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0

        # change movement mode
        pilot.app.config.task.movement_mode = MovementModes.JUMP
        # try move card right twice
        # ready -> done
        await pilot.press("L")
        assert pilot.app.screen.query_one(KanbanBoard).target_column == 2

        await pilot.press("L")
        assert pilot.app.screen.query_one(KanbanBoard).target_column == 3
        await pilot.press("enter")
        assert pilot.app.screen.query_one(KanbanBoard).target_column is None

        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 3
        assert pilot.app.focused.row == 1


async def test_kanbanboard_card_movement_mouse_same_column(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)
        await pilot.mouse_down(pilot.app.focused)
        assert pilot.app.screen.query_one(KanbanBoard).mouse_down
        await pilot.mouse_up(pilot.app.screen.query_one(Column))
        assert not pilot.app.screen.query_one(KanbanBoard).mouse_down
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 1
        assert pilot.app.focused.row == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Issues when runnning on windows CI runner"
)
async def test_kanbanboard_card_movement_mouse_different_column(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)
        await pilot.mouse_down(pilot.app.focused)
        assert pilot.app.screen.query_one(KanbanBoard).mouse_down
        await pilot.mouse_up(pilot.app.screen.query(Column).last())
        assert not pilot.app.screen.query_one(KanbanBoard).mouse_down
        assert pilot.app.focused.task_.title == "Task_ready_0"
        assert pilot.app.focused.task_.column == 3
        assert pilot.app.focused.row == 1


async def test_custom_footer(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert not pilot.app.screen.query_one(VimSelect).display

        await pilot.press("C")
        assert pilot.app.screen.query_one(VimSelect).display


async def test_custom_footer_backend_switcher(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert not pilot.app.screen.query_one(VimSelect).display
        assert pilot.app.screen.query_one(VimSelect).value == f"✔  {Backends.SQLITE}"
