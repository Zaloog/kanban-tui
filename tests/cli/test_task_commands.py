import pytest
from datetime import datetime
from freezegun import freeze_time
from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.config import Backends

TEST_TASK_OUTPUT = """Task(
    task_id=1,
    title='Task_ready_0',
    column=1,
    creation_date=datetime.datetime(2026, 4, 2, 13, 3, 7),
    start_date=None,
    finish_date=None,
    category=1,
    due_date=None,
    description='Hallo',
    blocked_by=[],
    blocking=[],
    metadata={},
    days_left=None,
    days_since_creation=0,
    finished=False,
    is_blocked=False,
    has_dependents=False
)
Task(
    task_id=2,
    title='Task_ready_1',
    column=1,
    creation_date=datetime.datetime(2026, 4, 2, 13, 3, 7),
    start_date=None,
    finish_date=None,
    category=3,
    due_date=None,
    description='Hallo',
    blocked_by=[],
    blocking=[],
    metadata={},
    days_left=None,
    days_since_creation=0,
    finished=False,
    is_blocked=False,
    has_dependents=False
)
Task(
    task_id=3,
    title='Task_ready_2',
    column=1,
    creation_date=datetime.datetime(2026, 4, 2, 13, 3, 7),
    start_date=None,
    finish_date=None,
    category=None,
    due_date=None,
    description='Hallo',
    blocked_by=[],
    blocking=[],
    metadata={},
    days_left=None,
    days_since_creation=0,
    finished=False,
    is_blocked=False,
    has_dependents=False
)
Task(
    task_id=4,
    title='Task_doing_0',
    column=2,
    creation_date=datetime.datetime(2026, 4, 2, 13, 3, 7),
    start_date=None,
    finish_date=None,
    category=2,
    due_date=None,
    description='Hallo',
    blocked_by=[],
    blocking=[],
    metadata={},
    days_left=None,
    days_since_creation=0,
    finished=False,
    is_blocked=False,
    has_dependents=False
)
Task(
    task_id=5,
    title='Task_done_0',
    column=3,
    creation_date=datetime.datetime(2026, 4, 2, 13, 3, 7),
    start_date=None,
    finish_date=None,
    category=1,
    due_date=None,
    description='Hallo',
    blocked_by=[],
    blocking=[],
    metadata={},
    days_left=None,
    days_since_creation=0,
    finished=False,
    is_blocked=False,
    has_dependents=False
)
"""

TEST_TASK_OUTPUT_JSON = """[
    {
        "task_id": 1,
        "title": "Task_ready_0",
        "column": 1,
        "creation_date": "2026-04-02T13:03:07",
        "category": 1,
        "description": "Hallo",
        "days_since_creation": 0,
        "finished": false,
        "is_blocked": false,
        "has_dependents": false
    },
    {
        "task_id": 2,
        "title": "Task_ready_1",
        "column": 1,
        "creation_date": "2026-04-02T13:03:07",
        "category": 3,
        "description": "Hallo",
        "days_since_creation": 0,
        "finished": false,
        "is_blocked": false,
        "has_dependents": false
    },
    {
        "task_id": 3,
        "title": "Task_ready_2",
        "column": 1,
        "creation_date": "2026-04-02T13:03:07",
        "description": "Hallo",
        "days_since_creation": 0,
        "finished": false,
        "is_blocked": false,
        "has_dependents": false
    },
    {
        "task_id": 4,
        "title": "Task_doing_0",
        "column": 2,
        "creation_date": "2026-04-02T13:03:07",
        "category": 2,
        "description": "Hallo",
        "days_since_creation": 0,
        "finished": false,
        "is_blocked": false,
        "has_dependents": false
    },
    {
        "task_id": 5,
        "title": "Task_done_0",
        "column": 3,
        "creation_date": "2026-04-02T13:03:07",
        "category": 1,
        "description": "Hallo",
        "days_since_creation": 0,
        "finished": false,
        "is_blocked": false,
        "has_dependents": false
    }
]
"""

SINGLE_TASK_JSON = """[
    {
        "task_id": 4,
        "title": "Task_doing_0",
        "column": 2,
        "creation_date": "2026-04-02T13:03:07",
        "category": 2,
        "description": "Hallo",
        "days_since_creation": 0,
        "finished": false,
        "is_blocked": false,
        "has_dependents": false
    }
]
"""


