import os
import json
from datetime import datetime

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends, init_config, SETTINGS, Settings
from kanban_tui.utils import create_demo_tasks, build_info_table
from kanban_tui.constants import (
    AUTH_FILE,
    CONFIG_FILE,
    DEMO_CONFIG_FILE,
    DATABASE_FILE,
    DEMO_DATABASE_FILE,
)
from kanban_tui.backends.sqlite.backend import SqliteBackend


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
        else:
            pass


@cli.command("demo")
@click.option("--clean", is_flag=True, default=False, help="Do not create dummy tasks")
@click.option(
    "--keep", is_flag=True, default=False, help="Do not delete db/config after closing"
)
@click.option("--web", is_flag=True, default=False, help="Host app locally")
def run_demo_app(clean: bool, keep: bool, web: bool):
    """
    Starts a demo app with temporary database and config
    """
    os.environ["KANBAN_TUI_CONFIG_FILE"] = DEMO_CONFIG_FILE.as_posix()
    if clean:
        DEMO_CONFIG_FILE.unlink(missing_ok=True)
        DEMO_DATABASE_FILE.unlink(missing_ok=True)
    else:
        if not DEMO_DATABASE_FILE.exists():
            create_demo_tasks(
                config_path=DEMO_CONFIG_FILE.as_posix(),
                database_path=DEMO_DATABASE_FILE.as_posix(),
            )

    if web:
        try:
            from textual_serve.server import Server
        except ModuleNotFoundError:
            Console().print("[yellow]textual-serve[/] dependency not found.")
            Console().print(
                "Please install [yellow]kanban-tui\\[web][/] to add web support."
            )
            return

        command = "ktui demo"
        command += " --clean" if clean else ""
        command += " --keep" if keep else ""
        server = Server(command)
        server.serve()
    else:
        app = KanbanTui(
            config_path=DEMO_CONFIG_FILE.as_posix(),
            database_path=DEMO_DATABASE_FILE.as_posix(),
            demo_mode=True,
        )
        app.run()

    if not keep:
        DEMO_CONFIG_FILE.unlink(missing_ok=True)
        DEMO_DATABASE_FILE.unlink(missing_ok=True)


@cli.command("clear")
@click.option(
    "--confirm",
    is_flag=True,
    expose_value=True,
    prompt="Are you sure you want to delete the db and config?",
    help="Do not ask for confirmation",
)
def delete_config_and_database(confirm: bool):
    """
    Deletes database and config
    """
    if confirm:
        CONFIG_FILE.unlink(missing_ok=True)
        DATABASE_FILE.unlink(missing_ok=True)
        Console().print(f"Config under {CONFIG_FILE}  deleted [green]successfully[/]")
        Console().print(
            f"Database under {DATABASE_FILE}  deleted [green]successfully[/]"
        )


@cli.command("auth")
def enter_auth_only_mode():
    """
    Open authentication screen only (requires `jira` backend selected)
    """
    app = KanbanTui(
        config_path=CONFIG_FILE.as_posix(),
        database_path=DATABASE_FILE.as_posix(),
        auth_only=True,
    )
    if app.config.backend.mode != Backends.JIRA:
        Console().print(f"Currently using [blue]{app.config.backend.mode}[/] backend.")
        Console().print(
            "Please change the backend to [blue]jira[/] before using the [green]`auth`[/] command."
        )
        return

    api_key = app.run()
    if api_key:
        Console().print(f"Api key detected under [green]{AUTH_FILE}[/].")
    else:
        Console().print(f"No api key found under [green]{AUTH_FILE}[/].")


@cli.command("info")
def show_file_infos():
    """
    Displays location of config/data/auth xdg path files
    """
    table = build_info_table()
    Console().print(table)


def get_backend(config_path: str = None, database_path: str = None):
    """Helper function to initialize backend for CLI commands"""
    if config_path is None:
        config_path = CONFIG_FILE.as_posix()
    if database_path is None:
        database_path = DATABASE_FILE.as_posix()

    # Initialize settings context and config file
    SETTINGS.set(Settings())
    init_config(config_path=config_path, database=database_path)
    config = SETTINGS.get()

    if config.backend.mode != Backends.SQLITE:
        Console().print(f"[yellow]Warning:[/] CLI commands currently only support SQLite backend.")
        Console().print(f"Current backend: [blue]{config.backend.mode}[/]")
        return None

    backend = SqliteBackend(settings=config.backend.sqlite_settings)
    return backend, config


