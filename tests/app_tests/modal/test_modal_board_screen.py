import pytest
from kanban_tui.app import KanbanTui
from textual.widgets import Input, Button, Static, Label
from kanban_tui.views.main_view import MainView
from kanban_tui.modal.modal_task_screen import ModalConfirmScreen
from kanban_tui.modal.modal_board_screen import (
    ModalBoardOverviewScreen,
    ModalNewBoardScreen,
)

from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.database import create_new_board_db
from rich.emoji import Emoji

APP_SIZE = (120, 80)


async def test_modal_board_creation_default(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open Board View

        await pilot.press("B")
        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)

        # Open Board Creation Screen
        await pilot.press("n")
        assert isinstance(pilot.app.screen, ModalNewBoardScreen)
        assert pilot.app.focused.id == "input_board_icon"
        assert pilot.app.screen.query_one("#input_board_name", Input).value == ""
        assert pilot.app.screen.query_one("#btn_continue_new_board", Button).disabled

        # Enter new Icon
        await pilot.press(*"bug")
        assert pilot.app.screen.query_one("#input_board_icon").value == "bug"

        # Enter new board name
        await pilot.click("#input_board_name")
        await pilot.press(*"Test Board")

        assert pilot.app.screen.query_one("#input_board_name").value == "Test Board"
        assert not pilot.app.screen.query_one(
            "#btn_continue_new_board", Button
        ).disabled

        # save board
        await pilot.click("#btn_continue_new_board")
        # leave board screen, still stay on old board
        await pilot.press("escape")
        assert isinstance(pilot.app.screen, MainView)

        # new Board no tasks
        assert len(list(pilot.app.screen.query(TaskCard).results())) == 5
        assert len(pilot.app.board_list) == 2


# @pytest.mark.skip(reason="Soon to be implemented")
async def test_modal_board_creation_custom(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open Board View

        await pilot.press("B")
        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)

        # Open Board Creation Screen
        await pilot.press("n")
        assert isinstance(pilot.app.screen, ModalNewBoardScreen)
        assert pilot.app.focused.id == "input_board_icon"
        assert pilot.app.screen.query_one("#input_board_name", Input).value == ""
        assert pilot.app.screen.query_one("#btn_continue_new_board", Button).disabled

        # Enter new Icon
        await pilot.press(*"bug")
        assert pilot.app.screen.query_one("#input_board_icon").value == "bug"

        # Enter new board name
        await pilot.click("#input_board_name")
        await pilot.press(*"Test Board")

        assert pilot.app.screen.query_one("#input_board_name").value == "Test Board"
        assert not pilot.app.screen.query_one(
            "#btn_continue_new_board", Button
        ).disabled

        # Add Custom Columns
        # CustomList visible after switch press
        assert pilot.app.screen.query_one("#new_column_list").has_class("hidden")
        await pilot.click("#switch_use_default_columns")
        assert not pilot.app.screen.query_one("#new_column_list").has_class("hidden")

        # Focus vscroll
        await pilot.press("tab")
        # Focus input
        await pilot.press("tab")
        await pilot.press(*"test_column")
        assert len(pilot.app.screen.query_one("#new_column_list").children) == 2
        # next column input
        await pilot.press("tab", "tab")
        await pilot.press(*"test_column2")
        assert len(pilot.app.screen.query_one("#new_column_list").children) == 3
        await pilot.press("shift+tab", "shift+tab", "delete")
        assert pilot.app.focused.value == ""
        assert len(pilot.app.screen.query_one("#new_column_list").children) == 2

        # save board
        await pilot.click("#btn_continue_new_board")
        # Click to activate new Board
        await pilot.press("j", "enter")
        assert isinstance(pilot.app.screen, MainView)

        # new Board no tasks
        assert len(pilot.app.column_list) == 1
        assert pilot.app.column_list[0].name == "test_column2"
        assert len(pilot.app.board_list) == 2


