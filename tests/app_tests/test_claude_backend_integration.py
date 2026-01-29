"""Integration tests for Claude backend in the TUI app."""

from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen

from kanban_tui.modal.modal_confirm_screen import ModalConfirmScreen

from kanban_tui.widgets.task_card import TaskCard

import json
import os
from pathlib import Path
import pytest

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends

APP_SIZE = (150, 50)


@pytest.fixture
def temp_claude_tasks_env(tmp_path: Path):
    """Create a temporary Claude tasks directory with test data."""
    # Create a session directory
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()

    session_id = "test-session-123"
    session_path = tmp_path / "tasks" / session_id
    session_path.mkdir(parents=True)

    # Create test tasks
    tasks = [
        {
            "id": "1",
            "subject": "Integration test task",
            "description": "Testing Claude backend in TUI",
            "activeForm": "Testing integration",
            "status": "in_progress",
            "blocks": [],
            "blockedBy": [],
        },
        {
            "id": "2",
            "subject": "Completed task",
            "description": "Already done",
            "activeForm": "Completing task",
            "status": "completed",
            "blocks": [],
            "blockedBy": [],
        },
    ]

    for task in tasks:
        task_file = session_path / f"{task['id']}.json"
        task_file.write_text(json.dumps(task, indent=2))

    yield tmp_path, session_id


def test_claude_backend_can_be_selected(test_app, temp_claude_tasks_env):
    """Test that Claude backend can be instantiated in the app."""
    tasks_path, session_id = temp_claude_tasks_env

    test_app.config.backend.mode = Backends.CLAUDE
    test_app.config.backend.claude_settings.active_session_id = session_id

    # Get backend should work
    backend = test_app.get_backend()
    assert backend is not None

    # Should be able to get boards
    boards = backend.get_boards()
    assert len(boards) == 1
    assert boards[0].name == session_id

    # Should be able to get tasks
    tasks = backend.get_tasks_on_active_board()
    assert len(tasks) == 2

    # Verify task statuses mapped correctly
    task1 = next(t for t in tasks if t.task_id == 1)
    assert task1.column == 2  # in_progress -> Doing

    task2 = next(t for t in tasks if t.task_id == 2)
    assert task2.column == 3  # completed -> Done


def test_claude_backend_settings_in_config(test_app: KanbanTui):
    """Test that Claude backend settings are part of config."""
    test_app.config.set_backend(Backends.CLAUDE)
    test_app.backend = test_app.get_backend()

    assert hasattr(test_app.backend.settings, "tasks_base_path")
    assert hasattr(test_app.backend.settings, "active_session_id")

    # Test default values
    assert test_app.backend.settings.tasks_base_path == "~/.claude/tasks"
    assert test_app.backend.settings.active_session_id == ""


def test_claude_backend_read_only_operations(temp_claude_tasks_env, test_app):
    """Test that write operations raise NotImplementedError."""
    tasks_path, session_id = temp_claude_tasks_env

    test_app.config.backend.mode = Backends.CLAUDE
    test_app.config.backend.claude_settings.active_session_id = session_id

    backend = test_app.get_backend()

    # All write operations should raise NotImplementedError
    with pytest.raises(NotImplementedError, match="read-only"):
        backend.create_new_task("Test", "Description", 1)

    with pytest.raises(NotImplementedError, match="read-only"):
        backend.create_new_board("Test Board")


async def test_claude_backend_move_task(temp_claude_tasks_env, test_app: KanbanTui):
    """Test that write operations raise NotImplementedError."""
    tasks_path, session_id = temp_claude_tasks_env

    test_app.config.backend.mode = Backends.CLAUDE
    test_app.config.backend.claude_settings.active_session_id = session_id
    test_app.backend = test_app.get_backend()

    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert isinstance(test_app.focused, TaskCard)
        assert test_app.focused.task_.task_id == 1
        assert test_app.focused.task_.column == 2

        await pilot.press("L")
        assert test_app.focused.task_.task_id == 1
        assert test_app.focused.task_.column == 3


async def test_claude_backend_delete_task(temp_claude_tasks_env, test_app: KanbanTui):
    """Test that write operations raise NotImplementedError."""
    tasks_path, session_id = temp_claude_tasks_env

    test_app.config.backend.mode = Backends.CLAUDE
    test_app.config.backend.claude_settings.active_session_id = session_id
    test_app.backend = test_app.get_backend()

    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert isinstance(test_app.focused, TaskCard)
        assert test_app.focused.task_.task_id == 1
        assert test_app.focused.task_.column == 2

        await pilot.press("d")
        await pilot.press("enter")
        assert len(test_app.task_list) == 1

        assert not (tasks_path / "tasks" / session_id / "1.json").exists()


async def test_claude_backend_update_task(temp_claude_tasks_env, test_app: KanbanTui):
    """Test that write operations raise NotImplementedError."""
    tasks_path, session_id = temp_claude_tasks_env

    test_app.config.backend.mode = Backends.CLAUDE
    test_app.config.backend.claude_settings.active_session_id = session_id
    test_app.backend = test_app.get_backend()

    async with test_app.run_test(size=APP_SIZE) as pilot:
        assert isinstance(test_app.focused, TaskCard)
        await pilot.press("e")
        assert isinstance(test_app.screen, ModalTaskEditScreen)
        # edit title
        await pilot.press(*" update")
        await pilot.press("tab")
        # edit title
        await pilot.press(*" edit")
        await pilot.press("ctrl+j")
        assert test_app.focused.task_.title == "Integration test task update"

    task_string = (tasks_path / "tasks" / session_id / "1.json").read_text(
        encoding="utf-8"
    )
    assert "update" in task_string
    assert "edit" in task_string


async def test_claude_backend_delete_board(temp_claude_tasks_env, test_app: KanbanTui):
    """Test that write operations raise NotImplementedError."""
    tasks_path, session_id = temp_claude_tasks_env

    session_name = "test-session-to-delete"
    session_path = tasks_path / "tasks" / session_name
    session_path.mkdir(parents=True)

    test_app.config.backend.mode = Backends.CLAUDE
    test_app.config.backend.claude_settings.active_session_id = session_id
    test_app.backend = test_app.get_backend()

    async with test_app.run_test(size=APP_SIZE) as pilot:
        # Open Boards and move to board to be deleted
        await pilot.press("B")
        await pilot.press("j")
        assert len(test_app.board_list) == 2

        # delete
        await pilot.press("d")
        assert isinstance(test_app.screen, ModalConfirmScreen)
        # + confirm
        await pilot.press("enter")
        assert len(test_app.board_list) == 1

        assert not (tasks_path / "tasks" / session_name).exists()
