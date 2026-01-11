import pytest
from click.testing import CliRunner
from click.exceptions import UsageError

from kanban_tui.cli import cli
from kanban_tui.config import Backends

BOARD_OUTPUT = """Column(column_id=1, name='Ready', visible=True, position=1, board_id=1)
Column(column_id=2, name='Doing', visible=True, position=2, board_id=1)
Column(column_id=3, name='Done', visible=True, position=3, board_id=1)
Column(column_id=4, name='Archive', visible=False, position=4, board_id=1)
"""


def test_column_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list"], obj=test_app)
        assert result.exit_code == 2
        assert pytest.raises(UsageError)


def test_column_list(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == BOARD_OUTPUT


def test_column_list_no_board(empty_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list"], obj=empty_app)
        assert result.exit_code == 0
        assert result.output == "No boards created yet.\n"