def test_task_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["task", "list"], obj=test_app)
        assert result.exit_code == 2
        assert (
            f"Currently using `{test_app.config.backend.mode}` backend."
            in result.output
        )
        assert (
            f"Please change the backend to `{Backends.SQLITE}` before using the `task` command."
            in result.output
        )


def test_task_list(test_app):
    # Use freezing here to keep days_since_creation the same
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, args=["task", "list"], obj=test_app)
            assert result.exit_code == 0
            # Replace __repr__ shows the FakeDatetime on creation, use a replace here to make the assert correct
            assert (
                result.output.replace("FakeDatetime", "datetime.datetime")
                == TEST_TASK_OUTPUT
            )


def test_task_list_json(test_app):
    # Use freezing here to keep days_since_creation the same
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, args=["task", "list", "--json"], obj=test_app)
            assert result.exit_code == 0
            assert result.output == TEST_TASK_OUTPUT_JSON


def test_task_list_json_filter(test_app):
    # Use freezing here to keep days_since_creation the same
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, args=["task", "list", "--json", "--column", "2"], obj=test_app
            )
            assert result.exit_code == 0
            assert result.output == SINGLE_TASK_JSON


def test_task_list_filter_no_task_in_column(test_app):
    # Use freezing here to keep days_since_creation the same
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, args=["task", "list", "--column", "4"], obj=test_app
            )
            assert result.exit_code == 0
            assert result.output == "No tasks in column with column_id = 4.\n"


def test_task_list_filter_board_(test_app):
    # Use freezing here to keep days_since_creation the same
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, args=["task", "list", "--board", "1", "--json"], obj=test_app
            )
            assert result.exit_code == 0
            assert result.output == TEST_TASK_OUTPUT_JSON


def test_task_list_filter_no_board_with_id(test_app):
    # Use freezing here to keep days_since_creation the same
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, args=["task", "list", "--board", "4"], obj=test_app
            )
            assert result.exit_code == 0
            assert result.output == "There is no board with board_id = 4.\n"


def test_task_list_no_board(empty_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["task", "list"], obj=empty_app)
        assert result.exit_code == 0
        assert result.output == "No boards created yet.\n"


def test_task_list_no_task(no_task_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["task", "list"], obj=no_task_app)
        assert result.exit_code == 0
        assert result.output == "No tasks created yet.\n"


