# Changelog

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
