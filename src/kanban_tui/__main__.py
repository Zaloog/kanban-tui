import click
from kanban_tui.app import KanbanTui

from kanban_tui.utils import create_demo_tasks
from kanban_tui.constants import (
    TEMP_CONFIG_FULL_PATH,
    TEMP_DB_FULL_PATH,
    DB_FULL_PATH,
    CONFIG_FULL_PATH,
)


@click.group(
    context_settings={"ignore_unknown_options": True}, invoke_without_command=True
)
@click.version_option(prog_name="kanban-tui")
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        app = KanbanTui()
        app.run()
    else:
        pass


@cli.command("demo")
@click.option("--clean", is_flag=True, default=False, help="Do not create dummy tasks")
def run_demo_app(clean: bool):
    """
    Starts a Demo App with temporary DB and Config
    """
    if not clean:
        create_demo_tasks(
            config_path=TEMP_CONFIG_FULL_PATH, database_path=TEMP_DB_FULL_PATH
        )

    app = KanbanTui(
        config_path=TEMP_CONFIG_FULL_PATH,
        database_path=TEMP_DB_FULL_PATH,
        demo_mode=True,
    )
    app.run()

    TEMP_CONFIG_FULL_PATH.unlink(missing_ok=True)
    TEMP_DB_FULL_PATH.unlink(missing_ok=True)


@cli.command("clear")
def delete_config_and_database():
    """
    Deletes DB and Config
    """

    CONFIG_FULL_PATH.unlink(missing_ok=True)
    DB_FULL_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    cli()
