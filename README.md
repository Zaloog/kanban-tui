<!-- Icons -->
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI-Server](https://img.shields.io/pypi/v/kanban-tui.svg)](https://pypi.org/project/kanban-tui/)
[![Pyversions](https://img.shields.io/pypi/pyversions/kanban-tui.svg)](https://pypi.python.org/pypi/kanban-tui)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/kanban-tui)](https://pepy.tech/project/kanban-tui)
[![Coverage Status](https://coveralls.io/repos/github/Zaloog/kanban-tui/badge.svg?branch=main)](https://coveralls.io/github/Zaloog/kanban-tui?branch=main)

# kanban-tui

kanban-tui is a customizable task manager in the terminal.

## Demo GIF
This preview shows the core functionality of creating, moving, and managing tasks across different boards.
![demo_gif](https://raw.githubusercontent.com/Zaloog/kanban-tui/main/images/demo.gif)

If you want to test `kanban-tui` you can directly run this demo yourself with the help of [uv] using `uvx`:

```bash
uvx --from kanban-tui ktui demo
```

## Features

<details><summary>Following the XDG basedir convention</summary>

kanban-tui utilizes [platformdirs] `user_config_dir` to save
the config file and `user_data_dir` for the sqlite database.
</details>

<details><summary>Customizable Board</summary>

kanban-tui comes with four default columns
(`Ready`, `Doing`, `Done`, `Archive`) but can be customized to your needs.
More columns can be created via the `Settings`-Tab. Also the visibility of columns can be toggled.
Deletion of existing columns is only possible, if no task is present in the column you want to delete.
</details>

<details><summary>Multi Board Support</summary>

With version v0.4.0 kanban-tui allows the creation of multiple boards.
Use `B` on the `Kanban Board`-Tab to get an overview over all Boards including
the amount of columns, tasks and the closest Due Date.
Each Board starts with the default columns, but the columns are individual for each board.
</details>

<details><summary>Task Management</summary>

When on the `Kanban Board`-Tab you can `create (n)`, `edit (e)`, `delete (d)` or `move (H, L)` tasks between columns.
</details>

<details><summary>Audit Trail</summary>

All actions such as creating, updating, moving, and deleting tasks are logged in an audit table. This provides a complete history of changes, which is useful for tracking progress and debugging.
</details>

<details><summary>Visual Summary</summary>

To give you an overview over the amount of tasks you `created`, `started` or `finished`, kanban-tui
provides an `Overview`-Tab to show you a bar-chart on a `monthly`, `weekly` or `daily` scale.
It also can be changed to a stacked bar chart per category.
This feature is powered by the [plotext] library with help of [textual-plotext].
</details>

## Database Schema

The application uses a SQLite database to persist data. The schema is designed to be simple and effective for managing boards, columns, and tasks.

### Tasks Table

| Column         | Data Type   | Constraints                | Description                                 |
|----------------|------------|----------------------------|---------------------------------------------|
| `id`           | INTEGER    | PRIMARY KEY                | Unique identifier for the task.             |
| `title`        | TEXT       | NOT NULL                   | The title of the task.                      |
| `description`  | TEXT       |                            | A detailed description of the task.         |
| `category`     | TEXT       |                            | A category for grouping tasks.              |
| `due_date`     | TIMESTAMP  |                            | The date and time the task is due.          |
| `creation_date`| TIMESTAMP  | DEFAULT CURRENT_TIMESTAMP  | Timestamp of when the task was created.     |
| `start_date`   | TIMESTAMP  |                            | Timestamp of when task moved to 'Doing'.    |
| `finish_date`  | TIMESTAMP  |                            | Timestamp of when task moved to 'Done'.     |
| `column_id`    | INTEGER    | FOREIGN KEY (Columns)      | The column this task belongs to.            |

### Columns Table

| Column   | Data Type | Constraints           | Description                          |
|----------|-----------|-----------------------|--------------------------------------|
| `id`     | INTEGER   | PRIMARY KEY           | Unique identifier for the column.    |
| `name`   | TEXT      | NOT NULL              | The name of the column (e.g., 'Doing'). |
| `board_id`| INTEGER  | FOREIGN KEY (Boards)  | The board this column belongs to.    |

### Boards Table

| Column   | Data Type | Constraints   | Description                       |
|----------|-----------|--------------|-----------------------------------|
| `id`     | INTEGER   | PRIMARY KEY  | Unique identifier for the board.  |
| `name`   | TEXT      | NOT NULL     | The name of the board.            |

### Audit Table

| Column    | Data Type  | Constraints                | Description                                 |
|-----------|------------|----------------------------|---------------------------------------------|
| `id`      | INTEGER    | PRIMARY KEY                | Unique identifier for the log entry.        |
| `task_id` | INTEGER    | FOREIGN KEY (Tasks)        | The affected task.                          |
| `action`  | TEXT       | NOT NULL                   | The action performed (e.g., 'CREATED', 'MOVED'). |
| `timestamp`| TIMESTAMP | DEFAULT CURRENT_TIMESTAMP  | When the action occurred.                   |

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

To be able to use `kanban-tui` in your browser with the `--web`-flag, the optional dependency
`textual-serve` is needed. You can add this to `kanban-tui` by installing the optional `web`-dependency
with the installer of your choice, for example with [uv]:

```bash
uv tool install 'kanban-tui[web]'
```

## Usage

### Normal Mode

Starts `kanban-tui` with a starting board. The application can be closed by pressing `ctrl+q`.
Pass the `--web` flag and follow the shown link to open `kanban-tui` in your browser.

```bash
ktui
```

### Demo Mode

Creates a temporary Config and Database which is populated with example Tasks to play around.
Kanban-Tui will delete the temporary Config and Database after closing the application.
Pass the `--clean` flag to start with an empty demo app.
Pass the `--keep` flag to tell `kanban-tui` not to delete the temporary Database and Config.
Pass the `--web` flag and follow the shown link to open `kanban-tui` in your browser.

```bash
ktui demo
```

### Clear Database and Configuration

If you want to start with a fresh database and configuration file, you can use this command to
delete your current database and configuration file.

```bash
ktui clear
```

## Feedback and Issues

Feel free to reach out and share your feedback, or open an [Issue],
if something doesn't work as expected.
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