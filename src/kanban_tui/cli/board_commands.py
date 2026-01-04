"""CLI commands for kanban-tui board management"""

import click
from rich.console import Console

from kanban_tui.app import KanbanTui
from kanban_tui.config import Backends


@click.group()
@click.pass_obj
def board(app: KanbanTui):
    """
    Commands to manage boards via the CLI
    """
    if app.config.backend.mode != Backends.SQLITE:
        Console().print(f"Currently using [blue]{app.config.backend.mode}[/] backend.")
        Console().print(
            "Please change the backend to [blue]jira[/] before using the [green]`auth`[/] command."
        )


@board.command("list")
@click.pass_obj
def list_boards(app: KanbanTui):
    """
    List all boards
    """
    boards = app.backend.get_boards()
    if boards:
        for board in boards:
            if board == app.backend.active_board:
                Console().print("[red]--- Active Board ---[/]")
            Console().print(board)
    else:
        Console().print("No boards created yet.")


@board.command("create")
@click.pass_obj
@click.argument("name", type=click.STRING)
@click.option(
    "--icon",
    default="",
    show_default=True,
    type=click.STRING,
    help="Icon to use for the board (example: `:books:`)",
)
@click.option(
    "--set-active",
    default=False,
    is_flag=True,
    type=click.BOOL,
    help="Set the created board as active",
)
@click.option(
    "-c",
    "--columns",
    default=None,
    type=click.STRING,
    multiple=True,
    help="Columns to add to the board [default: Ready, Doing, Done, Archive]",
)
def create_board(
    app: KanbanTui, name: str, icon: str, columns: tuple[str], set_active: bool
):
    """
    Creates a new board
    """
    column_dict = None
    if columns:
        column_dict = {column: True for column in columns}
    new_board = app.backend.create_new_board(
        name=name, icon=icon, column_dict=column_dict
    )
    if set_active:
        app.config.set_active_board(new_active_board_id=new_board.board_id)
    Console().print(f"Created board {name} with board_id: {new_board.board_id}.")


@board.command("delete")
@click.pass_obj
@click.argument("board_id", type=click.INT)
@click.option(
    "--no-confirm",
    default=False,
    is_flag=True,
    type=click.BOOL,
    help="Dont ask for confirmation to delete",
)
def delete_board(app: KanbanTui, board_id: int, no_confirm: bool):
    """
    Deletes a board
    """
    boards = app.backend.get_boards()
    if board_id == app.backend.active_board.board_id:
        Console().print("[red]Active board can not be deleted.[/]")
        return
    if boards:
        for board in boards:
            if board.board_id == board_id:
                if not no_confirm:
                    click.confirm(
                        f"Do you want to delete the board with {board_id=} ", abort=True
                    )
                app.backend.delete_board(board_id)
                Console().print(
                    f"Deleted board {board.name} with board_id: {board_id}."
                )
                # TODO Delete
                # TODO Confirm
                return
        Console().print(f"[red]There is no board with {board_id=}[/].")
    else:
        Console().print("No boards created yet.")
