import sys

from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.config import Backends


def test_mcp_wrong_backend(test_app, test_jira_config):
    test_app.config.backend.mode = Backends.JIRA
    test_app.backend = test_app.get_backend()

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["mcp"], obj=test_app)
        assert result.exit_code == 2
        assert (
            f"Currently using `{test_app.config.backend.mode}` backend."
            in result.output
        )
        assert (
            f"Please change the backend to `{Backends.SQLITE}` before using the `mcp` command."
            in result.output
        )


def test_mcp_missing_dependency(test_app, monkeypatch):
    monkeypatch.setitem(sys.modules, "mcp", None)
    monkeypatch.setitem(sys.modules, "mcp.server", None)
    monkeypatch.setitem(sys.modules, "mcp.server.stdio", None)
    monkeypatch.setitem(sys.modules, "pycli_mcp", None)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["mcp"], obj=test_app)
        assert result.exit_code == 0
        assert (
            result.output
            == "Please install kanban-tui[mcp] to use kanban-tui as an mcp server.\n"
        )


def test_mcp_success(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["mcp"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == (
            "To add kanban-tui as an mcp-server, e.g. for `claude`, run:\n"
            "claude mcp add kanban-tui --transport stdio --scope user -- ktui mcp --start-server\n"
        )