@cli.command("create-task")
@click.option("--title", required=True, help="Task title")
@click.option("--description", default="", help="Task description")
@click.option("--column", default=None, type=int, help="Column ID (defaults to first column)")
@click.option("--category", default=None, help="Task category")
@click.option("--due-date", default=None, help="Due date in ISO format (YYYY-MM-DD)")
@click.option("--board-id", default=None, type=int, help="Board ID (defaults to active board)")
def create_task(title: str, description: str, column: int | None, category: str | None, due_date: str | None, board_id: int | None):
    """
    Create a new task via CLI
    """
    result = get_backend()
    if result is None:
        return

    backend, _ = result

    # Set active board if specified
    if board_id is not None:
        backend.settings.active_board_id = board_id

    # Get columns for the active board
    columns = backend.get_columns()
    if not columns:
        Console().print("[red]Error:[/] No columns found on the active board.")
        return

    # Default to first column if not specified
    if column is None:
        column = columns[0].column_id
    else:
        # Validate column exists
        if not any(col.column_id == column for col in columns):
            Console().print(f"[red]Error:[/] Column ID {column} not found on board.")
            Console().print("Available columns:")
            for col in columns:
                Console().print(f"  ID: {col.column_id} - {col.name}")
            return

    # Parse due date
    due_date_obj = None
    if due_date:
        try:
            due_date_obj = datetime.fromisoformat(due_date)
        except ValueError:
            Console().print(f"[red]Error:[/] Invalid due date format. Use YYYY-MM-DD")
            return

    # Create the task
    task = backend.create_new_task(
        title=title,
        description=description,
        column=column,
        category=category,
        due_date=due_date_obj,
    )

    Console().print(f"[green]Task created successfully![/]")
    Console().print(json.dumps(json.loads(task.model_dump_json()), indent=2))


@cli.command("move-task")
@click.option("--task-id", required=True, type=int, help="Task ID to move")
@click.option("--column", required=True, type=int, help="Target column ID")
@click.option("--board-id", default=None, type=int, help="Board ID (defaults to active board)")
def move_task(task_id: int, column: int, board_id: int | None):
    """
    Move a task to a different column
    """
    result = get_backend()
    if result is None:
        return

    backend, _ = result

    # Set active board if specified
    if board_id is not None:
        backend.settings.active_board_id = board_id

    # Get all tasks on the active board
    tasks = backend.get_tasks_on_active_board()
    task = None
    for t in tasks:
        if t.task_id == task_id:
            task = t
            break

    if task is None:
        Console().print(f"[red]Error:[/] Task ID {task_id} not found on the active board.")
        return

    # Validate column exists
    columns = backend.get_columns()
    if not any(col.column_id == column for col in columns):
        Console().print(f"[red]Error:[/] Column ID {column} not found on board.")
        Console().print("Available columns:")
        for col in columns:
            Console().print(f"  ID: {col.column_id} - {col.name}")
        return

    # Get board info to get column mappings
    board = backend.active_board
    update_column_dict = {
        "reset": board.reset_column,
        "start": board.start_column,
        "finish": board.finish_column,
    }

    # Update task status
    task.update_task_status(column, update_column_dict)
    task.column = column

    # Save to database
    backend.update_task_status(task)

    Console().print(f"[green]Task {task_id} moved successfully to column {column}![/]")
    Console().print(json.dumps(json.loads(task.model_dump_json()), indent=2))


@cli.command("get-tasks")
@click.option("--board-id", default=None, type=int, help="Board ID (defaults to active board)")
@click.option("--format", type=click.Choice(["json", "pretty"]), default="json", help="Output format")
def get_tasks(board_id: int | None, format: str):
    """
    Retrieve tasks in JSON format
    """
    result = get_backend()
    if result is None:
        return

    backend, _ = result

    # Set active board if specified
    if board_id is not None:
        backend.settings.active_board_id = board_id

    # Get all tasks on the active board
    tasks = backend.get_tasks_on_active_board()

    # Convert tasks to JSON
    tasks_data = [json.loads(task.model_dump_json()) for task in tasks]

    if format == "pretty":
        Console().print(json.dumps(tasks_data, indent=2))
    else:
        print(json.dumps(tasks_data))


if __name__ == "__main__":
    cli()
