import os
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends
from kanban_tui.utils import create_demo_tasks
from kanban_tui.constants import (
    AUTH_FILE,
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
    Displayes location of config and data files
    """
    table = Table(title="[yellow]kanban-tui[/] xdg file locations", show_header=False)

    config_file = Path(os.getenv("KANBAN_TUI_CONFIG_FILE", CONFIG_FILE))
    config_exists = (
        "([green]exists[/])" if config_file.exists() else "([red]nothing here[/])"
    )
    demo_config_file = Path(os.getenv("KANBAN_TUI_CONFIG_FILE", DEMO_CONFIG_FILE))
    demo_config_exists = (
        "([green]exists[/])" if demo_config_file.exists() else "([red]nothing here[/])"
    )

    table.add_row("[blue]config files[/]", end_section=True)
    config_table = Table(show_header=False, show_edge=False)
    config_table.add_row("Normal", f"[yellow]{config_file}[/] {config_exists}")
    config_table.add_row(
        "Demo", f"[yellow]{demo_config_file}[/] {demo_config_exists}", end_section=True
    )
    table.add_row(config_table, end_section=True)

    data_file = DATABASE_FILE
    data_exists = (
        "([green]exists[/])" if data_file.exists() else "([red]nothing here[/])"
    )
    demo_data_file = DEMO_DATABASE_FILE
    demo_data_exists = (
        "([green]exists[/])" if demo_data_file.exists() else "([red]nothing here[/])"
    )

    table.add_row("[blue]data files[/]", end_section=True)
    data_table = Table(show_header=False, show_edge=False)
    data_table.add_row("Normal", f"[yellow]{data_file}[/] {data_exists}")
    data_table.add_row(
        "Demo", f"[yellow]{demo_data_file}[/] {demo_data_exists}", end_section=True
    )
    table.add_row(data_table, end_section=True)

    auth_file = Path(os.getenv("KANBAN_TUI_AUTH_FILE", AUTH_FILE))
    auth_exists = (
        "([green]exists[/])" if auth_file.exists() else "([red]nothing here[/])"
    )

    table.add_row("[blue]auth file[/]", end_section=True)
    auth_table = Table(show_header=False, show_edge=False)
    auth_table.add_row("Normal", f"[yellow]{auth_file}[/] {auth_exists}")
    table.add_row(auth_table, end_section=True)

    Console().print(table)


if __name__ == "__main__":
    cli()
