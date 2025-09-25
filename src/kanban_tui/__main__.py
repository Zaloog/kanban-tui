import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.utils import create_demo_tasks
from kanban_tui.constants import (
    CONFIG_FILE,
    DEMO_CONFIG_FILE,
    DATABASE_FILE,
    DEMO_DATABASE_FILE,
)


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
    Starts a Demo App with temporary DB and Config
    """
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
    Deletes DB and Config
    """
    if confirm:
        CONFIG_FILE.unlink(missing_ok=True)
        DATABASE_FILE.unlink(missing_ok=True)
        Console().print(f"Config under {CONFIG_FILE}  deleted [green]successfully[/]")
        Console().print(
            f"Database under {DATABASE_FILE}  deleted [green]successfully[/]"
        )


if __name__ == "__main__":
    cli()
