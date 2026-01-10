import pytest
from datetime import datetime
from freezegun import freeze_time
from click.testing import CliRunner
from click.exceptions import UsageError

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
    days_left=None,
    days_since_creation=0,
    finished=False
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
    days_left=None,
    days_since_creation=0,
    finished=False
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
    days_left=None,
    days_since_creation=0,
    finished=False
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
    days_left=None,
    days_since_creation=0,
    finished=False
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
    days_left=None,
    days_since_creation=0,
    finished=False
)
"""


def test_task_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["task", "list"], obj=test_app)
        assert result.exit_code == 2
        assert pytest.raises(UsageError)


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
        assert (
            result.output
            == "Target column is not on the active board, still continue? [y/N]: n\nAborted!\n"
        )
