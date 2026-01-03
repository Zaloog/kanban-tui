"""CLI commands for kanban-tui board management"""

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends


@click.group()
@click.pass_obj
def board(app: KanbanTui):
    """
    Commands to manage boards via the CLI
    """
    if app.config.backend.mode != Backends.SQLITE:
        Console().print(f"Currently using [blue]{app.config.backend.mode}[/] backend.")
        Console().print(
            "Please change the backend to [blue]jira[/] before using the [green]`auth`[/] command."
        )


@board.command("list")
@click.pass_obj
def list_boards(app: KanbanTui):
    """
    List all boards
    """
    boards = app.backend.get_boards()
    if boards:
        for board in boards:
            Console().print(board)
    else:
        Console().print("No boards created yet.")


@board.command("create")
@click.pass_obj
def create_board(app: KanbanTui):
    """
    Creates a new board
    """
    # TODO


@board.command("delete")
@click.pass_obj
def delete_board(app: KanbanTui):
    """
    Deletes a board
    """
    # TODO
