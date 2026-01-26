from datetime import datetime

from kanban_tui.app import KanbanTui
from textual.widgets import Input, TextArea
from kanban_tui.modal.modal_category_screen import ModalCategoryManageScreen
from kanban_tui.screens.board_screen import BoardScreen
from kanban_tui.modal.modal_confirm_screen import ModalConfirmScreen
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen

from kanban_tui.widgets.modal_task_widgets import CategorySelector
from kanban_tui.widgets.task_card import TaskCard

APP_SIZE = (150, 50)


async def test_task_creation(no_task_app: KanbanTui):
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        # open modal to create Task
        await pilot.press("n")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)

        # check title has focus
        assert pilot.app.focused.id == "input_title"
        assert pilot.app.screen.query_one("#input_title", Input).value == ""
        # Enter new task name
        await pilot.press(*"Test Task")
        assert pilot.app.screen.query_one("#input_title").value == "Test Task"

        # Enter new task description
        await pilot.press("tab")
        assert isinstance(pilot.app.focused, TextArea)
        await pilot.press(*"Test Description")
        assert pilot.app.screen.query_one(TextArea).text == "Test Description"

        # Choose new task Category
        await pilot.press("tab")
        assert isinstance(pilot.app.focused, CategorySelector)

        # open selector dropdown
        await pilot.press("enter")
        # go down and select new category
        await pilot.press("j")
        await pilot.press("enter")
        # focus button and press
        await pilot.press("tab")
        await pilot.press("enter")
        # new category open popup screen
        assert isinstance(pilot.app.focused, Input)
        await pilot.press(*"Test Category")
        await pilot.press("tab")
        # choose color
        await pilot.press(*"yellow")
        await pilot.click("#btn_continue_new_category")

        # check value
        await pilot.press("shift+tab")
        assert pilot.app.focused.highlighted_child.category.name == "Test Category"
        # selecting new category and exiting screen
        await pilot.press("enter")

        # save task
        await pilot.click("#btn_continue")
        assert isinstance(pilot.app.screen, BoardScreen)
        assert len(pilot.app.task_list) == 1
        await pilot.pause(delay=0.5)
        assert pilot.app.focused.id == "taskcard_1"
        assert pilot.app.focused.styles.background.hex == "#FFFF00"


async def test_task_edit_button(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done

        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)
        assert pilot.app.screen.kanban_task is not None

        # Check Task Stats
        assert (
            pilot.app.screen.query_exactly_one("#input_title", Input).value
            == "Task_ready_0"
        )
        assert pilot.app.screen.query_exactly_one(TextArea).text == "Hallo"
        assert pilot.app.screen.query_exactly_one(CategorySelector).selection == 1

        # add 1 to title
        # focus the input first to select the text
        pilot.app.screen.query_one("#input_title", Input).select_all()
        await pilot.press(*"Task_ready_01")
        await pilot.click("#btn_continue")

        assert pilot.app.focused.id == "taskcard_1"
        assert pilot.app.focused.task_.title == "Task_ready_01"


async def test_task_edit_shortcut(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done

        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)
        assert pilot.app.screen.kanban_task is not None

        # Check Task Stats
        assert (
            pilot.app.screen.query_exactly_one("#input_title", Input).value
            == "Task_ready_0"
        )
        assert pilot.app.screen.query_exactly_one(TextArea).text == "Hallo"
        assert pilot.app.screen.query_exactly_one(CategorySelector).selection == 1

        # add 1 to title
        # Focus Input first
        pilot.app.screen.query_one("#input_title", Input).select_all()
        await pilot.press(*"Task_ready_01")
        await pilot.press("ctrl+j")

        assert pilot.app.focused.id == "taskcard_1"
        assert pilot.app.focused.task_.title == "Task_ready_01"


async def test_task_edit_cancel(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)
        # Cancel with escape
        await pilot.press("escape")
        assert isinstance(pilot.app.screen, BoardScreen)
        assert pilot.app.focused.id == "taskcard_1"


async def test_task_delete(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("d")
        assert isinstance(pilot.app.screen, ModalConfirmScreen)
        # Cancel with escape
        await pilot.click("#btn_continue")
        assert isinstance(pilot.app.screen, BoardScreen)
        assert pilot.app.focused.id == "taskcard_5"


async def test_task_due_date(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)
        # Cancel with escape
        await pilot.click("#switch_due_date")
        assert pilot.app.screen.query_one("#switch_due_date").value
        await pilot.click("#dateselect_due_date")


async def test_task_due_date_picker(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)

        # click due date switch
        await pilot.click("#switch_due_date")
        assert pilot.app.screen.query_one("#switch_due_date").value
        await pilot.click("#dateselect_due_date")
        await pilot.press("enter")
        assert (
            pilot.app.screen.query_one("#dateselect_due_date").value.date()
            == datetime.today().date()
        )


async def test_task_category_selector(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("e")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)

        # check if category is correct in select
        category_id = pilot.app.screen.kanban_task.category
        assert pilot.app.screen.query_one(CategorySelector).value == category_id


async def test_task_category_deletion(test_app: KanbanTui):
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # 1st card is focused
        # 3 in ready, 1 in doing, 1 in done
        assert isinstance(pilot.app.focused, TaskCard)

        # open edit window
        await pilot.press("e")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)

        await pilot.press("tab")
        await pilot.press("tab")
        await pilot.pause()
        assert isinstance(pilot.app.focused, CategorySelector)

        # open selector dropdown
        await pilot.press("enter")
        await pilot.pause()
        # go up from current category and select add/edit category
        await pilot.press("k")
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ModalCategoryManageScreen)
        # delete category of current task and go back to task screen
        await pilot.press("d")
        await pilot.pause()
        # confirm deletion
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        # go back to board screen
        await pilot.press("escape")
        await pilot.pause()
        # check if category is None
        assert pilot.app.focused.task_.category is None

        # assert pilot.app.screen.query_one(CategorySelector).value == category_id
