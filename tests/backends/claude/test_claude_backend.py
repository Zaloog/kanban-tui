import os
import json
from pathlib import Path
import pytest

from kanban_tui.app import KanbanTui
from kanban_tui.backends.claude.backend import ClaudeBackend
from kanban_tui.config import ClaudeBackendSettings, Backends


@pytest.fixture
def temp_claude_tasks(tmp_path: Path):
    """Create a temporary Claude tasks directory with test data."""
    # Create a session directory
    session_id = "test-session-123"
    session_path = tmp_path / session_id
    session_path.mkdir()

    # Create test tasks
    tasks = [
        {
            "id": "1",
            "subject": "Implement feature X",
            "description": "Add new functionality",
            "activeForm": "Implementing feature X",
            "status": "in_progress",
            "blocks": ["2"],
            "blockedBy": [],
        },
        {
            "id": "2",
            "subject": "Test feature X",
            "description": "Write tests",
            "activeForm": "Testing feature X",
            "status": "pending",
            "blocks": [],
            "blockedBy": ["1"],
        },
        {
            "id": "3",
            "subject": "Deploy to production",
            "description": "Deploy the changes",
            "activeForm": "Deploying to production",
            "status": "completed",
            "blocks": [],
            "blockedBy": [],
        },
    ]

    for task in tasks:
        task_file = session_path / f"{task['id']}.json"
        task_file.write_text(json.dumps(task, indent=2))

    yield tmp_path, session_id


def test_claude_backend_get_boards(temp_claude_tasks):
    """Test that boards are created from session directories."""
    tasks_path, session_id = temp_claude_tasks

    settings = ClaudeBackendSettings(
        tasks_base_path=str(tasks_path), active_session_id=session_id
    )
    backend = ClaudeBackend(settings)

    boards = backend.get_boards()
    assert len(boards) == 1
    assert boards[0].name == session_id
    assert boards[0].icon == "🤖"
    assert boards[0].reset_column == 1
    assert boards[0].start_column == 2
    assert boards[0].finish_column == 3


def test_claude_backend_get_columns(temp_claude_tasks):
    """Test that columns are properly defined."""
    tasks_path, session_id = temp_claude_tasks

    settings = ClaudeBackendSettings(
        tasks_base_path=str(tasks_path), active_session_id=session_id
    )
    backend = ClaudeBackend(settings)

    columns = backend.get_columns()
    assert len(columns) == 3
    assert columns[0].name == "pending"
    assert columns[1].name == "in_progress"
    assert columns[2].name == "completed"


def test_claude_backend_get_tasks(temp_claude_tasks):
    """Test that tasks are read and converted correctly."""
    tasks_path, session_id = temp_claude_tasks

    settings = ClaudeBackendSettings(
        tasks_base_path=str(tasks_path), active_session_id=session_id
    )
    backend = ClaudeBackend(settings)

    tasks = backend.get_tasks_on_active_board()
    assert len(tasks) == 3

    # Check task mapping
    task1 = next(t for t in tasks if t.task_id == 1)
    assert task1.title == "Implement feature X"
    assert task1.column == 2  # in_progress → Doing
    assert task1.blocking == [2]
    assert task1.blocked_by == []
    assert task1.metadata["activeForm"] == "Implementing feature X"

    task2 = next(t for t in tasks if t.task_id == 2)
    assert task2.title == "Test feature X"
    assert task2.column == 1  # pending → Ready
    assert task2.blocking == []
    assert task2.blocked_by == [1]

    task3 = next(t for t in tasks if t.task_id == 3)
    assert task3.title == "Deploy to production"
    assert task3.column == 3  # completed → Done
    assert task3.finished is True


def test_claude_backend_get_task_by_id(temp_claude_tasks):
    """Test fetching a specific task by ID."""
    tasks_path, session_id = temp_claude_tasks

    settings = ClaudeBackendSettings(
        tasks_base_path=str(tasks_path), active_session_id=session_id
    )
    backend = ClaudeBackend(settings)

    task = backend.get_task_by_id(1)
    assert task is not None
    assert task.title == "Implement feature X"

    # Non-existent task
    task = backend.get_task_by_id(999)
    assert task is None


def test_claude_backend_read_only_operations(temp_claude_tasks):
    """Test that write operations raise NotImplementedError."""
    tasks_path, session_id = temp_claude_tasks

    settings = ClaudeBackendSettings(
        tasks_base_path=str(tasks_path), active_session_id=session_id
    )
    backend = ClaudeBackend(settings)

    # All write operations should raise NotImplementedError
    with pytest.raises(NotImplementedError):
        backend.create_new_board("Test Board")

    with pytest.raises(NotImplementedError):
        backend.create_new_task("Test Task", "Description", 1)

    with pytest.raises(NotImplementedError):
        backend.create_task_dependency(1, 2)


def test_claude_backend_empty_directory(tmp_path, test_app: KanbanTui):
    """Test backend behavior with no sessions."""
    os.environ["CLAUDE_CODE_CONFIG_DIR"] = tmp_path.as_posix()
    test_app.config.set_backend(Backends("claude"))
    backend = test_app.get_backend()

    boards = backend.get_boards()
    assert len(boards) == 0

    # Should raise exception when no boards exist
    with pytest.raises(Exception, match="No Claude task sessions found"):
        _ = backend.active_board
