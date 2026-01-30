"""CLI commands for kanban-tui board management"""

import click
from pydantic import TypeAdapter

from kanban_tui.app import KanbanTui
from kanban_tui.classes.board import Board
from kanban_tui.config import Backends
from kanban_tui.utils import print_to_console


@click.group()
@click.pass_obj
def board(app: KanbanTui):
    """
    Commands to manage boards via the CLI
    """
    if app.config.backend.mode != Backends.SQLITE:
        raise click.exceptions.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `board` command.
            """
        )


@board.command("list")
@click.pass_obj
@click.option(
    "--json",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="use JSON format",
)
def list_boards(app: KanbanTui, json: bool):
    """
    List all boards, agents should prefer the --json flag
    """
    boards = app.backend.get_boards()
    if not boards:
        print_to_console("No boards created yet.")
    else:
        active_board_id = app.backend.active_board.board_id
        print_to_console(
            f"[red]--- Active Board has board_id = {active_board_id} ---[/]"
        )
        if json:
            board_list = TypeAdapter(list[Board])
            json_str = board_list.dump_json(boards, indent=4, exclude_none=True).decode(
                "utf-8"
            )
            print_to_console(json_str)
        else:
            for board in boards:
                print_to_console(board)


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
    app: KanbanTui,
    name: str,
    icon: str | None,
    columns: tuple[str] | None,
    set_active: bool,
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
    board_id = new_board.board_id
    print_to_console(f"Created board `{name}` with {board_id = }.")


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

    if not boards:
        print_to_console("[red]No boards created yet.[/]")
    elif board_id == app.backend.active_board.board_id:
        print_to_console("[red]Active board can not be deleted.[/]")
    elif board_id in [board.board_id for board in boards]:
        if not no_confirm:
            click.confirm(
                f"Do you want to delete the board with {board_id = }?", abort=True
            )
        app.backend.delete_board(board_id)
        print_to_console(f"Deleted board with {board_id = }.")

    else:
        print_to_console(f"[red]There is no board with {board_id = }[/].")


@board.command("update")
@click.pass_obj
@click.argument("board_id", type=click.INT)
@click.option("--name", type=click.STRING, help="New name for the board")
@click.option("--icon", type=click.STRING, help="New icon for the board")
def update_board(app: KanbanTui, board_id: int, name: str | None, icon: str | None):
    """
    Updates an existing board
    """
    boards = app.backend.get_boards()
    target_board = next(
        (board for board in boards if board.board_id == board_id), None
    )

    if not target_board:
        print_to_console(f"[red]There is no board with {board_id = }[/].")
        return

    updated_name = name if name is not None else target_board.name
    updated_icon = icon if icon is not None else target_board.icon

    app.backend.update_board(board_id, updated_name, updated_icon)
    print_to_console(f"Updated board with {board_id = }.")

@board.command("activate")
@click.pass_obj
@click.argument("board_id", type=click.INT)
def activate_board(app: KanbanTui, board_id: int):
    """
    Sets a board to active
    """
    boards = app.backend.get_boards()

    if not boards:
        print_to_console("[red]No boards created yet.[/]")
    elif board_id == app.backend.active_board.board_id:
        print_to_console("[yellow]Board is already active.[/]")
    elif board_id in [board.board_id for board in boards]:
        app.config.set_active_board(new_active_board_id=board_id)
        print_to_console(f"Board with {board_id = } is set as active board.")
    else:
        print_to_console(f"[red]There is no board with {board_id = }[/].")
