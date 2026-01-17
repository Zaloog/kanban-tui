from pathlib import Path

import click

from kanban_tui.utils import print_to_console
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
        print_to_console(f"SKILL.md file under {file_path} already exists.")
    else:
        file_path.touch()
        file_path.write_text(get_skill_md(), encoding="utf-8")
        print_to_console(f"SKILL.md file created under [green]{file_path}[/].")


@skill.command("delete")
def delete_skill():
    """
    Deletes global and local SKILL.md file
    """
    local_file_path = get_skill_local_path()
    global_file_path = get_skill_global_path()

    # No files present
    if not any((local_file_path.exists(), global_file_path.exists())):
        print_to_console("No SKILL.md files found in global and local skills folder.")
        return

    if click.confirm("Delete all kanban-tui SKILL.md files and the kanban-tui folder?"):
        if local_file_path.exists():
            local_file_path.unlink(missing_ok=True)
            local_file_path.parent.rmdir()
            print_to_console(
                f"Local Skill under {local_file_path} deleted [green]successfully[/]."
            )

        if global_file_path.exists():
            global_file_path.unlink(missing_ok=True)
            global_file_path.parent.rmdir()
            print_to_console(
                f"Global Skill under {global_file_path} deleted [green]successfully[/]."
            )


@skill.command("update")
def update_skill():
    """
    Update SKILL.md to current tool version
    """
    current_tool_version = get_version()
    print_to_console(f"Current tool version [blue]{current_tool_version}[/].")

    file_version_dict = {}
    file_path_dict = {
        "local": get_skill_local_path(),
        "global": get_skill_global_path(),
    }

    for locality, file_path in file_path_dict.items():
        if not file_path.exists():
            print_to_console(
                f"No {locality} [blue]SKILL.md[/] file present, use [yellow]`kanban-tui skill init`[/] to create one."
            )
            continue
        current_version = get_skill_md_version(file_path=file_path)
        is_up_to_date = current_version == current_tool_version

        if not is_up_to_date:
            file_version_dict[locality] = current_version

        up_to_date_str = (
            "[green](up to date)[/]"
            if is_up_to_date
            else "[red](versions dont match)[/]"
        )
        print_to_console(
            f"Found {locality} [blue]SKILL.md[/] file with version [blue]{current_version}[/] {up_to_date_str}."
        )

    if len(file_version_dict) > 0:
        confirm_str = "and the".join(
            [
                f"{locality} file {version}"
                for locality, version in file_version_dict.items()
            ]
        )
        if click.confirm(
            f"Do you want to update the {confirm_str} to the current tool version?"
        ):
            for locality in file_version_dict.keys():
                file_path = file_path_dict[locality]
                file_path.write_text(get_skill_md())
                print_to_console(
                    f"Updated {locality} [blue]SKILL.md[/] file to current tool version [blue]{current_tool_version}[/]."
                )
