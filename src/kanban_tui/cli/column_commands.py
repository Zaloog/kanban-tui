"""CLI commands for kanban-tui column management"""

import click
from pydantic import TypeAdapter

from kanban_tui.app import KanbanTui
from kanban_tui.classes.column import Column
from kanban_tui.config import Backends
from kanban_tui.utils import print_to_console


@click.group()
@click.pass_obj
def column(app: KanbanTui):
    """
    Commands to manage columns via the CLI
    """
    if app.config.backend.mode != Backends.SQLITE:
        raise click.exceptions.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `column` command.
            """
        )


@column.command("list")
@click.pass_obj
@click.option(
    "--json",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="use JSON format",
)
@click.option(
    "--board",
    default=None,
    type=click.INT,
    help="show only columns on this board",
)
def list_columns(app: KanbanTui, json: bool, board: None | int):
    """
    List all columns on active board, agents should prefer --json flag
    """
    boards = app.backend.get_boards()
    if not boards:
        print_to_console("No boards created yet.")
        return

    columns = app.backend.get_columns(board_id=board)
    if not columns:
        print_to_console(f"There is no board with board_id = {board}.")

    if json:
        column_list = TypeAdapter(list[Column])
        json_str = column_list.dump_json(columns, indent=4, exclude_none=True).decode(
            "utf-8"
        )
        print_to_console(json_str)
    else:
        for column in columns:
            print_to_console(column)
