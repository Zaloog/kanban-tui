# Changelog

## v0.17.0 (unreleased)
### Added
- Added board/session deletion and Task title/description updates for Claude backend
- Added category command to manage categories and updated existing commands for `--category`
- Added category command to mcp server

### Changed
- Changed SKILL.md to include category commands/options, use `ktui skill update` to get the latest version

## v0.16.1
### Fixed
- Run mcp server in an asyncio task with another task listening to SIGINT and SIGTERM to properly close down the mcp Server
when exiting the agent. Before it happened, that a subprocess was dangling

## v0.16.0
### Added
- Added a local kanban-tui mcp server. Requires installation with optional `mcp` dependency (e.g. `uv tool install kanban-tui\[mcp\]`).
- Added new `ktui mcp` command, which shows helper command how to add the mcp server.
The server itself is started by appending the `--start-server` flag.
- Added a better indication, which backend is active in the backend selector

### Changed
- Changed `refresh` shortcut from `f5` to `r`

## v0.15.0
### Added
- `Claude` Backend now allows to move/delete tasks
- `Jira` Backend progress, can create boards via jql, columns are based on status read_only currently
- Removed Custom Backend Option

## v0.14.0
### Added
- FOREIGN_KEYS check to migration
- Claude Backend to view tasks under `~/.claude/tasks`
- First version of jira Backend (not fully functional)

### Fixed
- Added `Delete` mention on Category Dropdown

## v0.13.1
### Fixed
- Fix migration issue due to FOREIGN_KEYS not disabled during migration
- Updated SKILL.md file to prefer default columns, to ensure status transitions on first init

## v0.13.0
### Added
- Added a `--json` flag to `board/task/column list` commands, e.g. `ktui board list --json`
- Added a `--board/column` filter to `ktui task list`
- Added a `--board` filter to `ktui column list`
- Added a `skill delete` command to delete the local and global `SKILL.md` files for kanban-tui
and the parent kanban-tui folder
- Added task dependency management:
  - Tasks can now depend on other tasks, creating workflow dependencies
  - Dependency selector widget in task edit screen with dropdown and table display
  - Visual indicators on task cards showing blocked/blocking status
  - Circular dependency prevention to avoid dependency loops
  - Tasks with unfinished dependencies are blocked from moving to start/finish columns
  - CLI support with `--depends-on` flag for task creation
  - New `task_dependencies` table in database schema
- Added automatic database migrations

### Fixed
- Show proper time for `Created at` Label when editing existing boards, instead of the current time
- Make default description of tasks created without the `--description` option to `""` instead of `None`
to no break editing tasks
- Fix task query to get the correct `creation_date`
- Fixed foreign key constraint violation when deleting boards by correcting deletion order

### Changed
- Updated SKILL.md File
- New database schema (with automatic migrations)

## v0.12.0
### Added
- Added functionality to suspend app and edit task description in `$EDITOR` (default: `vim`),
will show notification, if command is not available

### Fixed
- Fixed validation issue, in category creation, where the button would be enabled with an empty
name/color input.


## v0.11.1
### Fixed
- Used proper "utf-8" encoding when Writing SKILL.md file


## v0.11.0
### Added
- Added CLI interface to manage boards/tasks/columns
- Added `skill init` command to create `SKILL.md` files for claude
- Added `skill update` command to update `SKILL.md` files to current used tool version
- Added `skill files` location to `info` command output table

### Fixed
- Fixed missing refresh, when new column is added

### Changed
- Removed board_id column from tasks table. No change in functionality.


## v0.10.2
### Fixed
- Fixed visual bug to display dates in modal task screen


## v0.10.1
### Fixed
- Fixed bug, that column.status_update selection values do not update, when the column order is changed
- Fixed bug, that SettingsScreen widgets were not updated, when the active board is changed


## v0.10.0
### Added
- Added option to change the column order via the SettingScreen
- Reworked the ColumnListView UI


