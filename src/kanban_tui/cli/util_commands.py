"""CLI commands for deleting the db, authentication and showing xdg file locations"""

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends
from kanban_tui.utils import build_info_table
from kanban_tui.constants import (
    AUTH_FILE,
    CONFIG_FILE,
    DATABASE_FILE,
)


@click.command()
@click.option(
    "--confirm",
    is_flag=True,
    expose_value=True,
    prompt="Are you sure you want to delete the db and config?",
    help="Do not ask for confirmation",
)
def clear(confirm: bool):
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


@click.command("auth")
@click.pass_obj
def auth(app: KanbanTui):
    """
    Open authentication screen only (requires `jira` backend selected)
    """
    app.auth_only = True
    if app.config.backend.mode != Backends.JIRA:
        Console().print(f"Currently using [blue]{app.config.backend.mode}[/] backend.")
        Console().print(
            "Please change the backend to [blue]jira[/] before using the [green]`auth`[/] command."
        )
        return

    api_key = app.run()
    if api_key:
        Console().print(f"Api key detected under [green]{AUTH_FILE}[/].")


@click.command("info")
def info():
    """
    Displays location of config/data/auth xdg path files
    """
    table = build_info_table()
    Console().print(table)
