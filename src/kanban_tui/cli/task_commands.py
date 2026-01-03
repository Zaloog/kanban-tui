"""CLI commands for kanban-tui task management"""

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends


@click.group()
@click.pass_obj
def task(app: KanbanTui):
    """
    Commands to manage boards via the CLI
    """
    if app.config.backend.mode != Backends.SQLITE:
        Console().print(f"Currently using [blue]{app.config.backend.mode}[/] backend.")
        Console().print(
            "Please change the backend to [blue]jira[/] before using the [green]`auth`[/] command."
        )


@task.command("list")
@click.pass_obj
def list_boards(app: KanbanTui):
    """
    List all tasks on active board
    """
    tasks = app.backend.get_tasks_on_active_board()
    if tasks:
        for task in tasks:
            Console().print(task)
    else:
        Console().print("No tasks created yet.")


@task.command("create")
@click.pass_obj
def create_task(app: KanbanTui):
    """
    Creates a new task
    """
    # TODO


@task.command("delete")
@click.pass_obj
def delete_task(app: KanbanTui):
    """
    Deletes a task
    """
    # TODO
