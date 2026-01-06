"""CLI commands for kanban-tui task management"""

import datetime

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
        raise click.exceptions.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `task` command.
            """
        )


@task.command("list")
@click.pass_obj
def list_tasks(app: KanbanTui):
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
@click.argument("title", type=click.STRING)
@click.option(
    "--description",
    type=click.STRING,
    help="The task description",
)
@click.option(
    "--column",
    default=None,
    type=click.INT,
    help="Column to put the task into [default: left most visible column]",
)
@click.option(
    "--due-date",
    default=None,
    type=click.DateTime(),
    help="Task due date (format `%Y-%m-%d`)",
)
def create_task(
    app: KanbanTui,
    title: str,
    description: str,
    column: int,
    due_date: datetime.datetime,
):
    """
    Creates a new task
    """
    first_visible_column = next(
        column for column in app.backend.get_columns() if column.visible
    ).column_id
    new_task = app.backend.create_new_task(
        title=title,
        description=description,
        column=column or first_visible_column,
        due_date=due_date,
    )
    task_id = new_task.task_id
    Console().print(f"Created task `{title}` with {task_id = }.")


@task.command("update")
@click.pass_obj
@click.argument("task_id", type=click.INT)
def update_task(app: KanbanTui):
    """
    Updates a task
    """
    # TODO


@task.command("delete")
@click.pass_obj
@click.argument("task_id", type=click.INT)
@click.option(
    "--no-confirm",
    default=False,
    is_flag=True,
    type=click.BOOL,
    help="Dont ask for confirmation to delete",
)
def delete_task(app: KanbanTui, task_id: int, no_confirm: bool):
    """
    Deletes a task
    """
    tasks = app.backend.get_tasks_on_active_board()

    if not tasks:
        Console().print("[red]No tasks created yet.[/]")
    elif task_id in [task.task_id for task in tasks]:
        if not no_confirm:
            click.confirm(
                f"Do you want to delete the task with {task_id = } ", abort=True
            )
        app.backend.delete_task(task_id)
        Console().print(f"Deleted task with {task_id = }.")

    else:
        Console().print(f"[red]There is no task with {task_id = }[/].")
    # TODO
