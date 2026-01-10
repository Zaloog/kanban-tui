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
    boards = app.backend.get_boards()
    if not boards:
        Console().print("No boards created yet.")
        return

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
    type=click.DateTime(formats=["%Y-%m-%d"]),
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
@click.option(
    "--title",
    default=None,
    type=click.STRING,
    help="The task title",
)
@click.option(
    "--description",
    default=None,
    type=click.STRING,
    help="The task description",
)
@click.option(
    "--due-date",
    default=None,
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Task due date (format `%Y-%m-%d`)",
)
def update_task(
    app: KanbanTui,
    task_id: int,
    title: str | None,
    description: str | None,
    due_date: datetime.datetime | None,
):
    """
    Updates a task
    """
    old_task = app.backend.get_task_by_id(task_id=task_id)
    if all((title is None, description is None, due_date is None)):
        Console().print("No fields to update provided.")
    else:
        _updated_task = app.backend.update_task_entry(
            task_id=task_id,
            title=title or old_task.title,
            description=description or old_task.description,
            category=None,
            due_date=due_date or old_task.due_date,
        )
        Console().print(f"Updated task with {task_id = }.")


@task.command("move")
@click.pass_obj
@click.argument("task_id", type=click.INT)
@click.argument("target_column", type=click.INT)
def move_task(app: KanbanTui, task_id: int, target_column: int):
    """
    Moves a task to another column
    """
    task = app.backend.get_task_by_id(task_id=task_id)
    new_column = app.backend.get_column_by_id(column_id=target_column)
    if not task:
        Console().print(f"[red]There is no task with {task_id = }.[/]")
    elif not new_column:
        Console().print(f"[red]There is no column with column_id = {target_column}.[/]")
    elif task.column == target_column:
        Console().print(
            f"[yellow]Task with {task_id = } is already in column {target_column}.[/]"
        )
    else:
        # Validate if task/column are on active board and ask for further confirmation if not
        active_board = app.backend.active_board
        old_column = app.backend.get_column_by_id(column_id=task.column)
        if active_board.board_id != old_column.board_id:
            click.confirm(
                "Task is not on the active board, still continue?", abort=True
            )
        if active_board.board_id != new_column.board_id:
            click.confirm(
                "Target column is not on the active board, still continue?", abort=True
            )
        task.column = target_column
        moved_task = app.backend.update_task_status(new_task=task)
        Console().print(
            f"Moved task with {task_id = } from column {old_column.column_id} to {moved_task.column}."
        )


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
    task = app.backend.get_task_by_id(task_id=task_id)

    if task:
        if not no_confirm:
            click.confirm(
                f"Do you want to delete the task with {task_id = } ", abort=True
            )
        app.backend.delete_task(task_id)
        Console().print(f"Deleted task with {task_id = }.")

    else:
        Console().print(f"[red]There is no task with {task_id = }[/].")
