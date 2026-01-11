"""CLI commands for kanban-tui column management"""

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
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
def list_columns(app: KanbanTui):
    """
    List all columns on active board
    """
    boards = app.backend.get_boards()
    if not boards:
        Console().print("No boards created yet.")
        return

    columns = app.backend.get_columns()
    for column in columns:
        Console().print(column)
