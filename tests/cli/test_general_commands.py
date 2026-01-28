from kanban_tui.config import Backends
from pathlib import Path

from click.testing import CliRunner

from kanban_tui.cli import cli

CLEAR_OUTPUT = """Are you sure you want to delete the db and config? [y/N]: y
Config under TEST_CONFIG_PATH deleted successfully.
Database under TEST_DB_PATH deleted successfully.
"""


def test_info():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["info"])
        assert result.exit_code == 0
        assert "xdg file and skill locations" in result.output


def test_auth_wrong_backend(test_app, test_database_path):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["auth"], obj=test_app)
        assert result.exit_code == 2
        assert (
            f"Currently using `{test_app.config.backend.mode}` backend."
            in result.output
        )
        assert (
            f"Please change the backend to `{Backends.JIRA}` before using the `auth` command."
            in result.output
        )


def test_clear_abort(test_app, test_database_path):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["clear"], input="n", obj=test_app)
        assert result.exit_code == 0
        assert Path(test_database_path).exists()


def test_clear_success(test_app, test_config_path, test_database_path):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["clear"], input="y", obj=test_app)
        assert result.exit_code == 0
        output = result.output.replace(test_config_path, "TEST_CONFIG_PATH").replace(
            test_database_path, "TEST_DB_PATH"
        )
        assert output == CLEAR_OUTPUT
        assert not Path(test_config_path).exists()
        assert not Path(test_database_path).exists()
