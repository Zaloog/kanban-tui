import pytest
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
    days_since_creation=-86,
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
    days_since_creation=-86,
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
    days_since_creation=-86,
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
    days_since_creation=-86,
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
    days_since_creation=-86,
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
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["task", "list"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == TEST_TASK_OUTPUT


def test_task_list_no_task(no_task_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["task", "list"], obj=no_task_app)
        assert result.exit_code == 0
        assert result.output == "No tasks created yet.\n"


@pytest.mark.skip
def test_task_create(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "task",
                "create",
                "'CLI Test Task'",
                "--description",
                "Make this test pass",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Created Task 'CLI Test Task' with task_id = 2.\n"
        assert len(test_app.backend.get_tasks_on_active_board()) == 6


def test_task_delete_fail_wrong_id(test_app):
    runner = CliRunner()
    # Attempting to delete the active board is not allowed
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


def test_board_delete_abort(test_app):
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


def test_board_delete_success_no_confirm(test_app):
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
    # create board first
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, args=["task", "delete", "2", "--no-confirm"], obj=no_task_app
        )
        assert result.exit_code == 0
        assert result.output == "No tasks created yet.\n"
        assert len(no_task_app.backend.get_tasks_on_active_board()) == 0


def test_board_activate_already_active(test_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "activate", "1"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == "Board is already active.\n"


def test_board_activate_success(test_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        runner.invoke(
            cli,
            args=["board", "create", "'CLI Test'", "--icon", ":books:"],
            obj=test_app,
        )
        result = runner.invoke(cli, args=["board", "activate", "2"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == "Board with board_id = 2 is set as active board.\n"


def test_board_activate_no_board(empty_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "activate", "2"], obj=empty_app)
        assert result.exit_code == 0
        assert result.output == "No boards created yet.\n"


def test_board_activate_no_board_with_id(test_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "activate", "2"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == "There is no board with board_id = 2.\n"
