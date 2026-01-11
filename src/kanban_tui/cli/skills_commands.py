from pathlib import Path

import click
from rich.console import Console

from kanban_tui.skills import (
    get_skill_md,
    get_skill_local_path,
    get_skill_global_path,
    get_skill_md_version,
    get_version,
)


@click.group()
def skill():
    """
    Entrypoint for all commands regarding agent skills
    """


@skill.command("init")
def init_skill():
    """
    Creates SKILL.md file in dedicated folder
    """
    file_path = get_skill_local_path()
    if click.confirm(
        f"Create SKILL.md in global skills folder under {get_skill_global_path()}?"
    ):
        file_path = get_skill_global_path()

    Path(file_path.parent).mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        Console().print(f"SKILL.md file under {file_path} already exists.")
    else:
        file_path.touch()
        file_path.write_text(get_skill_md())
        Console().print(f"SKILL.md file created under [green]{file_path}[/].")


@skill.command("update")
def update_skill():
    """
    Update SKILL.md to current tool version
    """
    current_version = get_version()
    Console().print(f"Current tool version [green]v{current_version}[/].")

    local_file = get_skill_local_path()
    if local_file.exists():
        current_local_version = get_skill_md_version(local_file)
        local_is_up_to_date = current_version < current_local_version
        local_up_to_date_str = (
            "[green](up to date)[/]"
            if local_is_up_to_date
            else "[red](newer version available)[/]"
        )
        Console().print(
            f"Found local [blue]SKILL.md[/] file with version [blue]v{current_local_version}[/] {local_up_to_date_str}."
        )
    else:
        Console().print(
            "No local [blue]SKILL.md[/] file present, use [yellow]`kanban-tui skill init`[/] to create one"
        )

    global_file = get_skill_global_path()
    if global_file.exists():
        current_global_version = get_skill_md_version(global_file)
        global_is_up_to_date = current_version < current_global_version
        global_up_to_date_str = (
            "[green](up to date)[/]"
            if global_is_up_to_date
            else "[red](newer version available)[/]"
        )
        Console().print(
            f"Found global [blue]SKILL.md[/] file with version [blue]v{current_global_version}[/] {global_up_to_date_str}."
        )
    else:
        Console().print(
            "No global [blue]SKILL.md[/] file present, use [yellow]`kanban-tui skill init`[/] to create one"
        )
