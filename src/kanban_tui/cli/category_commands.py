"""CLI commands for kanban-tui category management"""

import click
from pydantic import TypeAdapter
from textual.color import Color, ColorParseError

from kanban_tui.app import KanbanTui
from kanban_tui.classes.category import Category
from kanban_tui.config import Backends
from kanban_tui.utils import print_to_console, get_next_category_color


@click.group()
@click.pass_obj
def category(app: KanbanTui):
    """
    Commands to manage categories via the CLI
    """
    if app.config.backend.mode != Backends.SQLITE:
        raise click.exceptions.UsageError(
            f"""
            Currently using `{app.config.backend.mode}` backend.
            Please change the backend to `{Backends.SQLITE}` before using the `category` command.
            """
        )


@category.command("list")
@click.pass_obj
@click.option(
    "--json",
    is_flag=True,
    default=False,
    type=click.BOOL,
    help="Use JSON format",
)
def list_categories(app: KanbanTui, json: bool):
    """
    List all categories, agents should prefer the --json flag
    """
    categories = app.backend.get_all_categories()
    if not categories:
        print_to_console("No categories created yet.")
    else:
        if json:
            category_list = TypeAdapter(list[Category])
            json_str = category_list.dump_json(
                categories, indent=4, exclude_none=True
            ).decode("utf-8")
            print_to_console(json_str)
        else:
            for category in categories:
                print_to_console(category)


@category.command("create")
@click.pass_obj
@click.argument("name", type=click.STRING)
@click.argument("color", type=click.STRING, required=False)
def create_category(app: KanbanTui, name: str, color: str | None):
    """
    Creates a new category
    """
    if color is None:
        existing_categories = app.backend.get_all_categories()
        used_colors = [cat.color for cat in existing_categories]
        color = get_next_category_color(used_colors)
    else:
        try:
            Color.parse(color)
        except ColorParseError:
            print_to_console(f"[red]Invalid color: {color}[/]")
            return

    new_category = app.backend.create_new_category(name=name, color=color)
    category_id = new_category.category_id
    print_to_console(
        f"Created category `{name}` with color `{color}` and {category_id = }."
    )


@category.command("delete")
@click.pass_obj
@click.argument("category_id", type=click.INT)
@click.option(
    "--no-confirm",
    default=False,
    is_flag=True,
    type=click.BOOL,
    help="Dont ask for confirmation to delete",
)
def delete_category(app: KanbanTui, category_id: int, no_confirm: bool):
    """
    Deletes a category
    """
    categories = app.backend.get_all_categories()

    if not categories:
        print_to_console("[red]No categories created yet.[/]")
    elif category_id in [category.category_id for category in categories]:
        if not no_confirm:
            click.confirm(
                f"Do you want to delete the category with {category_id = }?", abort=True
            )
        app.backend.delete_category(category_id)
        print_to_console(f"Deleted category with {category_id = }.")
    else:
        print_to_console(f"[red]There is no category with {category_id = }[/].")


@category.command("update")
@click.pass_obj
@click.argument("category_id", type=click.INT)
@click.option("--name", type=click.STRING, help="New name for the category")
@click.option("--color", type=click.STRING, help="New color for the category")
def update_category(
    app: KanbanTui, category_id: int, name: str | None, color: str | None
):
    """
    Updates an existing category
    """
    category = app.backend.get_category_by_id(category_id)
    if not category:
        print_to_console(f"[red]There is no category with {category_id = }[/].")
        return

    if color:
        try:
            Color.parse(color)
        except ColorParseError:
            print_to_console(f"[red]Invalid color: {color}[/]")
            return

    updated_name = name if name is not None else category.name
    updated_color = color if color is not None else category.color

    app.backend.update_category(category_id, updated_name, updated_color)
    print_to_console(f"Updated category with {category_id = }.")
