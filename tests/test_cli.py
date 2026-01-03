from click.testing import CliRunner

from kanban_tui.cli import cli

board_output = """Board(
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
