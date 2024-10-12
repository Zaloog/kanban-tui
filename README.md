<!-- Icons -->
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI-Server](https://img.shields.io/pypi/v/kanban-tui.svg)](https://pypi.org/project/kanban-tui/)
[![Pyversions](https://img.shields.io/pypi/pyversions/kanban-tui.svg)](https://pypi.python.org/pypi/kanban-tui)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/kanban-tui)](https://pepy.tech/project/kanban-tui)
[![Coverage Status](https://coveralls.io/repos/github/Zaloog/kanban-tui/badge.svg?branch=main)](https://coveralls.io/github/Zaloog/kanban-tui?branch=main)

# kanban-tui

kanban-tui is a customizable task manager in the terminal.

![board_image](https://raw.githubusercontent.com/Zaloog/kanban-tui/main/images/image_kanbanboard.png)

<!-- ## Demo -->

## Features
Expand for more detailed information

</details>
<details><summary>Following the XDG basedir convention</summary>

kanban-tui utilizes [platformdirs] `user_config_dir` to save
the config file and `user_data_dir` for the sqlite database.
</details>

</details>
<details><summary>Customizeable Board</summary>

kanban-tui comes with four default columns
(`Ready`, `Doing`, `Done`, `Archive`).
More columns can be created via the `Settings`-Tab. Also the visibility of columns can be toggled.
Deletion of an existing columns is only possible, if no task is present in the column you want to delete.
</details>

</details>
<details><summary>Task Management</summary>

When on the `Kanban Board`-Tab you can `create (n)`, `edit (e)`, `delete (d)` or `move (H, L)` tasks between columns.
</details>

<!-- </details>
<details><summary>Database Infomation</summary>

- Task attributes
    - Title
    - Category
    - Description
    - Due Date
    - Creation Date (updated on task creation)
    - Start Date (updated on movement to Doing column)
    - Finish Date (updated on movement to Done column)
</details> -->

</details>
<details><summary>Visual Summary</summary>

To give you an overview over the amount of tasks you `created`, `started` or `finished`, kanban-tui
provides an `Overview`-Tab to show you a bar-chart on a `monthly`, `weekly` or `daily` scale.
It also can be changed to a stacked bar chart per category.
This feature is powered by the [plotext] library with help of [textual-plotext].
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
I recommend using [pipx], [rye] or [uv] to install CLI Tools into an isolated environment.


## Usage
### Normal Mode
```bash
ktui
```

### Demo Mode
Creates a temporary Config and Database which is populated with example Tasks to play around.
Kanban-Tui will delete the temporary Config and Database after closing the application.
Pass the `--clean` flag to start with an empty demo app.

```bash
ktui demo
```

## Feedback and Issues
Feel free to reach out and share your feedback, or open an [Issue],
if something doesnt work as expected.
Also check the [Changelog] for new updates.


<!-- Repo Links -->
[Changelog]: https://github.com/Zaloog/kanban-tui/blob/main/CHANGELOG.md
[Issue]: https://github.com/Zaloog/kanban-tui/issues


<!-- external Links Python -->
[platformdirs]: https://platformdirs.readthedocs.io/en/latest/
[textual]: https://textual.textualize.io
[pipx]: https://github.com/pypa/pipx
[PyPi]: https://pypi.org/project/kanban-tui/
[plotext]: https://github.com/piccolomo/plotext
[textual-plotext]: https://github.com/Textualize/textual-plotext

<!-- external Links Others -->
[XDG]: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
[rye]: https://rye.astral.sh
[uv]: https://docs.astral.sh/uv
