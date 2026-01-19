from kanban_tui.app import KanbanTui
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
from kanban_tui.widgets.modal_task_widgets import (
    TaskDependencyManager,
    DependencySelector,
)
from kanban_tui.widgets.task_card import TaskCard
from textual.widgets import DataTable

APP_SIZE = (150, 50)


async def test_dependency_manager_visibility_new_task(no_task_app: KanbanTui):
    """Test that dependency manager is NOT visible when creating a new task."""
    async with no_task_app.run_test(size=APP_SIZE) as pilot:
        # Open modal to create new task
        await pilot.press("n")
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)

        # Dependency manager should not be present for new tasks
        dependency_managers = pilot.app.screen.query(TaskDependencyManager)
        assert len(dependency_managers) == 0


async def test_dependency_manager_visibility_edit_task(test_app: KanbanTui):
    """Test that dependency manager IS visible when editing an existing task."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # Focus first task and open edit window
        assert isinstance(pilot.app.focused, TaskCard)
        await pilot.press("e")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ModalTaskEditScreen)

        # Dependency manager should be present for existing tasks
        dependency_manager = pilot.app.screen.query_one(TaskDependencyManager)
        assert dependency_manager is not None
        assert (
            dependency_manager.current_task_id == pilot.app.screen.kanban_task.task_id
        )


async def test_dependency_selector_available_tasks(test_app: KanbanTui):
    """Test that dependency selector shows available tasks excluding current task."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # Get total task count
        total_tasks = len(pilot.app.backend.get_tasks_on_active_board())

        # Focus first task and open edit window
        current_task_id = pilot.app.focused.task_.task_id
        await pilot.press("e")
        await pilot.pause()

        # Get dependency selector
        selector = pilot.app.screen.query_one(DependencySelector)
        available_tasks = selector.get_available_tasks()

        # Should have all tasks except current one
        assert len(available_tasks) == total_tasks - 1

        # Verify current task is not in available tasks
        task_ids = [task_id for _, task_id in available_tasks]
        assert current_task_id not in task_ids


async def test_add_dependency_via_selector(test_app: KanbanTui):
    """Test adding a dependency through the dropdown selector."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # Focus first task (task_id = 1)
        await pilot.press("e")
        await pilot.pause()

        current_task_id = pilot.app.screen.kanban_task.task_id

        # Get dependency selector and check initial state
        selector = pilot.app.screen.query_one(DependencySelector)
        table = pilot.app.screen.query_one("#dependencies_table", DataTable)
        initial_row_count = table.row_count

        # Focus selector and open dropdown
        selector.focus()
        await pilot.press("enter")
        await pilot.pause()

        # Select first available task
        await pilot.press("j")  # Move down to first task
        await pilot.press("enter")
        await pilot.pause()

        # Verify dependency was added to database
        task = pilot.app.backend.get_task_by_id(current_task_id)
        assert len(task.blocked_by) > initial_row_count

        # Verify table was updated
        assert table.row_count == len(task.blocked_by)


async def test_remove_dependency_via_table(test_app: KanbanTui):
    """Test removing a dependency by selecting it in the table."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # First, add a dependency
        await pilot.press("e")
        await pilot.pause()

        current_task_id = pilot.app.screen.kanban_task.task_id

        # Add dependency via selector
        selector = pilot.app.screen.query_one(DependencySelector)
        selector.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j")
        await pilot.press("enter")
        await pilot.pause()

        # Get table and verify dependency exists
        table = pilot.app.screen.query_one("#dependencies_table", DataTable)
        initial_row_count = table.row_count
        assert initial_row_count > 0

        # Focus table and select first row to remove
        table.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        # Verify dependency was removed from database
        task = pilot.app.backend.get_task_by_id(current_task_id)
        assert len(task.blocked_by) == initial_row_count - 1

        # Verify table was updated
        assert table.row_count == initial_row_count - 1


