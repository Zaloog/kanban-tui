from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.config import Backends

COLUMN_OUTPUT = """Column(column_id=1, name='Ready', visible=True, position=1, board_id=1)
Column(column_id=2, name='Doing', visible=True, position=2, board_id=1)
Column(column_id=3, name='Done', visible=True, position=3, board_id=1)
Column(column_id=4, name='Archive', visible=False, position=4, board_id=1)
"""

COLUMN_OUTPUT_JSON = """[
    {
        "column_id": 1,
        "name": "Ready",
        "visible": true,
        "position": 1,
        "board_id": 1
    },
    {
        "column_id": 2,
        "name": "Doing",
        "visible": true,
        "position": 2,
        "board_id": 1
    },
    {
        "column_id": 3,
        "name": "Done",
        "visible": true,
        "position": 3,
        "board_id": 1
    },
    {
        "column_id": 4,
        "name": "Archive",
        "visible": false,
        "position": 4,
        "board_id": 1
    }
]
"""


def test_column_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list"], obj=test_app)
        assert result.exit_code == 2
        assert (
            f"Currently using `{test_app.config.backend.mode}` backend."
            in result.output
        )
        assert (
            f"Please change the backend to `{Backends.SQLITE}` before using the `column` command."
            in result.output
        )


def test_column_list(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == COLUMN_OUTPUT


def test_column_list_json(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list", "--json"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == COLUMN_OUTPUT_JSON


def test_column_list_no_board(empty_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["column", "list"], obj=empty_app)
        assert result.exit_code == 0
        assert result.output == "No boards created yet.\n"


def test_column_list_filter_no_board(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, args=["column", "list", "--board", "2"], obj=test_app
        )
        assert result.exit_code == 0
        assert result.output == "There is no board with board_id = 2.\n"
