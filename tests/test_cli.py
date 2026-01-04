import pytest
from click.testing import CliRunner

from kanban_tui.cli import cli

board_output = """--- Active Board ---
Board(
    board_id=1,
    name='Kanban Board',
    icon=':sparkles:',
    creation_date=datetime.datetime(2026, 4, 2, 13, 3, 7),
    reset_column=None,
    start_column=None,
    finish_column=None
)
"""


def test_info():
    runner = CliRunner()
    result = runner.invoke(cli, args=["info"])
    assert result.exit_code == 0
    assert "xdg file locations" in result.output


def test_clear():
    runner = CliRunner()
    result = runner.invoke(cli, args=["clear"], input="n")
    assert result.exit_code == 0


def test_board_list(test_app):
    runner = CliRunner()
    result = runner.invoke(cli, args=["board", "list"])
    assert result.exit_code == 0
    assert board_output == result.output


def test_board_create(test_app):
    runner = CliRunner()
    result = runner.invoke(
        cli, args=["board", "create", "'CLI Test'", "--icon", ":books:"]
    )
    assert result.exit_code == 0
    assert result.output == "Created board 'CLI Test' with board_id: 2.\n"
    assert len(test_app.backend.get_boards()) == 2


def test_board_delete_fail_active_board(test_app):
    runner = CliRunner()
    # Attempting to delete the active board is not allowed
    result = runner.invoke(
        cli,
        args=[
            "board",
            "delete",
            "1",
        ],
        input="y",
    )
    assert result.exit_code == 0
    assert result.output == "Active board can not be deleted.\n"


def test_board_delete_fail_wrong_id(test_app):
    runner = CliRunner()
    # Attempting to delete the active board is not allowed
    result = runner.invoke(
        cli,
        args=[
            "board",
            "delete",
            "12",
        ],
        input="y",
    )
    assert result.exit_code == 0
    assert result.output == "There is no board with board_id=12.\n"


def test_board_delete_success(test_app):
    runner = CliRunner()
    # create board first
    runner.invoke(cli, args=["board", "create", "'CLI Test'", "--icon", ":books:"])
    result = runner.invoke(cli, args=["board", "delete", "2"], input="y")
    assert result.exit_code == 0
    assert (
        result.output
        == "Do you want to delete the board with board_id=2  [y/N]: y\nDeleted board 'CLI Test' with board_id: 2.\n"
    )
    assert len(test_app.backend.get_boards()) == 1


def test_board_delete_abort(test_app):
    runner = CliRunner()
    # create board first
    runner.invoke(cli, args=["board", "create", "'CLI Test'", "--icon", ":books:"])
    result = runner.invoke(cli, args=["board", "delete", "2"], input="n")
    assert result.exit_code == 1
    assert (
        result.output
        == "Do you want to delete the board with board_id=2  [y/N]: n\nAborted!\n"
    )
    assert len(test_app.backend.get_boards()) == 1


def test_board_delete_success_no_confirm(test_app):
    runner = CliRunner()
    # create board first
    runner.invoke(cli, args=["board", "create", "'CLI Test'", "--icon", ":books:"])
    result = runner.invoke(
        cli,
        args=["board", "delete", "2", "--no-confirm"],
    )
    assert result.exit_code == 0
    assert result.output == "Deleted board 'CLI Test' with board_id: 2.\n"
    assert len(test_app.backend.get_boards()) == 1


@pytest.mark.skip
def test_task_list(test_app):
    runner = CliRunner()
    result = runner.invoke(cli, args=["task", "list"])
    assert result.exit_code == 0
    assert board_output == result.output
