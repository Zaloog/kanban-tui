import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from kanban_tui.cli import cli
from kanban_tui.config import Backends

MCP_ADD_OUTPUT = (
    "To add kanban-tui as an mcp-server, e.g. for `claude`, run:\n"
    "claude mcp add kanban-tui --transport stdio --scope user -- "
    "ktui --scope user mcp --start-server\n"
)


def _user_env(home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["XDG_DATA_HOME"] = str(home / ".local" / "share")
    env.pop("KANBAN_TUI_CONFIG_FILE", None)
    env.pop("KANBAN_TUI_DATABASE_FILE", None)
    env["PATH"] = f"{Path(sys.executable).parent}{os.pathsep}{env.get('PATH', '')}"
    return env


def _point_home(monkeypatch, home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))
    monkeypatch.delenv("KANBAN_TUI_CONFIG_FILE", raising=False)
    monkeypatch.delenv("KANBAN_TUI_DATABASE_FILE", raising=False)


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


def test_mcp_start_server_missing_dependency(tmp_path, monkeypatch):
    _point_home(monkeypatch, tmp_path / "home")
    monkeypatch.setitem(sys.modules, "mcp", None)
    monkeypatch.setitem(sys.modules, "mcp.server", None)
    monkeypatch.setitem(sys.modules, "mcp.server.stdio", None)
    monkeypatch.setitem(sys.modules, "pycli_mcp", None)

    runner = CliRunner()
    result = runner.invoke(cli, args=["--scope", "user", "mcp", "--start-server"])
    assert result.exit_code == 1
    assert "Please install kanban-tui[mcp]" in result.output


def test_mcp_success(test_app):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, args=["mcp"], obj=test_app)
        assert result.exit_code == 0
        assert result.output == MCP_ADD_OUTPUT


def test_scope_project_is_usage_error():
    runner = CliRunner()
    result = runner.invoke(cli, args=["--scope", "project", "mcp", "--start-server"])
    assert result.exit_code == 2
    assert "Invalid value" in result.output


def test_mcp_help_documents_start_server_and_scope():
    runner = CliRunner()
    result = runner.invoke(cli, args=["mcp", "--help"])
    assert result.exit_code == 0
    assert "--start-server" in result.output
    assert "long-running" in result.output
    assert "--scope" in result.output
    assert "user" in result.output


def test_global_help_documents_scope():
    runner = CliRunner()
    result = runner.invoke(cli, args=["--help"])
    assert result.exit_code == 0
    assert "--scope" in result.output
    assert "XDG" in result.output


def test_start_server_empty_user_store(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _point_home(monkeypatch, home)
    monkeypatch.setattr(
        "kanban_tui.cli.mcp_commands.run_mcp_stdio_server", lambda server: 0
    )

    runner = CliRunner()
    result = runner.invoke(cli, args=["--scope", "user", "mcp", "--start-server"])

    assert result.exit_code == 0
    assert "claude mcp add" not in result.output
    db = home / ".local" / "share" / "kanban_tui" / "kanban_tui.db"
    assert db.exists()


def test_start_server_ignores_cwd_project_store(tmp_path, monkeypatch):
    home = tmp_path / "home"
    project = tmp_path / "project"
    project.mkdir()
    project_db = project / "kanban_tui.db"
    project_db.write_bytes(b"project-store")
    _point_home(monkeypatch, home)
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        "kanban_tui.cli.mcp_commands.run_mcp_stdio_server", lambda server: 0
    )

    runner = CliRunner()
    result = runner.invoke(cli, args=["mcp", "--scope", "user", "--start-server"])

    assert result.exit_code == 0
    assert project_db.read_bytes() == b"project-store"
    user_db = home / ".local" / "share" / "kanban_tui" / "kanban_tui.db"
    assert user_db.exists()
    assert user_db.resolve() != project_db.resolve()


def test_start_server_unresolved_home(monkeypatch):
    def no_home():
        raise RuntimeError("HOME is not set")

    monkeypatch.setattr("kanban_tui.scope.Path.home", staticmethod(no_home))
    monkeypatch.setattr(
        "kanban_tui.cli.mcp_commands.run_mcp_stdio_server",
        lambda server: pytest.fail("server must not start"),
    )

    runner = CliRunner()
    result = runner.invoke(cli, args=["--scope", "user", "mcp", "--start-server"])
    assert result.exit_code == 1
    assert "user scope cannot be resolved" in result.output
    assert "home directory is not set" in result.output


