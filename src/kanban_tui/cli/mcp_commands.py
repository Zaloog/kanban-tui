import asyncio
import os
import signal
import sys
from importlib.metadata import PackageNotFoundError, version

import click

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends
from kanban_tui.scope import (
    SCOPE_USER,
    ScopeError,
    bind_user_scope_env,
    ensure_user_scope_dirs,
    resolve_user_scope,
)
from kanban_tui.utils import print_to_console, print_to_stderr


def _effective_scope(ctx: click.Context, scope: str | None) -> str | None:
    if scope:
        return scope
    if ctx.parent is not None:
        return ctx.parent.meta.get("scope")
    return None


def _bind_user_scope_for_server(ctx: click.Context):
    try:
        user_scope = resolve_user_scope()
        ensure_user_scope_dirs(user_scope)
        bind_user_scope_env(user_scope)
    except ScopeError as e:
        raise click.ClickException(str(e)) from e
    except OSError as e:
        raise click.ClickException(f"cannot write user-scope store: {e}") from e
    ctx.meta["user_scope"] = user_scope
    if ctx.parent is not None:
        ctx.parent.meta["user_scope"] = user_scope
        ctx.parent.meta["scope"] = SCOPE_USER
    return user_scope


def _open_user_scope_app(user_scope) -> KanbanTui:
    try:
        app = KanbanTui(
            config_path=user_scope.config_file.as_posix(),
            database_path=user_scope.database_file.as_posix(),
        )
    except Exception as e:
        raise click.ClickException(f"user-scope store is unreadable: {e}") from e

    if app.config.backend.mode != Backends.SQLITE:
        raise click.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `mcp` command.
            """
        )
    try:
        app.backend.get_boards()
    except Exception as e:
        raise click.ClickException(f"user-scope store is unreadable: {e}") from e
    return app


def _set_server_identity(mcp_server) -> None:
    try:
        pkg_version = version("kanban_tui")
    except PackageNotFoundError:
        pkg_version = None
    server = mcp_server.server
    server.name = "kanban-tui"
    if pkg_version is not None:
        server.version = pkg_version


def _install_shutdown_signals(shutdown_event: asyncio.Event | None = None) -> None:
    def signal_handler(sig, frame):
        if shutdown_event is not None:
            shutdown_event.set()
        os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sigbreak = getattr(signal, "SIGBREAK", None)
    if sigbreak is not None:
        signal.signal(sigbreak, signal_handler)


def run_mcp_stdio_server(mcp_server) -> int:
    """Foreground stdio MCP serve loop. Protocol on stdout; diagnostics on stderr."""
    from mcp.server.stdio import stdio_server

    # Use signal.signal, not loop.add_signal_handler. MCP stdio reads stdin on
    # the event-loop thread; asyncio signal wakeup never runs while that read
    # blocks. A real Python handler interrupts the read and exits.
    _install_shutdown_signals()

    async def run_stdio() -> int:
        _install_shutdown_signals()
        try:
            async with stdio_server() as (read_stream, write_stream):
                print_to_stderr("kanban-tui mcp server starting (scope=user)")
                _install_shutdown_signals()
                await mcp_server.server.run(
                    read_stream,
                    write_stream,
                    mcp_server.server.create_initialization_options(),
                )
            return 0
        except Exception as e:
            print_to_stderr(f"[red]MCP server error: {e}[/]")
            return 1

    try:
        return asyncio.run(run_stdio())
    except KeyboardInterrupt:
        return 0


@click.command()
@click.pass_context
@click.pass_obj
@click.option(
    "--start-server",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help=(
        "Start a long-running stdio MCP server for MCP clients. "
        "Binds to --scope user (per-user XDG config and data). "
        "Protocol frames go to stdout; human diagnostics go to stderr."
    ),
)
@click.option(
    "--scope",
    type=click.Choice([SCOPE_USER], case_sensitive=False),
    default=None,
    metavar="SCOPE",
    help=(
        "Store scope for this process. 'user' is the per-user XDG store. "
        "Defaults to user when --start-server is set."
    ),
)
def mcp(app: KanbanTui, ctx, start_server: bool, scope: str | None):
    """
    Starts the mcp server, exposes the CLI Interface Commands.

    --start-server runs a long-running stdio MCP process intended for MCP
    clients. User scope (--scope user) selects the per-user XDG store and
    does not fall back to a project or system board store.
    """
    try:
        from pycli_mcp import CommandMCPServer, CommandQuery
    except ImportError:
        print_to_console(
            "Please install [yellow]kanban-tui\\[mcp][/] to use kanban-tui as an mcp server."
        )
        if start_server:
            sys.exit(1)
        return

    if not start_server:
        if app is not None and app.config.backend.mode != Backends.SQLITE:
            raise click.exceptions.UsageError(
                f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `mcp` command.
            """
            )
        print_to_console(
            "To add [yellow]kanban-tui[/] as an mcp-server, e.g. for `claude`, run:"
        )
        print_to_console(
            "[blue]claude mcp add kanban-tui --transport stdio --scope user -- ktui --scope user mcp --start-server[/]"
        )
        return

    effective_scope = _effective_scope(ctx, scope) or SCOPE_USER
    if effective_scope != SCOPE_USER:
        raise click.UsageError(
            f"unsupported --scope {effective_scope!r}; only 'user' is implemented"
        )

    user_scope = _bind_user_scope_for_server(ctx)
    app = _open_user_scope_app(user_scope)
    ctx.obj = app

    query = CommandQuery(
        command=ctx.parent.command, name="ktui", include=r"task|board|column|category"
    )
    mcp_server = CommandMCPServer(commands=[query])
    _set_server_identity(mcp_server)

    sys.exit(run_mcp_stdio_server(mcp_server))
