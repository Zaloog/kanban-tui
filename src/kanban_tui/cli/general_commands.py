"""CLI commands for deleting the db, authentication and showing xdg file locations"""

import os
from pathlib import Path

import click

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends
from kanban_tui.utils import build_info_table
from kanban_tui.utils import print_to_console
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
        conf_path_str = os.getenv("KANBAN_TUI_CONFIG_FILE", CONFIG_FILE.as_posix())
        Path(conf_path_str).unlink(missing_ok=True)

        db_path_str = os.getenv("KANBAN_TUI_DATABASE_FILE", DATABASE_FILE.as_posix())
        Path(db_path_str).unlink(missing_ok=True)

        print_to_console(
            f"Config under {conf_path_str} deleted [green]successfully[/]."
        )
        print_to_console(
            f"Database under {db_path_str} deleted [green]successfully[/]."
        )


@click.command("auth")
@click.pass_obj
def auth(app: KanbanTui):
    """
    Open authentication screen only (requires `jira` backend selected)
    """
    app.auth_only = True
    if app.config.backend.mode != Backends.JIRA:
        raise click.exceptions.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.JIRA}` before using the `auth` command.
            """
        )

    api_key = app.run()
    if api_key:
        print_to_console(f"Api key detected under [green]{AUTH_FILE}[/].")


@click.command("info")
def info():
    """
    Displays location of config/data/auth xdg path files
    """
    table = build_info_table()
    print_to_console(table)
