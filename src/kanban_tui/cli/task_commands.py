"""CLI commands for kanban-tui task management"""

from pydantic import TypeAdapter

import datetime

import click

from kanban_tui.app import KanbanTui
from kanban_tui.classes.task import Task
from kanban_tui.config import Backends
from kanban_tui.utils import print_to_console


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
@click.option(
    "--json",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Use JSON format",
)
@click.option(
    "--column",
    default=None,
    type=click.INT,
    help="Show only tasks in this column",
)
@click.option(
    "--board",
    default=None,
    type=click.INT,
    help="Show only tasks on this board",
)
@click.option(
    "--actionable",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Show only actionable tasks (not blocked by unfinished dependencies)",
)
def list_tasks(
    app: KanbanTui, json: bool, column: None | int, board: None | int, actionable: bool
):
    """
    List all tasks on active board
    """
    boards = app.backend.get_boards()
    if not boards:
        print_to_console("No boards created yet.")
        return

    if column:
        tasks = app.backend.get_tasks_by_column(column_id=column)
    elif board:
        tasks = app.backend.get_tasks_by_board(board_id=board)
        board_present = board in [board.board_id for board in boards]
    else:
        tasks = app.backend.get_tasks_on_active_board()

    # Filter for actionable tasks if requested
    if actionable and tasks:
        tasks = [
            task
            for task in tasks
            if not task.blocked_by
            or all(
                app.backend.get_task_by_id(dep_id).finished
                for dep_id in task.blocked_by
            )
        ]

    if not tasks and column:
        print_to_console(f"No tasks in column with column_id = {column}.")
    elif board and not board_present:
        print_to_console(f"There is no board with board_id = {board}.")
    elif not tasks:
        print_to_console("No tasks created yet.")

    else:
        if json:
            task_list = TypeAdapter(list[Task])
            json_str = task_list.dump_json(
                tasks, indent=4, exclude_none=True, exclude_defaults=True
            ).decode("utf-8")
            print_to_console(json_str)
        else:
            for task in tasks:
                print_to_console(task)


@task.command("create")
@click.pass_obj
@click.argument("title", type=click.STRING)
@click.option(
    "--description",
    default="",
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
@click.option(
    "--depends-on",
    multiple=True,
    type=click.INT,
    help="Task ID(s) this task depends on (can be used multiple times)",
)
def create_task(
    app: KanbanTui,
    title: str,
    description: str,
    column: int,
    due_date: datetime.datetime,
    depends_on: tuple[int, ...],
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
    print_to_console(f"Created task `{title}` with {task_id = }.")

    # Add dependencies if specified
    if depends_on:
        for depends_on_task_id in depends_on:
            # Check if dependency task exists
            dep_task = app.backend.get_task_by_id(task_id=depends_on_task_id)
            if not dep_task:
                print_to_console(
                    f"[yellow]Task {depends_on_task_id} does not exist, skipping dependency.[/]"
                )
                continue

            # Check if dependency already exists
            existing_deps = app.backend.get_task_dependencies(task_id=task_id)
            if depends_on_task_id in existing_deps:
                print_to_console(
                    f"[yellow]Task {task_id} already depends on task {depends_on_task_id}.[/]"
                )
                continue

            # Check if this would create a circular dependency
            from kanban_tui.backends.sqlite.database import would_create_cycle

            if would_create_cycle(
                task_id, depends_on_task_id, app.backend.database_path
            ):
                print_to_console(
                    f"[red]Cannot add dependency: would create circular dependency with task {depends_on_task_id}.[/]"
                )
                continue

            # All checks passed, create the dependency
            app.backend.create_task_dependency(
                task_id=task_id,
                depends_on_task_id=depends_on_task_id,
            )
            print_to_console(
                f"[green]Added dependency: task {task_id} depends on task {depends_on_task_id}.[/]"
            )


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
        print_to_console("No fields to update provided.")
    else:
        _updated_task = app.backend.update_task_entry(
            task_id=task_id,
            title=title or old_task.title,
            description=description or old_task.description,
            category=None,
            due_date=due_date or old_task.due_date,
        )
        print_to_console(f"Updated task with {task_id = }.")


@task.command("move")
@click.pass_obj
@click.argument("task_id", type=click.INT)
@click.argument("target_column", type=click.INT)
@click.option(
    "--force",
    default=False,
    is_flag=True,
    type=click.BOOL,
    help="Force move even if blocked by dependencies",
)
def move_task(app: KanbanTui, task_id: int, target_column: int, force: bool):
    """
    Moves a task to another column
    """
    task = app.backend.get_task_by_id(task_id=task_id)
    new_column = app.backend.get_column_by_id(column_id=target_column)
    if not task:
        print_to_console(f"[red]There is no task with {task_id = }.[/]")
    elif not new_column:
        print_to_console(
            f"[red]There is no column with column_id = {target_column}.[/]"
        )
    elif task.column == target_column:
        print_to_console(
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

        # Check if task can move to target column (dependency validation)
        if not force:
            can_move, reason = task.can_move_to_column(
                target_column=target_column,
                start_column=active_board.start_column,
                backend=app.backend,
            )
            if not can_move:
                print_to_console(f"[red]Cannot move task: {reason}[/]")
                print_to_console("[yellow]Use --force flag to override this check.[/]")
                return

        # Update task status dates based on column transitions
        task.update_task_status(
            new_column=target_column,
            update_column_dict={
                "reset": active_board.reset_column,
                "start": active_board.start_column,
                "finish": active_board.finish_column,
            },
        )
        task.column = target_column
        moved_task = app.backend.update_task_status(new_task=task)
        print_to_console(
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
        print_to_console(f"Deleted task with {task_id = }.")

    else:
        print_to_console(f"[red]There is no task with {task_id = }[/].")
