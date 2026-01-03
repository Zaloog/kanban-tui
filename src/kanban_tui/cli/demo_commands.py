"""CLI commands for the demo"""

import os

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.constants import (
    DEMO_CONFIG_FILE,
    DEMO_DATABASE_FILE,
)
from kanban_tui.utils import create_demo_tasks


@click.command()
@click.option("--clean", is_flag=True, default=False, help="Do not create dummy tasks")
@click.option(
    "--keep", is_flag=True, default=False, help="Do not delete db/config after closing"
)
@click.option("--web", is_flag=True, default=False, help="Host app locally")
def demo(clean: bool, keep: bool, web: bool):
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
