import pytest
from click.testing import CliRunner

from kanban_tui.cli import cli


def test_info():
    runner = CliRunner()
    result = runner.invoke(cli, args=["info"])
    assert result.exit_code == 0
    assert "xdg file locations" in result.output


def test_clear():
    runner = CliRunner()
    result = runner.invoke(cli, args=["clear"], input="n")
    assert result.exit_code == 0


@pytest.mark.skip
def test_task_list(test_app):
    runner = CliRunner()
    result = runner.invoke(cli, args=["task", "list"])
    assert result.exit_code == 0
