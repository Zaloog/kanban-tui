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


@pytest.mark.skip
def test_task_list(test_app):
    runner = CliRunner()
    result = runner.invoke(cli, args=["task", "list"])
    assert result.exit_code == 0
    assert board_output == result.output
