# from kanban_tui.app import KanbanTui
# from textual.widgets import Input, Button
# from kanban_tui.views.main_view import MainView
# from kanban_tui.views.kanbanboard_tab_view import KanbanBoard
# from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
# from kanban_tui.modal.modal_board_screen import (
# ModalBoardOverviewScreen,
# ModalNewBoardScreen,
# )

# from kanban_tui.widgets.task_card import TaskCard
# from kanban_tui.widgets.filter_sidebar import FilterOverlay

# APP_SIZE = (120, 80)


# async def test_kanbanboard(empty_app: KanbanTui):
# async with empty_app.run_test(size=APP_SIZE) as pilot:
# assert len(pilot.app.task_list) == 0
# assert isinstance(pilot.app.screen, MainView)

# assert isinstance(pilot.app.focused, KanbanBoard)


# async def test_kanbanboard_task_creation(empty_app: KanbanTui):
# async with empty_app.run_test(size=APP_SIZE) as pilot:
## open modal to create Task
# await pilot.press("n")
# assert isinstance(pilot.app.screen, ModalTaskEditScreen)
# assert pilot.app.focused.id == "input_title"
# assert pilot.app.query_one("#input_title", Input).value == ""

## Enter new task name
# await pilot.press(*"Test Task")
# assert pilot.app.query_one("#input_title").value == "Test Task"

## save task
# await pilot.click("#btn_continue")
# assert isinstance(pilot.app.screen, MainView)

# assert len(list(pilot.app.query(TaskCard).results())) == 1
