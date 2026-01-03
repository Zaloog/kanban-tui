"""CLI entry-point for kanban-tui"""

from kanban_tui.cli.column_commands import column
from kanban_tui.cli.task_commands import task

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.cli.board_commands import board
from kanban_tui.cli.demo_commands import demo
from kanban_tui.cli.util_commands import info, clear, auth
from kanban_tui.constants import (
    CONFIG_FILE,
    DATABASE_FILE,
)


@click.group(
    context_settings={"ignore_unknown_options": True}, invoke_without_command=True
)
@click.version_option(prog_name="kanban-tui")
@click.option("--web", is_flag=True, default=False, help="Host app locally")
@click.pass_context
def cli(ctx, web: bool):
    if web:
        try:
            from textual_serve.server import Server
        except ModuleNotFoundError:
            Console().print("[yellow]textual-serve[/] dependency not found.")
            Console().print(
                "Please install [yellow]kanban-tui\\[web][/] to add web support."
            )
            return

        command = "ktui"
        server = Server(command)
        server.serve()
    else:
        if ctx.invoked_subcommand is None:
            app = KanbanTui(
                config_path=CONFIG_FILE.as_posix(),
                database_path=DATABASE_FILE.as_posix(),
            )
            app.run()
        elif ctx.invoked_subcommand == "demo":
            print("demo")
        else:
            app = KanbanTui(
                config_path=CONFIG_FILE.as_posix(),
                database_path=DATABASE_FILE.as_posix(),
            )
            ctx.obj = app


cli.add_command(demo)
cli.add_command(auth)
cli.add_command(info)
cli.add_command(clear)
cli.add_command(board)
cli.add_command(task)
cli.add_command(column)


if __name__ == "__main__":
    cli()