def test_start_server_corrupt_store(tmp_path, monkeypatch):
    home = tmp_path / "home"
    _point_home(monkeypatch, home)
    data_dir = home / ".local" / "share" / "kanban_tui"
    data_dir.mkdir(parents=True)
    (data_dir / "kanban_tui.db").write_text("not a sqlite database")
    monkeypatch.setattr(
        "kanban_tui.cli.mcp_commands.run_mcp_stdio_server",
        lambda server: pytest.fail("server must not start"),
    )

    runner = CliRunner()
    result = runner.invoke(cli, args=["--scope", "user", "mcp", "--start-server"])
    assert result.exit_code == 1
    assert "user-scope store is unreadable" in result.output


def test_command_query_exposes_board_commands():
    pycli_mcp = pytest.importorskip("pycli_mcp")
    query = pycli_mcp.CommandQuery(
        command=cli, name="ktui", include=r"task|board|column|category"
    )
    server = pycli_mcp.CommandMCPServer(commands=[query])
    assert "ktui" in server.commands
    description = server.commands["ktui"].tool.description or ""
    assert "board list" in description


def _ktui_cmd() -> list[str]:
    return [str(Path(sys.executable).parent / "ktui")]


async def test_mcp_initialize_empty_store_and_board_list(tmp_path):
    pytest.importorskip("mcp")
    pytest.importorskip("pycli_mcp")
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    home = tmp_path / "home"
    home.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    (cwd / "kanban_tui.db").write_bytes(b"project-store")
    errlog_path = tmp_path / "mcp-stderr.log"

    params = StdioServerParameters(
        command=_ktui_cmd()[0],
        args=["--scope", "user", "mcp", "--start-server"],
        env=_user_env(home),
        cwd=str(cwd),
    )

    with errlog_path.open("w", encoding="utf-8") as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                assert init.serverInfo.name == "kanban-tui"
                tools = await session.list_tools()
                names = [tool.name for tool in tools.tools]
                assert "ktui" in names
                result = await session.call_tool(
                    "ktui", {"args": ["board", "list", "--json"]}
                )
                text = "".join(
                    block.text for block in result.content if hasattr(block, "text")
                )
                assert "No boards created yet." in text

    assert (cwd / "kanban_tui.db").read_bytes() == b"project-store"
    assert (home / ".local" / "share" / "kanban_tui" / "kanban_tui.db").exists()
    assert "scope=user" in errlog_path.read_text(encoding="utf-8")


def test_mcp_shutdown_on_stdin_eof(tmp_path):
    pytest.importorskip("mcp")
    pytest.importorskip("pycli_mcp")
    home = tmp_path / "home"
    home.mkdir()
    proc = subprocess.Popen(
        [*_ktui_cmd(), "--scope", "user", "mcp", "--start-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_user_env(home),
        cwd=str(tmp_path),
    )
    assert proc.stdin is not None
    proc.stdin.close()
    code = proc.wait(timeout=15)
    stderr = proc.stderr.read().decode() if proc.stderr else ""
    stdout = proc.stdout.read() if proc.stdout else b""
    assert code == 0, stderr
    assert b"kanban-tui mcp server starting" not in stdout
    assert "scope=user" in stderr
    db = home / ".local" / "share" / "kanban_tui" / "kanban_tui.db"
    assert db.exists()
    import sqlite3

    sqlite3.connect(db).execute("SELECT name FROM sqlite_master").fetchall()


def test_mcp_shutdown_on_sigterm(tmp_path):
    pytest.importorskip("mcp")
    pytest.importorskip("pycli_mcp")
    home = tmp_path / "home"
    home.mkdir()
    proc = subprocess.Popen(
        [*_ktui_cmd(), "--scope", "user", "mcp", "--start-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_user_env(home),
        cwd=str(tmp_path),
    )
    try:
        assert proc.stderr is not None
        while True:
            line = proc.stderr.readline()
            if not line:
                raise AssertionError("server exited before becoming ready")
            if b"scope=user" in line:
                break
        proc.send_signal(signal.SIGTERM)
        assert proc.wait(timeout=15) == 0
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
