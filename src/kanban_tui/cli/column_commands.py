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
        Console().print(f"Currently using [blue]{app.config.backend.mode}[/] backend.")
        Console().print(
            "Please change the backend to [blue]jira[/] before using the [green]`auth`[/] command."
        )


@column.command("list")
@click.pass_obj
def list_columns(app: KanbanTui):
    """
    List all columns on active board
    """
    tasks = app.backend.get_columns()
    if tasks:
        for task in tasks:
            Console().print(task)
    else:
        Console().print("No tasks created yet.")


@column.command("create")
@click.pass_obj
def create_column(app: KanbanTui):
    """
    Creates a new column
    """
    # TODO


@column.command("delete")
@click.pass_obj
def delete_column(app: KanbanTui):
    """
    Deletes a column
    """
    # TODO
