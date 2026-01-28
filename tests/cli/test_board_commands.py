from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.config import Backends

BOARD_OUTPUT = """--- Active Board has board_id = 1 ---
Board(
    board_id=1,
    name='Kanban Board',
    icon=':sparkles:',
    creation_date=datetime.datetime(2026, 4, 2, 13, 3, 7),
    reset_column=1,
    start_column=2,
    finish_column=3
)
"""

BOARD_OUTPUT_JSON = """--- Active Board has board_id = 1 ---
[
    {
        "board_id": 1,
        "name": "Kanban Board",
        "icon": "✨",
        "creation_date": "2026-04-02T13:03:07",
        "reset_column": 1,
        "start_column": 2,
        "finish_column": 3
    }
]
"""


def test_board_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "list"], obj=test_app)
        assert result.exit_code == 2
        assert (
            f"Currently using `{test_app.config.backend.mode}` backend."
            in result.output
        )
        assert (
            f"Please change the backend to `{Backends.SQLITE}` before using the `board` command."
            in result.output
        )


def test_board_list(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "list"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == BOARD_OUTPUT


def test_board_list_json(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "list", "--json"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == BOARD_OUTPUT_JSON


def test_board_list_no_boards(empty_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "list"], obj=empty_app)
        assert result.exit_code == 0
        assert result.output == "No boards created yet.\n"


def test_board_create(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=["board", "create", "CLI Test", "--icon", ":books:"],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Created board `CLI Test` with board_id = 2.\n"
        assert len(test_app.backend.get_boards()) == 2


def test_board_create_custom_columns(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "board",
                "create",
                "CLI Test",
                "--icon",
                ":books:",
                "-c",
                "TestCol1",
                "-c",
                "TestCol2",
            ],
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Created board `CLI Test` with board_id = 2.\n"
        assert len(test_app.backend.get_boards()) == 2
        assert test_app.backend.get_column_by_id(5).name == "TestCol1"
        assert test_app.backend.get_column_by_id(6).name == "TestCol2"


def test_board_delete_fail_active_board(test_app):
    runner = CliRunner()
    # Attempting to delete the active board is not allowed
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "board",
                "delete",
                "1",
            ],
            input="y",
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "Active board can not be deleted.\n"


def test_board_delete_fail_wrong_id(test_app):
    runner = CliRunner()
    # Attempting to delete the active board is not allowed
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            args=[
                "board",
                "delete",
                "12",
            ],
            input="y",
            obj=test_app,
        )
        assert result.exit_code == 0
        assert result.output == "There is no board with board_id = 12.\n"


def test_board_delete_success(test_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        runner.invoke(
            cli,
            args=["board", "create", "CLI Test", "--icon", ":books:"],
            obj=test_app,
        )
        result = runner.invoke(
            cli, args=["board", "delete", "2"], input="y", obj=test_app
        )
        assert result.exit_code == 0
        assert (
            result.output
            == "Do you want to delete the board with board_id = 2? [y/N]: y\nDeleted board with board_id = 2.\n"
        )
        assert len(test_app.backend.get_boards()) == 1


def test_board_delete_abort(test_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        runner.invoke(
            cli,
            args=["board", "create", "'CLI Test'", "--icon", ":books:"],
            obj=test_app,
        )
        result = runner.invoke(
            cli, args=["board", "delete", "2"], input="n", obj=test_app
        )
        assert result.exit_code == 1
        assert (
            result.output
            == "Do you want to delete the board with board_id = 2? [y/N]: n\nAborted!\n"
        )
        assert len(test_app.backend.get_boards()) == 2


def test_board_delete_success_no_confirm(test_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        runner.invoke(
            cli,
            args=["board", "create", "'CLI Test'", "--icon", ":books:"],
            obj=test_app,
        )
        result = runner.invoke(
            cli, args=["board", "delete", "2", "--no-confirm"], obj=test_app
        )
        assert result.exit_code == 0
        assert result.output == "Deleted board with board_id = 2.\n"
        assert len(test_app.backend.get_boards()) == 1


def test_board_delete_fail_no_boards(empty_app):
    runner = CliRunner()
    # create board first
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, args=["board", "delete", "2", "--no-confirm"], obj=empty_app
        )
        assert result.exit_code == 0
        assert result.output == "No boards created yet.\n"
        assert len(empty_app.backend.get_boards()) == 0


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