def test_task_create_minimal(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "CLI Test Task",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Created task `CLI Test Task` with task_id = 6.\n"
        assert len(test_app.backend.get_tasks_on_active_board()) == 6


@pytest.mark.parametrize(
    "title,description,due_date",
    [
        ("CLI Test Task", "", None),
        ("CLI Test Task", "Easy Description", None),
        (
            "CLI Test Task",
            """# MarkdownEasy Description
            - Subtask 1
            - Subtask 2
            """,
            None,
        ),
        ("CLI Test Task", "", "2026-01-01"),
    ],
)
def test_task_create_all_options(
    test_app, title: str, description: str | None, due_date: str | None
):
    runner = CliRunner()
    all_args = ["task", "create", title]
    if description:
        all_args.extend(["--description", description])
    if due_date:
        all_args.extend(["--due-date", due_date])
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=all_args,
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == f"Created task `{title}` with task_id = 6.\n"

        tasks = test_app.backend.get_tasks_on_active_board()
        assert len(tasks) == 6

        new_task = tasks[-1]
        assert new_task.title == title
        assert new_task.description == description

        if due_date:
            assert new_task.due_date.strftime("%Y-%m-%d") == due_date
        else:
            assert new_task.due_date is due_date


def test_task_delete_fail_wrong_id(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "delete",
                "7",
            ],
            input="y",
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "There is no task with task_id = 7.\n"


def test_task_delete_success(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, args=["task", "delete", "5"], input="y", obj=test_app
        )
        assert result.exit_code == 0
        assert (
            result.output
            == "Do you want to delete the task with task_id = 5  [y/N]: y\nDeleted task with task_id = 5.\n"
        )
        assert len(test_app.backend.get_tasks_on_active_board()) == 4


def test_task_delete_abort(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, args=["task", "delete", "5"], input="n", obj=test_app
        )
        assert result.exit_code == 1
        assert (
            result.output
            == "Do you want to delete the task with task_id = 5  [y/N]: n\nAborted!\n"
        )
        assert len(test_app.backend.get_tasks_on_active_board()) == 5


def test_task_delete_success_no_confirm(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, args=["task", "delete", "5", "--no-confirm"], obj=test_app
        )
        assert result.exit_code == 0
        assert result.output == "Deleted task with task_id = 5.\n"
        assert len(test_app.backend.get_tasks_on_active_board()) == 4


def test_task_delete_fail_no_tasks(no_task_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, args=["task", "delete", "2", "--no-confirm"], obj=no_task_app
        )
        assert result.exit_code == 0
        assert result.output == "There is no task with task_id = 2.\n"
        assert len(no_task_app.backend.get_tasks_on_active_board()) == 0


def test_task_update_no_fields(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["task", "update", "2"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == "No fields to update provided.\n"


@pytest.mark.parametrize(
    "title,description,due_date",
    [
        ("CLI Test Task", None, None),
        ("CLI Test Task", "Easy Description", None),
        (
            "CLI Test Task",
            """# MarkdownEasy Description
            - Subtask 1
            - Subtask 2
            """,
            None,
        ),
        ("CLI Test Task", None, "2026-01-01"),
    ],
)
def test_task_update_all_options(
    test_app, title: str, description: str | None, due_date: str | None
):
    runner = CliRunner()
    task_id = 1
    old_task = test_app.backend.get_task_by_id(task_id=task_id)
    all_args = ["task", "update", f"{task_id}"]
    if title:
        all_args.extend(["--title", title])
    if description:
        all_args.extend(["--description", description])
    if due_date:
        all_args.extend(["--due-date", due_date])

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=all_args,
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == f"Updated task with {task_id = }.\n"

        updated_task = test_app.backend.get_task_by_id(task_id=task_id)

        if title:
            assert updated_task.title == title
        else:
            assert updated_task.title is old_task.title

        if description:
            assert updated_task.description == description
        else:
            assert updated_task.description == old_task.description

        if due_date:
            assert updated_task.due_date.strftime("%Y-%m-%d") == due_date
        else:
            assert updated_task.due_date is old_task.due_date


def test_task_move_success(test_app):
    runner = CliRunner()
    task_id = 1
    target_column = 2

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["task", "move", f"{task_id}", f"{target_column}"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == f"Moved task with {task_id = } from column 1 to 2.\n"

    moved_task = test_app.backend.get_task_by_id(task_id=task_id)
    assert moved_task.column == target_column


def test_task_move_fail_task_already_in_column(test_app):
    runner = CliRunner()
    task_id = 1
    target_column = 1

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["task", "move", f"{task_id}", f"{target_column}"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert (
            result.output
            == f"Task with {task_id = } is already in column {target_column}.\n"
        )


def test_task_move_fail_wrong_task_id(test_app):
    runner = CliRunner()
    task_id = 10
    target_column = 1

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["task", "move", f"{task_id}", f"{target_column}"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == f"There is no task with {task_id = }.\n"


def test_task_move_fail_wrong_column_id(test_app):
    runner = CliRunner()
    task_id = 1
    target_column = 10

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["task", "move", f"{task_id}", f"{target_column}"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert (
            result.output == f"There is no column with column_id = {target_column}.\n"
        )


def test_task_move_confirm_column_not_active_board(test_app):
    runner = CliRunner()
    task_id = 1
    # column is on new board
    target_column = 6

    with runner.isolated_filesystem():
        # create 2nd board first
        runner.invoke(
            cli,
            args=["board", "create", "'CLI Test'", "--icon", ":books:"],
            obj=test_app,
        )
        result = runner.invoke(
            cli,
            args=["task", "move", f"{task_id}", f"{target_column}"],
            input="y",
            obj=test_app,
        )
        assert result.exit_code == 0
        assert (
            result.output
            == f"Target column is not on the active board, still continue? [y/N]: y\nMoved task with {task_id = } from column 1 to 6.\n"
        )


def test_task_move_confirm_task_not_active_board(test_app):
    runner = CliRunner()
    task_id = 6
    # column is on new board
    target_column = 1

    with runner.isolated_filesystem():
        # create 2nd board, activate and create a task there first
        runner.invoke(
            cli,
            args=["board", "create", "'CLI Test'", "--icon", ":books:", "--set-active"],
            obj=test_app,
        )
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "Task on other Board",
            ],
            obj=test_app,
        )
        result = runner.invoke(
            cli,
            args=[
                "board",
                "activate",
                "1",
            ],
            obj=test_app,
        )
        result = runner.invoke(
            cli,
            args=["task", "move", f"{task_id}", f"{target_column}"],
            input="y",
            obj=test_app,
        )
        assert result.exit_code == 0
        assert (
            result.output
            == f"Task is not on the active board, still continue? [y/N]: y\nMoved task with {task_id = } from column 5 to 1.\n"
        )
        assert test_app.backend.get_tasks_on_active_board()[-1].task_id == 6


def test_task_move_abort_column_not_active_board(test_app):
    runner = CliRunner()
    task_id = 1
    # column is on new board
    target_column = 6

    with runner.isolated_filesystem():
        # create 2nd board first
        runner.invoke(
            cli,
            args=["board", "create", "'CLI Test'", "--icon", ":books:"],
            obj=test_app,
        )
        result = runner.invoke(
            cli,
            args=["task", "move", f"{task_id}", f"{target_column}"],
            input="n",
            obj=test_app,
        )
        assert result.exit_code == 1
        expected_output = (
            "Target column is not on the active board, still continue? [y/N]: n\n"
            "Aborted!\n"
        )
        assert result.output == expected_output


def test_task_move_blocked_by_dependency(test_app):
    """Test that moving a task to start column is blocked when dependencies are unfinished."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create two tasks: task A (id=6) and task B (id=7)
        runner.invoke(
            cli,
            args=["task", "create", "Task A"],
            obj=test_app,
        )
        runner.invoke(
            cli,
            args=["task", "create", "Task B", "--depends-on", "6"],
            obj=test_app,
        )

        # Try to move task B (id=7) to the start column (id=2, "Doing")
        # This should be blocked because task A (id=6) is not finished
        result = runner.invoke(
            cli,
            args=["task", "move", "7", "2"],
            obj=test_app,
        )

        assert result.exit_code == 0
        expected_output = "Cannot move task: Task is blocked by unfinished dependencies: #6 'Task A'\n"
        assert result.output == expected_output

        # Verify task B is still in original column
        task_b = test_app.backend.get_task_by_id(task_id=7)
        assert task_b.column == 1  # Still in Ready column


def test_task_move_not_blocked_when_dependency_finished(test_app):
    """Test that moving a task is allowed when all dependencies are finished."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create two tasks: task A (id=6) and task B (id=7)
        runner.invoke(
            cli,
            args=["task", "create", "Task A"],
            obj=test_app,
        )
        runner.invoke(
            cli,
            args=["task", "create", "Task B", "--depends-on", "6"],
            obj=test_app,
        )

        # Move task A to Doing (start column)
        runner.invoke(
            cli,
            args=["task", "move", "6", "2"],
            obj=test_app,
        )
        # Move task A to Done (finish column) to mark it as finished
        runner.invoke(
            cli,
            args=["task", "move", "6", "3"],
            obj=test_app,
        )

        # Now try to move task B to Doing - should succeed
        result = runner.invoke(
            cli,
            args=["task", "move", "7", "2"],
            obj=test_app,
        )

        assert result.exit_code == 0
        assert result.output == "Moved task with task_id = 7 from column 1 to 2.\n"

        # Verify task B was moved
        task_b = test_app.backend.get_task_by_id(task_id=7)
        assert task_b.column == 2


def test_task_move_not_blocked_when_not_moving_to_start_column(test_app):
    """Test that dependency blocking only applies when moving to start column."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create two tasks: task A (id=6) and task B (id=7)
        runner.invoke(
            cli,
            args=["task", "create", "Task A"],
            obj=test_app,
        )
        runner.invoke(
            cli,
            args=["task", "create", "Task B", "--depends-on", "6"],
            obj=test_app,
        )

        # Move task B to Done column (not start column) - should succeed even though A is unfinished
        result = runner.invoke(
            cli,
            args=["task", "move", "7", "3"],
            obj=test_app,
        )

        assert result.exit_code == 0
        assert result.output == "Moved task with task_id = 7 from column 1 to 3.\n"

        # Verify task B was moved
        task_b = test_app.backend.get_task_by_id(task_id=7)
        assert task_b.column == 3


# Task Dependency Tests


def test_task_create_with_single_dependency(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "Dependent Task",
                "--depends-on",
                "1",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        expected_output = """Created task `Dependent Task` with task_id = 6.
Added dependency: task 6 depends on task 1.
"""
        assert result.output == expected_output

        # Verify the dependency was created
        new_task = test_app.backend.get_task_by_id(task_id=6)
        assert new_task.blocked_by == [1]

        # Verify the blocking task knows about it
        blocking_task = test_app.backend.get_task_by_id(task_id=1)
        assert 6 in blocking_task.blocking


def test_task_create_with_multiple_dependencies(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "Multi-Dependent Task",
                "--depends-on",
                "1",
                "--depends-on",
                "2",
                "--depends-on",
                "3",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        expected_output = """Created task `Multi-Dependent Task` with task_id = 6.
Added dependency: task 6 depends on task 1.
Added dependency: task 6 depends on task 2.
Added dependency: task 6 depends on task 3.
"""
        assert result.output == expected_output

        # Verify all dependencies were created
        new_task = test_app.backend.get_task_by_id(task_id=6)
        assert sorted(new_task.blocked_by) == [1, 2, 3]


def test_task_create_with_nonexistent_dependency(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "Task with Bad Dependency",
                "--depends-on",
                "999",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        expected_output = """Created task `Task with Bad Dependency` with task_id = 6.
Task 999 does not exist, skipping dependency.
"""
        assert result.output == expected_output

        # Verify the task was created but without the dependency
        new_task = test_app.backend.get_task_by_id(task_id=6)
        assert new_task.blocked_by == []


def test_task_create_with_mixed_valid_invalid_dependencies(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "Mixed Dependencies Task",
                "--depends-on",
                "1",
                "--depends-on",
                "999",
                "--depends-on",
                "2",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        expected_output = """Created task `Mixed Dependencies Task` with task_id = 6.
Added dependency: task 6 depends on task 1.
Task 999 does not exist, skipping dependency.
Added dependency: task 6 depends on task 2.
"""
        assert result.output == expected_output

        # Verify only valid dependencies were created
        new_task = test_app.backend.get_task_by_id(task_id=6)
        assert sorted(new_task.blocked_by) == [1, 2]


def test_task_create_with_circular_dependency_direct(test_app):
    """Test creating a task that would create a direct circular dependency"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # First create task 6
        runner.invoke(
            cli,
            args=["task", "create", "Task 6"],
            obj=test_app,
        )

        # Make task 1 depend on task 6
        test_app.backend.create_task_dependency(task_id=1, depends_on_task_id=6)

        # Now try to create task 7 that depends on task 1
        runner.invoke(
            cli,
            args=["task", "create", "Task 7", "--depends-on", "1"],
            obj=test_app,
        )

        # Create task 8 that depends on task 7
        result = runner.invoke(
            cli,
            args=["task", "create", "Task 8", "--depends-on", "7"],
            obj=test_app,
        )
        # This should succeed
        assert result.exit_code == 0

        # Check that creating 6 -> 8 would create a cycle (8 -> 7 -> 1 -> 6)

        from kanban_tui.backends.sqlite.database import would_create_cycle

        assert would_create_cycle(6, 8, test_app.backend.database_path)


def test_task_create_with_circular_dependency_indirect(test_app):
    """Test creating a task that would create an indirect circular dependency"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a chain: task 6 -> task 1 -> task 2
        runner.invoke(
            cli, args=["task", "create", "Task 6", "--depends-on", "1"], obj=test_app
        )
        test_app.backend.create_task_dependency(task_id=1, depends_on_task_id=2)

        # Now try to make task 2 depend on task 6 (would create cycle: 6 -> 1 -> 2 -> 6)
        result = runner.invoke(
            cli,
            args=["task", "create", "Task 7", "--depends-on", "6"],
            obj=test_app,
        )
        assert result.exit_code == 0

        # Verify using backend that 2 -> 6 would create a cycle
        from kanban_tui.backends.sqlite.database import would_create_cycle

        assert would_create_cycle(2, 6, test_app.backend.database_path)


def test_task_create_self_dependency_prevented(test_app):
    """Test that a task cannot depend on itself"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create task 6 first
        result = runner.invoke(
            cli,
            args=["task", "create", "Self-dependent Task"],
            obj=test_app,
        )
        assert result.exit_code == 0

        # Try to make it depend on itself via backend
        from kanban_tui.backends.sqlite.database import would_create_cycle

        assert would_create_cycle(6, 6, test_app.backend.database_path)


def test_task_create_duplicate_dependency(test_app):
    """Test that duplicate dependencies are handled gracefully"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create first task with dependency on task 1
        result = runner.invoke(
            cli,
            args=["task", "create", "Task 6", "--depends-on", "1"],
            obj=test_app,
        )
        assert result.exit_code == 0
        expected_output = """Created task `Task 6` with task_id = 6.
Added dependency: task 6 depends on task 1.
"""
        assert result.output == expected_output

        # Verify the dependency was created
        task_deps = test_app.backend.get_task_dependencies(task_id=6)
        assert task_deps == [1]

        # Try to create a task with duplicate dependency flags
        result2 = runner.invoke(
            cli,
            args=["task", "create", "Task 7", "--depends-on", "1", "--depends-on", "1"],
            obj=test_app,
        )
        assert result2.exit_code == 0
        # Should only add the dependency once
        expected_output2 = """Created task `Task 7` with task_id = 7.
Added dependency: task 7 depends on task 1.
Task 7 already depends on task 1.
"""
        assert result2.output == expected_output2


def test_task_dependencies_persist_in_json_output(test_app):
    """Test that dependencies appear in JSON output"""
    runner = CliRunner()
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        with runner.isolated_filesystem():
            # Create a task with dependencies
            runner.invoke(
                cli,
                args=[
                    "task",
                    "create",
                    "Dependent Task",
                    "--depends-on",
                    "1",
                    "--depends-on",
                    "2",
                ],
                obj=test_app,
            )

            # Get JSON output
            result = runner.invoke(cli, args=["task", "list", "--json"], obj=test_app)
            assert result.exit_code == 0

            import json

            tasks = json.loads(result.output)

            # Find the newly created task
            new_task = [t for t in tasks if t["task_id"] == 6][0]
            assert sorted(new_task["blocked_by"]) == [1, 2]
            assert new_task["is_blocked"]
            assert not new_task["has_dependents"]

            # Check that task 1 shows it's blocking task 6
            task_1 = [t for t in tasks if t["task_id"] == 1][0]
            assert 6 in task_1["blocking"]
            assert task_1["has_dependents"]
            assert not task_1["is_blocked"]


def test_task_with_dependencies_computed_fields(test_app):
    """Test that is_blocked and has_dependents computed fields work correctly"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a task with dependencies
        runner.invoke(
            cli,
            args=["task", "create", "Blocked Task", "--depends-on", "1"],
            obj=test_app,
        )

        # Get the task and verify computed fields
        blocked_task = test_app.backend.get_task_by_id(task_id=6)
        assert blocked_task.is_blocked
        assert not blocked_task.has_dependents

        blocking_task = test_app.backend.get_task_by_id(task_id=1)
        assert not blocking_task.is_blocked
        assert blocking_task.has_dependents


def test_task_create_with_circular_dependency_error_message(test_app):
    """Test that circular dependencies are properly detected"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create task 6 that depends on task 1
        runner.invoke(
            cli, args=["task", "create", "Task 6", "--depends-on", "1"], obj=test_app
        )

        # Try to create task 7 that depends on task 1 (which depends on 6)
        runner.invoke(
            cli, args=["task", "create", "Task 7", "--depends-on", "1"], obj=test_app
        )

        # Now manually check if creating 1 -> 6 would create a cycle
        # (since 6 already depends on 1, making 1 depend on 6 would be circular)
        from kanban_tui.backends.sqlite.database import would_create_cycle

        would_cycle = would_create_cycle(1, 6, test_app.backend.database_path)
        assert would_cycle

        # Also verify that the backend raises ValueError when attempting this
        with pytest.raises(ValueError, match="would create a circular dependency"):
            test_app.backend.create_task_dependency(task_id=1, depends_on_task_id=6)


def test_task_list_actionable_no_dependencies(test_app):
    """Test --actionable flag with no dependencies shows all tasks"""
    runner = CliRunner()
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, args=["task", "list", "--actionable"], obj=test_app
            )
            assert result.exit_code == 0
            # All 5 tasks should be shown since none have dependencies
            assert result.output.count("Task(") == 5


def test_task_list_actionable_with_blocked_tasks(test_app):
    """Test --actionable flag filters out blocked tasks"""
    runner = CliRunner()
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        with runner.isolated_filesystem():
            # Create task 6 that depends on task 1 (which is not finished)
            runner.invoke(
                cli,
                args=["task", "create", "Blocked Task", "--depends-on", "1"],
                obj=test_app,
            )

            # List actionable tasks - should exclude task 6
            result = runner.invoke(
                cli, args=["task", "list", "--actionable"], obj=test_app
            )
            assert result.exit_code == 0

            # Should show 5 original tasks but not task 6
            assert result.output.count("Task(") == 5
            assert "Blocked Task" not in result.output


def test_task_list_actionable_with_finished_dependency(test_app):
    """Test --actionable flag includes tasks whose dependencies are finished"""
    runner = CliRunner()
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        with runner.isolated_filesystem():
            # Move task 1 to Done column (column 3) to mark it as finished
            runner.invoke(cli, args=["task", "move", "1", "3"], obj=test_app)

            # Get task 1 and manually finish it
            task1 = test_app.backend.get_task_by_id(task_id=1)
            task1.finish_task()
            test_app.backend.update_task_status(task1)

            # Create task 6 that depends on task 1 (which is now finished)
            runner.invoke(
                cli,
                args=["task", "create", "Unblocked Task", "--depends-on", "1"],
                obj=test_app,
            )

            # List actionable tasks - should include task 6
            result = runner.invoke(
                cli, args=["task", "list", "--actionable"], obj=test_app
            )
            assert result.exit_code == 0

            # Should show all 6 tasks including the unblocked one
            assert result.output.count("Task(") == 6
            assert "Unblocked Task" in result.output


def test_task_list_actionable_with_multiple_dependencies(test_app):
    """Test --actionable flag with multiple dependencies"""
    runner = CliRunner()
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        with runner.isolated_filesystem():
            # Finish task 1
            task1 = test_app.backend.get_task_by_id(task_id=1)
            task1.finish_task()
            test_app.backend.update_task_status(task1)

            # Create task 6 that depends on task 1 (finished) and task 2 (not finished)
            runner.invoke(
                cli,
                args=[
                    "task",
                    "create",
                    "Multi-Dep Task",
                    "--depends-on",
                    "1",
                    "--depends-on",
                    "2",
                ],
                obj=test_app,
            )

            # List actionable tasks - should exclude task 6 because task 2 is not finished
            result = runner.invoke(
                cli, args=["task", "list", "--actionable"], obj=test_app
            )
            assert result.exit_code == 0

            # Should show 5 original tasks but not task 6
            assert result.output.count("Task(") == 5
            assert "Multi-Dep Task" not in result.output

            # Now finish task 2
            task2 = test_app.backend.get_task_by_id(task_id=2)
            task2.finish_task()
            test_app.backend.update_task_status(task2)

            # List actionable tasks again - should now include task 6
            result = runner.invoke(
                cli, args=["task", "list", "--actionable"], obj=test_app
            )
            assert result.exit_code == 0

            # Should show all 6 tasks
            assert result.output.count("Task(") == 6
            assert "Multi-Dep Task" in result.output


def test_task_list_actionable_json_format(test_app):
    """Test --actionable flag with JSON output"""
    runner = CliRunner()
    with freeze_time(datetime(year=2026, month=4, day=2, hour=13, minute=3, second=7)):
        with runner.isolated_filesystem():
            # Create blocked task
            runner.invoke(
                cli,
                args=["task", "create", "Blocked Task", "--depends-on", "1"],
                obj=test_app,
            )

            # List actionable tasks in JSON format
            result = runner.invoke(
                cli, args=["task", "list", "--actionable", "--json"], obj=test_app
            )
            assert result.exit_code == 0

            import json

            tasks = json.loads(result.output)

            # Should have 5 tasks (excluding the blocked one)
            assert len(tasks) == 5

            # None of the returned tasks should be task 6
            task_ids = [t["task_id"] for t in tasks]
            assert 6 not in task_ids


def test_task_create_with_category(test_app):
    """Test creating a task with a category"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "Task with Category",
                "--category",
                "1",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Created task `Task with Category` with task_id = 6.\n"

        # Verify the task has the correct category
        tasks = test_app.backend.get_tasks_on_active_board()
        new_task = tasks[-1]
        assert new_task.category == 1


def test_task_update_category(test_app):
    """Test updating a task's category"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a task without category first
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "Task to Update",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0

        # Now update it with a category
        result = runner.invoke(
            cli,
            args=[
                "task",
                "update",
                "6",
                "--category",
                "2",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Updated task with task_id = 6.\n"

        # Verify the category was updated
        updated_task = test_app.backend.get_task_by_id(task_id=6)
        assert updated_task.category == 2