## v0.9.0
### Added
- Added new config values `movement_mode` to change task movement modes
    - `adjacent` (default, same as before)
    - `jump` shows the column to jump to and can confirm move with enter
- Added new config value `columns_in_view` to change the amount of visible columns on board
which makes the board is now horizontally scrollable
- Added vim bindings to all Select Navigation
- Added Task Card Movement via Mouse Drag n Drop
- Added Category Management to database and menu in TaskEditScreen
- Added new `info` command to show location and presence of xdg config/data/auth file paths
- Added jump functionality to the SettingScreen via `textual-jumper`
- Rework the Modal Task Screen
- Added new entrypoint `kanban-tui`, old entrypoint `ktui` is still available
- Update Docs (mermaid schema, new commands)
- (not fully functional yet) Option to switch the Backend in the Footer
- (not fully functional yet) Added new `auth` command to directly open the auth modal screen when jira backend is chosen
- (not fully functional yet) Added Jira Backend + AuthFile (Backends can be switched in Settings)

### Fixed
- Fixed focus bug if no visible tasks are on board (due to column visibility change)
- Fixed error, if start column was set to a column a task was already in and the task was then moved
to finish column. The creation_date is used in that case, instead of the start_date

### Changed
- Changed kanban-tui config to a `.toml` config file instead of `.yaml` and now using pydantic_settings
- XDG dirs are now under `~/.local/share/kanban_tui` for data and `~/.config/kanban_tui` for configs
- Reworked UI


## v0.8.2
- Fix Bugs and make `kanban-tui` compatible with `textual` 6.X


## v0.8.1
- Fix Config initialization for mac port which uses pydantic v1.X


## v0.8.0
- Add theme to config value to make it persistant after closing the app


## v0.7.4
- Move back to use hatchling as build backend


## v0.7.3
- Removed pendulum dependency and change to python native datetime
- Move to uv build backend


## v0.7.2
- Add fixed textual_datepicker to repo cause no longer maintained and not compatible with textual 3.X


## v0.7.1
- Fix crashes due to new textual major version. `app.query` -> `app.screen.query`


## v0.7.0
- Added better column management
- Added improvements to the settings tab UI including shortcuts
- Added support for arbitrary column names, also supporting emoji codes
- Added manual refresh binding, helpful when having multiple sessions open to sync between them
- Added new audit table in db
- Added new audit table log to OverView tab
- Added shortcuts to tab headers
- Fixed Bug, that allowed duplicate column names


## v0.6.4
- Fix emoji of boardname in border title

## v0.6.3
- Bug Fixes due to breaking changes with textual 2.0 release
    - Emojis are now rendered with rich.text.Text.from_markup
    - Disabled the type_to_search functionality to keep vim-like navigation on CategorySelector

## v0.6.2
- Fix Demo Category colors to be less bright

## v0.6.1
- Fix flicker back when clicking on `Overview`-tab when on `KanbanBoard`-tab

## v0.6.0
- Add Confirmation prompt to database and config deletion
- Add serving on localhost via `textual-serve` with new`--web`-flag
- Fix Bug in Overview Daterange Creation

## v0.5.0
- Add Footer to Task Edit and Shortcut to save/edit Task
- Add Custom Column Creation on Board Creation

## v0.4.0
- Add Multi Board support
- Add Individual Columns for each board

## v0.3.2
- Bugfix: Attempting to move a task with h/j/k/l caused Error, when no task was present

## v0.3.1
- Fix add a new Rule Widget in the `columns.visibility`-Settings to create columns at position 0
and also enables creation if all columns are deleted

## v0.3.0
- Add `--keep` flag to demo mode to prevent kanban-tui from deleting the temporary files

## v0.2.0
- Added Click Options `demo` and `clear`
- Added command for Demo-Mode with tasks and Demo-Mode without tasks (`--clean` -flag)
- Added command to delete config and database

## v0.1.2...v0.1.6
- Added CICD automation

## v0.1.1
- Switched database and config path from `CWD` for developing to `XDG`

## v0.1.0
- Published on PyPi
