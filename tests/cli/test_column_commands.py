import pytest
from click.testing import CliRunner
from click.exceptions import UsageError

from kanban_tui.cli import cli
from kanban_tui.config import Backends

BOARD_OUTPUT = """--- Active Board ---
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


def test_column_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list"], obj=test_app)
        assert result.exit_code == 2
        assert pytest.raises(UsageError)


def test_board_list(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["board", "list"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == BOARD_OUTPUT
