"""CLI commands for kanban-tui column management"""

import click
from pydantic import TypeAdapter
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.classes.column import Column
from kanban_tui.config import Backends


@click.group()
@click.pass_obj
def column(app: KanbanTui):
    """
    Commands to manage columns via the CLI
    """
    if app.config.backend.mode != Backends.SQLITE:
        raise click.exceptions.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `column` command.
            """
        )


@column.command("list")
@click.pass_obj
@click.option(
    "--json",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="use JSON format",
)
def list_columns(app: KanbanTui, json: bool):
    """
    List all columns on active board
    """
    boards = app.backend.get_boards()
    if not boards:
        Console().print("No boards created yet.")
        return

    columns = app.backend.get_columns()
    if json:
        column_list = TypeAdapter(list[Column])
        json_str = column_list.dump_json(columns, indent=4, exclude_none=True).decode(
            "utf-8"
        )
        Console().print(json_str)
    else:
        for column in columns:
            Console().print(column)
