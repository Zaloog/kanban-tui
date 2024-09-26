<!-- Icons -->
<!-- Ruff -->
[![Rye](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/rye/main/artwork/badge.json)](https://rye-up.com)
[![PyPI-Server](https://img.shields.io/pypi/v/kanban-tui.svg)](https://pypi.org/project/kanban-tui/)
[![Pyversions](https://img.shields.io/pypi/pyversions/kanban-tui.svg)](https://pypi.python.org/pypi/kanban-tui)
[![Licence](https://img.shields.io/pypi/l/kanban-tui.svg)](https://github.com/astral-sh/kanban-tui/blob/main/LICENSE)
[![Downloads](https://static.pepy.tech/badge/kanban-tui)](https://pepy.tech/project/kanban-tui)

# kanban-tui

kanban-tui is a customizable task manager in the terminal.

![board_image](https://raw.githubusercontent.com/Zaloog/kanban-tui/main/images/image_kanbanboard.png)

## Demo

## Features
Expand for more detailed information

</details>
<details><summary>Following the XDG basedir convention</summary>

kanban-tui utilizes [platformdirs] `user_config_dir` to save the config file and `user_data_dir` for
the board specific task files. After creating your first board, you can use `kanban configure` to show the current settings table.
The config path in the table caption and the path for the task files can be found in the kanban_boards section.
</details>

</details>
<details><summary>Customizeable Board</summary>

- 4 default columns (more can be added via settings)
    - Ready
    - Doing
    - Done
    - Archive (default not visible)
</details>

</details>
<details><summary>Task Management</summary>

Features task creation, editing, deletion, movement between columns
</details>

</details>
<details><summary>Database Infomation</summary>

- Task attributes
    - Title
    - Category
    - Description
    - Due Date
    - Creation Date (updated on task creation)
    - Start Date (updated on movement to Doing column)
    - Finish Date (updated on movement to Done column)
</details>

</details>
<details><summary>Visual Summary</summary>

Uses plotext to show cool stuff
</details>

## Installation

You can install `kanban-tui` with one of the following options:

```bash
# not recommended
pip install kanban-tui
```

```bash
pipx install kanban-tui
```

```bash
rye install kanban-tui
```

```bash
uv tool install kanban-tui
```
I recommend using [pipx] or [rye] or [uv] to install CLI Tools into an isolated environment.

## Feedback and Issues
Feel free to reach out and share your feedback, or open an Issue, if something doesnt work as expected.
Also check the [Changelog] for new updates.

<!-- Repo Links -->
[Changelog]: https://github.com/Zaloog/kanban-tui/blob/main/CHANGELOG.md


<!-- external Links Python -->
[platformdirs]: https://platformdirs.readthedocs.io/en/latest/
[textual]: https://textual.textualize.io
[pipx]: https://github.com/pypa/pipx
[PyPi]: https://pypi.org/project/kanban-tui/
[plotext]: Link

<!-- external Links Others -->
[XDG]: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
[rye]: https://rye-up.com # Update
[uv]: https://rye-up.com # Update
