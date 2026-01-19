"""CLI commands for the demo"""

import click

from kanban_tui.app import KanbanTui
from kanban_tui.constants import (
    DEMO_CONFIG_FILE,
    DEMO_DATABASE_FILE,
)
from kanban_tui.utils import print_to_console, create_demo_tasks


@click.command()
@click.option("--clean", is_flag=True, default=False, help="Do not create dummy tasks")
@click.option(
    "--keep", is_flag=True, default=False, help="Do not delete db/config after closing"
)
@click.option("--web", is_flag=True, default=False, help="Host app locally")
@click.pass_obj
def demo(app: KanbanTui, clean: bool, keep: bool, web: bool):
    """
    Starts a demo app with temporary database and config
    """
    if not clean:
        create_demo_tasks(app)

    if web:
        try:
            from textual_serve.server import Server
        except ModuleNotFoundError:
            print_to_console("[yellow]textual-serve[/] dependency not found.")
            print_to_console(
                "Please install [yellow]kanban-tui\\[web][/] to add web support."
            )
            return

        command = "ktui demo"
        command += " --clean" if clean else ""
        command += " --keep" if keep else ""
        server = Server(command)
        server.serve()
    else:
        app.run()

    if not keep:
        DEMO_CONFIG_FILE.unlink(missing_ok=True)
        DEMO_DATABASE_FILE.unlink(missing_ok=True)
