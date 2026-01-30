"""CLI entry-point for kanban-tui"""

import sys

import os
from collections import OrderedDict

from kanban_tui.cli.column_commands import column
from kanban_tui.cli.task_commands import task
from kanban_tui.cli.category_commands import category

import click

from kanban_tui.app import KanbanTui
from kanban_tui.cli.board_commands import board
from kanban_tui.cli.demo_commands import demo
from kanban_tui.cli.skills_commands import skill
from kanban_tui.cli.mcp_commands import mcp
from kanban_tui.cli.general_commands import info, clear, auth
from kanban_tui.utils import print_to_console
from kanban_tui.constants import (
    CONFIG_FILE,
    DATABASE_FILE,
    DEMO_CONFIG_FILE,
    DEMO_DATABASE_FILE,
)

COMMAND_DICT = {
    "General Commands": [
        "demo",
        "info",
        "clear",
        "skill",
        "mcp",
    ],
    "CLI Interface Commands": [
        "board",
        "category",
        "column",
        "task",
    ],
    # "Not yet implemented": [
    #     "auth",
    # ],
}


# Enables Custom Help Interface
class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands

    def format_commands(self, ctx, formatter):
        super().get_usage(ctx)

        HELP_LIMIT_LEN = 120
        formatter.write_paragraph()
        for section, commands in COMMAND_DICT.items():
            with formatter.section(section):
                for command in commands:
                    formatter.write_text(
                        f"{self.commands[command].name}\t\t"
                        f"{self.commands[command].get_short_help_str(HELP_LIMIT_LEN)}"
                    )


@click.group(
    cls=OrderedGroup,
    context_settings={
        "ignore_unknown_options": True,
        "help_option_names": ["-h", "--help"],
    },
    invoke_without_command=True,
)
@click.version_option(prog_name="kanban-tui")
@click.option("--web", is_flag=True, default=False, help="Host app locally")
@click.pass_context
def cli(ctx: click.Context, web: bool):
    """Running without any commands starts the TUI and should never be used by agents"""
    if web:
        try:
            from textual_serve.server import Server
        except ModuleNotFoundError:
            print_to_console("[yellow]textual-serve[/] dependency not found.")
            print_to_console(
                "Please install [yellow]kanban-tui\\[web][/] to add web support."
            )
            sys.exit(1)

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
            os.environ["KANBAN_TUI_CONFIG_FILE"] = DEMO_CONFIG_FILE.as_posix()
            app = KanbanTui(
                config_path=DEMO_CONFIG_FILE.as_posix(),
                database_path=DEMO_DATABASE_FILE.as_posix(),
                demo_mode=True,
            )
            ctx.obj = app
        elif ctx.invoked_subcommand in ["info", "clear"]:
            pass
        else:
            app = KanbanTui(
                config_path=os.getenv("KANBAN_TUI_CONFIG_FILE", CONFIG_FILE.as_posix()),
                database_path=os.getenv(
                    "KANBAN_TUI_DATABASE_FILE", DATABASE_FILE.as_posix()
                ),
            )
            ctx.obj = app


cli.add_command(demo)
cli.add_command(info)
cli.add_command(clear)
cli.add_command(board)
cli.add_command(category)
cli.add_command(task)
cli.add_command(column)
cli.add_command(auth)
cli.add_command(skill)
cli.add_command(mcp)


if __name__ == "__main__":
    cli()
