import sys

import pytest

from kanban_tui.app import KanbanTui
from textual.widgets import Input, Button, Label
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
        assert len(no_task_app.task_list) == 0
        assert isinstance(no_task_app.screen, BoardScreen)

        assert isinstance(no_task_app.focused, KanbanBoard)


async def test_kanbanboard_task_creation(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        await pilot.press("n")
        assert isinstance(no_task_app.screen, ModalTaskEditScreen)
        assert no_task_app.focused.id == "input_title"
        assert no_task_app.screen.query_one("#input_title", Input).value == ""

        # Enter new task name
        await pilot.press(*"Test Task")
        assert no_task_app.screen.query_one("#input_title").value == "Test Task"

        # save task
        await pilot.click("#btn_continue")
        assert isinstance(no_task_app.screen, BoardScreen)

        assert len(list(no_task_app.screen.query(TaskCard).results())) == 1


async def test_task_metadata_visible_by_default(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert test_app.config.task.metadata_always_expanded
        metadata = pilot.app.focused.query_one(".label-metadata", Label)
        assert metadata.display
        assert "no due" in metadata.content.plain
        assert "no dependencies" in metadata.content.plain


async def test_task_metadata_hidden_until_focus_when_disabled(test_app: KanbanTui):
    test_app.config.task.metadata_always_expanded = False
    async with test_app.run_test(size=APP_SIZE) as pilot:
        task_cards = list(pilot.app.screen.query(TaskCard).results())
        first_card = task_cards[0]
        second_card = task_cards[1]

        first_metadata = first_card.query_one(".label-metadata", Label)
        second_metadata = second_card.query_one(".label-metadata", Label)

        assert first_metadata.display
        assert not second_metadata.display

        await pilot.press("j")

        assert not first_metadata.display
        assert second_metadata.display
        assert "no due" in second_metadata.content.plain
        assert "no dependencies" in second_metadata.content.plain


async def test_kanbanboard_board_view(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        # open modal to show Boards
        await pilot.press("B")
        assert isinstance(no_task_app.screen, ModalBoardOverviewScreen)

        # Open Board Creation Screen
        await pilot.press("n")
        assert isinstance(no_task_app.screen, ModalNewBoardScreen)
        assert no_task_app.focused.id == "input_board_icon"
        assert no_task_app.screen.query_one("#input_board_name", Input).value == ""
        assert no_task_app.screen.query_one("#btn_continue_new_board", Button).disabled

        # Enter new board name
        await pilot.click("#input_board_name")
        await pilot.press(*"Test Board")

        assert no_task_app.screen.query_one("#input_board_name").value == "Test Board"
        assert not no_task_app.screen.query_one(
            "#btn_continue_new_board", Button
        ).disabled

        # save board
        await pilot.click("#btn_continue_new_board")
        await pilot.press("escape")
        assert isinstance(no_task_app.screen, BoardScreen)

        # new Board no tasks
        assert len(list(no_task_app.screen.query(TaskCard).results())) == 0
        assert len(list(no_task_app.board_list)) == 2


# https://github.com/Zaloog/kanban-tui/issues/1
async def test_kanbanboard_movement_no_task_app(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        # check if board has focus
        assert isinstance(no_task_app.focused, KanbanBoard)

        # if no card is present, should just return and dont do any movevemt
        await pilot.press("h")

        assert isinstance(no_task_app.focused, KanbanBoard)


async def test_kanbanboard_movement(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(test_app.focused, TaskCard)
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        # up 0 -> 2
        await pilot.press("k")
        assert test_app.focused.task_.title == "Task_ready_2"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 2

        # up 2- > 1
        await pilot.press("k")
        assert test_app.focused.task_.title == "Task_ready_1"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 1

        # 2x down 1 -> 0
        await pilot.press("j", "j")
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        # right ready -> doing
        await pilot.press("j")
        await pilot.press("l")
        assert test_app.focused.task_.title == "Task_doing_0"
        assert test_app.focused.task_.column == 2
        assert test_app.focused.row == 0

        # 2x right doing -> ready
        await pilot.press("l", "l")
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        # left ready -> done
        await pilot.press("k")
        await pilot.press("h")
        assert test_app.focused.task_.title == "Task_done_0"
        assert test_app.focused.task_.column == 3
        assert test_app.focused.row == 0

        # 2x left done -> ready
        await pilot.press("h", "h")
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        # delete Done Task
        await pilot.press("l")
        await pilot.press("d")
        await pilot.click("#btn_continue")
        assert test_app.focused.task_.title == "Task_ready_2"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 2

        # move right skip done column
        await pilot.press("l")
        assert test_app.focused.task_.title == "Task_done_0"
        assert test_app.focused.task_.column == 3
        assert test_app.focused.row == 0

        # move left skip done column
        await pilot.press("h")
        assert test_app.focused.task_.title == "Task_ready_2"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 2


async def test_kanbanboard_card_movement_adjacent(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(test_app.focused, TaskCard)
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        # try move card left
        # ready -> ready
        await pilot.press("H")
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        await pilot.press("L")
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 2
        assert test_app.focused.row == 0

        await pilot.press("h")
        assert test_app.focused.task_.title == "Task_ready_1"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        await pilot.press("L")
        assert test_app.focused.task_.title == "Task_ready_1"
        assert test_app.focused.task_.column == 2
        assert test_app.focused.row == 0


async def test_kanbanboard_card_movement_jump(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(test_app.focused, TaskCard)
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0

        # change movement mode
        pilot.app.config.task.movement_mode = MovementModes.JUMP
        # try move card right twice
        # ready -> done
        await pilot.press("L")
        assert test_app.screen.query_one(KanbanBoard).target_column == 2

        await pilot.press("L")
        assert test_app.screen.query_one(KanbanBoard).target_column == 3
        await pilot.press("enter")
        assert test_app.screen.query_one(KanbanBoard).target_column is None

        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 3
        assert test_app.focused.row == 0


async def test_kanbanboard_card_movement_mouse_same_column(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(test_app.focused, TaskCard)
        await pilot.mouse_down(pilot.app.focused)
        assert test_app.screen.query_one(KanbanBoard).mouse_down
        await pilot.mouse_up(pilot.app.screen.query_one(Column))
        assert not test_app.screen.query_one(KanbanBoard).mouse_down
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 1
        assert test_app.focused.row == 0


@pytest.mark.skipif(
    sys.platform == "win32", reason="Issues when runnning on windows CI runner"
)
async def test_kanbanboard_card_movement_mouse_different_column(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(test_app.focused, TaskCard)
        await pilot.mouse_down(pilot.app.focused)
        assert test_app.screen.query_one(KanbanBoard).mouse_down
        await pilot.mouse_up(pilot.app.screen.query(Column).last())
        assert not test_app.screen.query_one(KanbanBoard).mouse_down
        assert test_app.focused.task_.title == "Task_ready_0"
        assert test_app.focused.task_.column == 3


async def test_kanbanboard_drag_cross_column_inserts_at_target_position(
    test_app: KanbanTui,
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        board = pilot.app.screen.query_one(KanbanBoard)
        assert isinstance(test_app.focused, TaskCard)
        assert test_app.focused.task_.title == "Task_ready_0"

        board.selected_task = pilot.app.focused.task_
        board.mouse_down = True
        board.target_column = 3
        board.drag_target_position = 0

        await board.action_confirm_move()
        board.mouse_down = False
        board._clear_drag_target()

        done_tasks = list(
            pilot.app.screen.query_one("#column_3", Column).query(TaskCard)
        )
        assert [task_card.task_.title for task_card in done_tasks] == [
            "Task_ready_0",
            "Task_done_0",
        ]


async def test_refresh_columns_preserves_unchanged_column_widgets(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        board = pilot.app.screen.query_one(KanbanBoard)
        ready_column_before = pilot.app.screen.query_one("#column_1", Column)
        doing_column_before = pilot.app.screen.query_one("#column_2", Column)

        ready_cards_before = list(ready_column_before.query(TaskCard).results())
        doing_cards_before = list(doing_column_before.query(TaskCard).results())

        pilot.app.backend.delete_task(task_id=5)
        pilot.app.update_task_list()
        await board.refresh_columns()

        ready_column_after = pilot.app.screen.query_one("#column_1", Column)
        doing_column_after = pilot.app.screen.query_one("#column_2", Column)
        done_column_after = pilot.app.screen.query_one("#column_3", Column)

        assert ready_column_after is ready_column_before
        assert doing_column_after is doing_column_before
        assert list(ready_column_after.query(TaskCard).results()) == ready_cards_before
        assert list(doing_column_after.query(TaskCard).results()) == doing_cards_before
        assert done_column_after.task_amount == 0


async def test_replace_tasks_bulk_mount_preserves_order(no_task_app: KanbanTui):
    no_task_app.backend.create_new_category(name="red", color="#FF0000")
    no_task_app.backend.create_new_category(name="green", color="#00FF00")

    for idx in range(250):
        no_task_app.backend.create_new_task(
            title=f"Task_done_{idx}",
            description="Hallo",
            category=1 if idx % 2 == 0 else 2,
            column=3,
        )

    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        done_column = pilot.app.screen.query_one("#column_3", Column)
        done_tasks = [task for task in pilot.app.task_list if task.column == 3]
        reordered_tasks = list(reversed(done_tasks))

        await done_column.replace_tasks(reordered_tasks)

        rendered_cards = list(done_column.query(TaskCard).results())

        assert done_column.task_amount == 250
        assert len(rendered_cards) == 250
        assert rendered_cards[0].task_.title == "Task_done_249"
        assert rendered_cards[-1].task_.title == "Task_done_0"
        assert rendered_cards[0].row == 0
        assert rendered_cards[-1].row == 249
        assert rendered_cards[0].task_.position == 0
        assert rendered_cards[-1].task_.position == 249


async def test_sync_tasks_removes_deleted_card_without_rebuilding_column(
    no_task_app: KanbanTui,
):
    no_task_app.backend.create_new_category(name="red", color="#FF0000")
    for idx in range(6):
        no_task_app.backend.create_new_task(
            title=f"Task_done_{idx}",
            description="Hallo",
            category=1,
            column=3,
        )

    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        done_column = pilot.app.screen.query_one("#column_3", Column)
        original_cards = list(done_column.query(TaskCard).results())
        surviving_card = original_cards[4]
        updated_tasks = [
            task
            for task in pilot.app.task_list
            if task.column == 3 and task.task_id != original_cards[2].task_.task_id
        ]

        await done_column.sync_tasks(updated_tasks)

        rendered_cards = list(done_column.query(TaskCard).results())

        assert len(rendered_cards) == 5
        assert surviving_card in rendered_cards
        assert surviving_card.row == 3
        assert rendered_cards[3] is surviving_card


async def test_sync_tasks_appends_new_cards_without_rebuilding_existing_prefix(
    no_task_app: KanbanTui,
):
    for idx in range(6):
        no_task_app.backend.create_new_task(
            title=f"Task_done_{idx}",
            description="Hallo",
            column=3,
        )

    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        done_column = pilot.app.screen.query_one("#column_3", Column)
        original_cards = list(done_column.query(TaskCard).results())

        for idx in range(6, 8):
            pilot.app.backend.create_new_task(
                title=f"Task_done_{idx}",
                description="Hallo",
                column=3,
            )

        pilot.app.update_task_list()
        updated_tasks = [task for task in pilot.app.task_list if task.column == 3]

        await done_column.sync_tasks(updated_tasks)

        rendered_cards = list(done_column.query(TaskCard).results())

        assert len(rendered_cards) == 8
        assert rendered_cards[:6] == original_cards
        assert rendered_cards[6].task_.title == "Task_done_6"
        assert rendered_cards[7].task_.title == "Task_done_7"
        assert rendered_cards[6].row == 6
        assert rendered_cards[7].row == 7


async def test_sync_tasks_updates_same_ids_in_place(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        done_column = pilot.app.screen.query_one("#column_3", Column)
        original_card = done_column.query_one(TaskCard)
        original_task_id = original_card.task_.task_id

        pilot.app.backend.update_task_entry(
            task_id=original_task_id,
            title="Task_done_updated",
            description="Updated description",
            category=1,
            due_date=None,
        )

        pilot.app.update_task_list()
        updated_tasks = [task for task in pilot.app.task_list if task.column == 3]

        await done_column.sync_tasks(updated_tasks)
        await pilot.pause()

        refreshed_card = done_column.query_one(TaskCard)

        assert refreshed_card is original_card
        assert refreshed_card.task_.task_id == original_task_id
        assert refreshed_card.task_.title == "Task_done_updated"
        assert refreshed_card.query_one(".label-title", Label).content == (
            "Task_done_updated"
        )


async def test_refresh_keeps_focus_on_same_task(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("j")
        assert isinstance(test_app.focused, TaskCard)
        focused_before = pilot.app.focused.task_.task_id

        await pilot.press("r")

        assert isinstance(test_app.focused, TaskCard)
        assert test_app.focused.task_.task_id == focused_before


async def test_custom_footer(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert not test_app.screen.query_one(VimSelect).display

        await pilot.press("C")
        assert test_app.screen.query_one(VimSelect).display


async def test_custom_footer_backend_switcher(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert not test_app.screen.query_one(VimSelect).display
        assert test_app.screen.query_one(VimSelect).value == f"✔  {Backends.SQLITE}"
