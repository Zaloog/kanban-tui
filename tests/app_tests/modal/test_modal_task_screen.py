from kanban_tui.app import KanbanTui
from textual.widgets import Input, TextArea
from kanban_tui.views.main_view import MainView
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen, ModalConfirmScreen

from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.widgets.modal_task_widgets import CategorySelector
from kanban_tui.modal.modal_color_pick import TitleInput

APP_SIZE = (120, 80)


async def test_task_creation(empty_app: KanbanTui):
    async with empty_app.run_test(size=APP_SIZE) as pilot:
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
        # new category open popup screen
        assert isinstance(pilot.app.focused, TitleInput)
        await pilot.press(*"Test Category")
        await pilot.press("tab")
        # choose color
        await pilot.press("l")
        table = pilot.app.focused
        assert table.get_cell_at(table.cursor_coordinate).color_value == "#a8a29e"
        await pilot.click("#btn_confirm_category")

        # check value
        assert pilot.app.focused.value == "Test Category"

        # save task
        await pilot.click("#btn_continue")
        assert isinstance(pilot.app.screen, MainView)
        assert len(pilot.app.task_list) == 1
        await pilot.pause(delay=0.5)
        assert pilot.app.focused.id == "taskcard_1"


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
        assert pilot.app.screen.query_exactly_one(CategorySelector).value == "green"

        # add 1 to title
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
        assert pilot.app.screen.query_exactly_one(CategorySelector).value == "green"

        # add 1 to title
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
        assert isinstance(pilot.app.screen, MainView)
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
        await pilot.click("#btn_continue_delete")
        assert isinstance(pilot.app.screen, MainView)
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