@pytest.mark.parametrize(
    "input_icon, expected_preview_result",
    [
        ("Vampire ", "vampire"),
        ("books ", "books"),
        (" ", "No Icon"),
    ],
)
async def test_modal_board_icon_check(
    test_app: KanbanTui, input_icon, expected_preview_result
):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open modal to list boards
        await pilot.press("B")
        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)

        # Open Board Creation Screen
        await pilot.press("n")
        assert isinstance(pilot.app.screen, ModalNewBoardScreen)
        assert pilot.app.focused.id == "input_board_icon"

        await pilot.press(*input_icon)
        await pilot.press("backspace")
        assert (
            pilot.app.screen.query_one("#input_board_icon", Input).value
            == input_icon.strip()
        )
        if input_icon in ["Vampire ", "books "]:
            assert (
                pilot.app.screen.query_one(
                    "#static_preview_icon", Static
                ).visual.markup  # ._text[0]
                == Emoji(expected_preview_result)._char
            )
        else:
            assert (
                pilot.app.screen.query_one("#static_preview_icon", Static).visual._text
                == expected_preview_result
            )


async def test_modal_board_creation_list_check(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        create_new_board_db(
            name="Test Board 1", icon="Vampire", database=pilot.app.cfg.database_path
        )
        create_new_board_db(
            name="Test Board 2", icon="Vampire", database=pilot.app.cfg.database_path
        )

        pilot.app.update_board_list()

        await pilot.press("B")
        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)
        assert len(pilot.app.board_list) == 3


async def test_modal_board_edit(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        await pilot.press("B")

        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)
        assert pilot.app.focused.id == "board_list"
        assert pilot.app.focused.highlighted_child.board.board_id == 1
        assert len(pilot.app.board_list) == 1

        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalNewBoardScreen)

        assert pilot.app.screen.kanban_board.name == "Test_Board"
        assert pilot.app.screen.kanban_board.icon == ":bug:"

        assert (
            pilot.app.screen.query_exactly_one(
                "#btn_continue_new_board", Button
            ).label._text
            == "Edit Board"
        )
        assert (
            pilot.app.screen.query_exactly_one("#label_header", Label)._content
            == "Edit Board"
        )

        assert (
            pilot.app.screen.query_one("#input_board_name", Input).value == "Test_Board"
        )
        assert pilot.app.screen.query_one("#input_board_icon", Input).value == "bug"
        assert not pilot.app.screen.query_one(
            "#btn_continue_new_board", Button
        ).disabled

        await pilot.click("#btn_continue_new_board")
        assert len(pilot.app.board_list) == 1


async def test_modal_board_edit_cancel(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        await pilot.press("B")

        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalNewBoardScreen)

        await pilot.click("#btn_cancel_new_board")
        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)


async def test_modal_board_delete_board(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        create_new_board_db(
            name="Test Board 1", icon="Vampire", database=pilot.app.cfg.database_path
        )
        create_new_board_db(
            name="Test Board 2", icon="Vampire", database=pilot.app.cfg.database_path
        )

        pilot.app.update_board_list()

        await pilot.press("B")
        # Delete Board number 2
        await pilot.press(*"jd")
        assert isinstance(pilot.app.screen, ModalConfirmScreen)
        await pilot.click("#btn_continue_delete")
        assert isinstance(pilot.app.screen, ModalBoardOverviewScreen)
        assert len(pilot.app.board_list) == 2


async def test_modal_board_activate_board(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        create_new_board_db(
            name="Test Board 1", icon="Vampire", database=pilot.app.cfg.database_path
        )
        create_new_board_db(
            name="Test Board 2", icon="Vampire", database=pilot.app.cfg.database_path
        )

        pilot.app.update_board_list()

        await pilot.press("B")
        # activate Board number 3
        await pilot.press(*"jj")
        await pilot.press("enter")
        assert isinstance(pilot.app.screen, MainView)
        assert pilot.app.active_board.name == "Test Board 2"


async def test_modal_board_copy_board(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # open modal to show Boards
        await pilot.press("B")

        # copy board
        await pilot.press("c")

        await pilot.press("j")
        assert pilot.app.focused.highlighted_child.board.board_id == 2
        assert pilot.app.focused.highlighted_child.board.name == "Test_Board_copy"
        assert pilot.app.focused.highlighted_child.board.icon == ":bug:"
        await pilot.press("enter")
        assert isinstance(pilot.app.screen, MainView)
        assert pilot.app.active_board.name == "Test_Board_copy"
        assert len(pilot.app.board_list) == 2
