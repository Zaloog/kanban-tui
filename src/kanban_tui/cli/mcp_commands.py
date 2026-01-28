import asyncio

import click

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends
from kanban_tui.utils import print_to_console


@click.command()
@click.pass_context
@click.pass_obj
@click.option(
    "--start-server",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Starts the actual mcp server",
)
def mcp(app: KanbanTui, ctx, start_server: bool):
    """
    Starts the mcp server that exposes task/board/column commands
    """
    try:
        from mcp.server.stdio import stdio_server
        from pycli_mcp import CommandQuery, CommandMCPServer
    except ImportError:
        print_to_console(
            "Please install [yellow]kanban-tui\\[mcp][/] to use kanban-tui as an mcp server."
        )
        return

    if app.config.backend.mode != Backends.SQLITE:
        raise click.exceptions.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `mcp` command.
            """
        )
    if not start_server:
        print_to_console(
            "To add [yellow]kanban-tui[/] as an mcp-server, e.g. for `claude`, run:"
        )
        print_to_console(
            "[blue]claude mcp add kanban-tui --transport stdio --scope user -- ktui mcp --start-server[/]"
        )
        return

    query = CommandQuery(
        command=ctx.parent.command, name="ktui", include=r"task|board|column"
    )
    mcp_server = CommandMCPServer(commands=[query])

    async def run_stdio():
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.server.run(
                read_stream,
                write_stream,
                mcp_server.server.create_initialization_options(),
            )

    asyncio.run(run_stdio())
