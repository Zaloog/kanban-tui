import asyncio
import signal
import sys

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
        command=ctx.parent.command, name="ktui", include=r"task|board|column|category"
    )
    mcp_server = CommandMCPServer(commands=[query])

    # Create a shutdown event for graceful cleanup
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully"""
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    async def run_stdio():
        try:
            async with stdio_server() as (read_stream, write_stream):
                server_task = asyncio.create_task(
                    mcp_server.server.run(
                        read_stream,
                        write_stream,
                        mcp_server.server.create_initialization_options(),
                    )
                )

                shutdown_task = asyncio.create_task(shutdown_event.wait())

                # Wait for either the server to complete or shutdown signal
                done, pending = await asyncio.wait(
                    {server_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel any pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            print_to_console(f"[red]MCP server error: {e}[/]")
            sys.exit(1)
        finally:
            pass

    try:
        asyncio.run(run_stdio())
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit(0)