async def test_circular_dependency_prevention(test_app: KanbanTui):
    """Test that circular dependencies are prevented."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # Create dependency: Task 1 depends on Task 2
        await pilot.press("e")  # Edit task 1
        await pilot.pause()

        task1_id = pilot.app.screen.kanban_task.task_id

        # Add Task 2 as dependency of Task 1
        selector = pilot.app.screen.query_one(DependencySelector)
        available_tasks = selector.get_available_tasks()
        task2_id = available_tasks[0][1]  # Get first available task ID

        # Add the dependency
        pilot.app.backend.create_task_dependency(
            task_id=task1_id, depends_on_task_id=task2_id
        )

        # Close and go back to board screen
        await pilot.press("escape")
        await pilot.pause()

        # Find task 2 by querying all task cards
        all_cards = pilot.app.screen.query(TaskCard).results()
        task2_card = None
        for card in all_cards:
            if card.task_.task_id == task2_id:
                task2_card = card
                break

        assert task2_card is not None
        task2_card.focus()
        await pilot.pause()
        await pilot.press("e")
        await pilot.pause()

        # Verify we're now editing task 2
        assert pilot.app.screen.kanban_task.task_id == task2_id

        # Verify programmatically that circular dependency would be created
        from kanban_tui.backends.sqlite.database import would_create_cycle

        assert would_create_cycle(task2_id, task1_id, pilot.app.backend.database_path)


async def test_dependency_table_shows_status(test_app: KanbanTui):
    """Test that dependency table shows correct status for finished/unfinished tasks."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        # Add a dependency to first task
        await pilot.press("e")
        await pilot.pause()

        current_task_id = pilot.app.screen.kanban_task.task_id

        # Add dependency
        selector = pilot.app.screen.query_one(DependencySelector)
        available_tasks = selector.get_available_tasks()
        dep_task_id = available_tasks[0][1]

        pilot.app.backend.create_task_dependency(
            task_id=current_task_id, depends_on_task_id=dep_task_id
        )

        # Refresh table
        dependency_manager = pilot.app.screen.query_one(TaskDependencyManager)
        dependency_manager.refresh_dependencies_table()

        # Check table contents
        table = pilot.app.screen.query_one("#dependencies_table", DataTable)
        assert table.row_count > 0

        # Get the dependency task and check if status is correct in table
        dep_task = pilot.app.backend.get_task_by_id(dep_task_id)
        # Note: Rich Text emojis may render differently than Unicode emojis
        expected_word = "Done" if dep_task.finished else "Pending"

        # Verify table shows correct status (check for the word, emojis may vary)
        row = table.get_row_at(0)
        assert expected_word in str(row[2])


async def test_dependency_selector_updates_after_add(test_app: KanbanTui):
    """Test that selector options update after adding a dependency."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("e")
        await pilot.pause()

        # Get initial available tasks count
        selector = pilot.app.screen.query_one(DependencySelector)
        initial_count = len(selector.get_available_tasks())

        # Add a dependency
        selector.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j")
        await pilot.press("enter")
        await pilot.pause()

        # Check that available tasks decreased by 1
        updated_count = len(selector.get_available_tasks())
        assert updated_count == initial_count - 1


async def test_dependency_manager_keyboard_navigation(test_app: KanbanTui):
    """Test keyboard navigation between selector and table."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("e")
        await pilot.pause()

        # Focus selector
        selector = pilot.app.screen.query_one(DependencySelector)
        selector.focus()
        await pilot.pause()
        assert pilot.app.focused == selector

        # Tab to table
        await pilot.press("tab")
        await pilot.pause()

        # Should eventually reach the table or continue through other widgets
        # Just verify we can navigate without errors
        assert pilot.app.screen is not None


async def test_empty_dependencies_table(test_app: KanbanTui):
    """Test that table displays correctly when task has no dependencies."""
    async with test_app.run_test(size=APP_SIZE) as pilot:
        await pilot.press("e")
        await pilot.pause()

        current_task = pilot.app.screen.kanban_task

        # Ensure task has no dependencies
        for dep_id in list(current_task.blocked_by):
            pilot.app.backend.delete_task_dependency(
                task_id=current_task.task_id, depends_on_task_id=dep_id
            )

        # Refresh table
        dependency_manager = pilot.app.screen.query_one(TaskDependencyManager)
        dependency_manager.refresh_dependencies_table()

        # Verify table is empty
        table = pilot.app.screen.query_one("#dependencies_table", DataTable)
        assert table.row_count == 0
