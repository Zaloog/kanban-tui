---
name: kanban-tui
description: Plans and manages tasks and todos for all project and task related prompts. Use this tool instead of your TodoWrite tool everytime. Make sure kanban-tui or ktui command are available otherwise use `uvx kanban-tui`
---

# Kanban-TUI Task Management Skill

## Description
Use kanban-tui (ktui) for task planning, tracking, and management throughout conversations. This skill provides CLI-based kanban board management for organizing work.

## When to Use
Use this skill proactively for:
- Complex multi-step tasks (3+ distinct steps)
- Non-trivial and complex tasks requiring planning
- When user explicitly requests task tracking or todo lists
- When user provides multiple tasks (numbered or comma-separated)
- After receiving new instructions to capture requirements
- Throughout implementation to track progress

## Prerequisites
- kanban-tui must be installed (`which kanban-tui`) if not installed and uv is installed use `uvx kanban-tui COMMAND`
- Use only CLI commands (`ktui board/task/column`), never launch the TUI interface by running kanban-tui without any command

## Core Commands

### Board Management
```bash
# ALWAYS use --json flag when listing for programmatic use
ktui board list --json

# Create new board (when not providing any -c/--columns argument, default Columns: Ready, Doing, Done, Archive will be used)
ktui board create "Board Name" --icon ":emoji:" --set-active -c "First Column" -c "Second Column"

# Activate a board
ktui board activate BOARD_ID

# Delete a board
ktui board delete BOARD_ID
```

### Column Management
```bash
# ALWAYS use --json flag when listing for programmatic use
ktui column list --json

# List columns for a specific board
ktui column list --board BOARD_ID --json
```

### Task Management
```bash
# Create task
ktui task create "Task Title" --description "Task details" --column COLUMN_ID

# Create task with due date
ktui task create "Task Title" --description "Details" --column COLUMN_ID --due-date 2026-12-31

# Create task with dependencies (task will be blocked until dependency is finished)
ktui task create "Task Title" --depends-on TASK_ID --column COLUMN_ID

# Create task with multiple dependencies (blocked until ALL dependencies are finished)
ktui task create "Task Title" --depends-on TASK_ID1 --depends-on TASK_ID2 --depends-on TASK_ID3 --column COLUMN_ID

# ALWAYS use --json flag when listing for programmatic use
ktui task list --json

# List tasks in a specific column (with JSON)
ktui task list --column COLUMN_ID --json

# List tasks on a specific board (with JSON)
ktui task list --board BOARD_ID --json

# List only actionable tasks (not blocked by unfinished dependencies)
ktui task list --actionable --json

# Move task to different column
ktui task move TASK_ID COLUMN_ID

# Move task even if blocked by unfinished dependencies (use --force to override)
ktui task move TASK_ID COLUMN_ID --force

# Update task
ktui task update TASK_ID --title "New Title" --description "New details"

# Delete task (with confirmation prompt)
ktui task delete TASK_ID

# Delete task (skip confirmation)
ktui task delete TASK_ID --no-confirm
```

### Skill Management
```bash
# Initialize SKILL.md in dedicated folder
ktui skill init

# Update SKILL.md to current tool version
ktui skill update

# Delete global and local SKILL.md files
ktui skill delete
```

## JSON Output Format
Use `--json` flag for machine-readable output. The JSON format provides:
- Valid JSON with double quotes
- ISO 8601 datetime strings
- Lowercase booleans (`true`/`false`)
- Only populated fields (null values and default values omitted)
- Computed fields always included (`days_since_creation`, `finished`, `is_blocked`, `has_dependents`)

Example output without dependencies:
```json
[
    {
        "task_id": 1,
        "title": "Implement feature",
        "column": 5,
        "creation_date": "2026-01-11T22:53:12",
        "description": "Feature details",
        "days_since_creation": 3,
        "finished": false,
        "is_blocked": false,
        "has_dependents": false
    }
]
```

Example output with dependencies:
```json
[
    {
        "task_id": 2,
        "title": "Dependent task",
        "column": 5,
        "creation_date": "2026-01-11T22:55:00",
        "blocked_by": [1],
        "days_since_creation": 3,
        "finished": false,
        "is_blocked": true,
        "has_dependents": false
    },
    {
        "task_id": 1,
        "title": "Implement feature",
        "column": 7,
        "creation_date": "2026-01-11T22:53:12",
        "blocking": [2],
        "days_since_creation": 3,
        "finished": false,
        "is_blocked": false,
        "has_dependents": true
    }
]
```

## Workflow

### 1. Initial Setup (per session)
When starting work that requires task tracking:

```bash
# Create and activate project board
# Use multiple `-c` arguments for custom columns
ktui board create "Project Name" --icon ":EMOJI_CODE:" --set-active

# Check default columns and get their IDs (ALWAYS use --json)
ktui column list --json
```

### 2. Task Creation
Break down work into specific, actionable tasks:

```bash
# Add tasks to Ready column (defaults to left-most visible column if --column not provided)
ktui task create "Task 1" --description "Details" --column READY_COLUMN_ID
ktui task create "Task 2" --description "Details" --column READY_COLUMN_ID

# If starting immediately, add to Doing column
ktui task create "Current Task" --description "Details" --column DOING_COLUMN_ID
```

### 3. Task Progression
As you work:

```bash
# Move task to Doing when starting
ktui task move TASK_ID DOING_COLUMN_ID

# Move task to Done when complete
ktui task move TASK_ID DONE_COLUMN_ID

# Archive completed tasks
ktui task move TASK_ID ARCHIVE_COLUMN_ID
```

### 4. Status Tracking
Regularly check progress:

```bash
# ALWAYS view tasks in JSON format for reliable parsing
ktui task list --json

# View only tasks in a specific column
ktui task list --column COLUMN_ID --json

# View only actionable tasks (not blocked by dependencies)
ktui task list --actionable --json
```

## Best Practices

### Command Usage
1. **Always Use --json**: Use `--json` flag for ALL list commands (board list, column list, task list) for reliable parsing
2. **Parse JSON Output**: Parse the JSON to extract IDs, status, and dependency information programmatically
3. **Check for Dependencies**: Always review `blocked_by` and `blocking` fields before moving tasks
4. **Use --force Carefully**: Only use `--force` flag when you understand the implications of moving blocked tasks

### Task Management
1. **Create Specific Tasks**: Break complex work into clear, actionable items
2. **Use Descriptions**: Add context about what needs to be done, markdown is supported
3. **One Active Task**: Keep only 1-2 tasks in Doing column at a time
4. **Immediate Updates**: Move tasks as soon as status changes
5. **Complete First**: Finish current tasks before starting new ones
6. **Use Dependencies**: Link tasks that have ordering requirements using `--depends-on`
7. **Check Dependencies**: Review `blocked_by` and `blocking` fields in JSON output to understand task relationships
8. **Focus on Actionable**: Use `--actionable --json` flag to see only tasks you can work on (not blocked)
9. **Respect Blocking**: Don't move tasks that are blocked unless using `--force` with valid reason

### Task States
- **Ready**: Not yet started, planned work
- **Doing**: Currently in progress (limit to 1-2 tasks)
- **Done**: Completed successfully
- **Archive**: Finished tasks no longer needing visibility

### Task Naming
Use imperative verbs for clarity:
- "Implement authentication feature"
- "Fix login bug"
- "Write unit tests for API"
- ~~"Authentication"~~ (too vague)
- ~~"Working on tests"~~ (status, not action)

### Task Completion
Only move to Done when:
- Task is FULLY accomplished
- Tests pass (if applicable)
- No blocking errors remain
- Implementation is complete

Keep as Doing if:
- Tests are failing
- Implementation is partial
- Unresolved errors exist
- Missing files or dependencies

## Examples

### Example 1: Feature Implementation
```bash
# Setup
ktui board create "Auth Feature" --icon ":lock:" --set-active
ktui column list --json  # Get column IDs (ALWAYS use --json)

# Plan tasks
ktui task create "Design authentication flow" --column 5
ktui task create "Implement login endpoint" --column 5
ktui task create "Add JWT token generation" --column 5
ktui task create "Write auth middleware" --column 5
ktui task create "Add tests for auth flow" --column 5

# Check all tasks (ALWAYS use --json)
ktui task list --json

# Start first task
ktui task move 1 6  # Move to Doing

# Complete and move to next
ktui task move 1 7  # Move to Done
ktui task move 2 6  # Start next task
```

### Example 2: Bug Fix with Investigation
```bash
# Create investigation tasks
ktui task create "Reproduce bug" --description "Verify the issue" --column 5
ktui task create "Identify root cause" --description "Debug and trace issue" --column 5
ktui task create "Implement fix" --description "Apply solution" --column 5
ktui task create "Test fix" --description "Verify resolution" --column 5

# Work through systematically (ALWAYS use --json)
ktui task list --json  # Check status regularly
```

### Example 3: Multiple Features
```bash
# User requests: "Add login, signup, and password reset"
ktui task create "Implement login form" --column 5
ktui task create "Implement signup form" --column 5
ktui task create "Implement password reset" --column 5
ktui task create "Add form validation" --column 5
ktui task create "Write tests for auth forms" --column 5
ktui task create "Update documentation" --column 5
```

### Example 4: Tasks with Dependencies
```bash
# Create foundational task first
ktui task create "Set up database schema" --column 5
# Assume task_id=1

# Create tasks that depend on the foundation
ktui task create "Implement user model" --depends-on 1 --column 5
ktui task create "Implement auth endpoints" --depends-on 1 --column 5
# Assume task_id=2 and 3

# Create task depending on multiple tasks
ktui task create "Write integration tests" --depends-on 2 --depends-on 3 --column 5

# View dependencies in JSON format
ktui task list --json
# Shows blocked_by and blocking arrays

# See only actionable tasks (not blocked by unfinished dependencies)
ktui task list --actionable
# Shows task 1 (no dependencies) but not tasks 2, 3, or 4 (blocked)

# After completing task 1, check actionable tasks
ktui task move 1 7  # Move to Done
ktui task list --actionable
# Now shows tasks 2 and 3 (task 1 is finished)
```

## Integration with Claude Code

### When to Use vs TodoWrite
- **Use ktui**: When user explicitly requests it (as per their preference)
- **TodoWrite**: Only if user hasn't specified a preference

### Communication
After creating/updating tasks:
1. Inform user briefly: "Added X tasks to kanban board"
2. Show task list output when relevant
3. Don't over-communicate every task move unless significant

### Task Breakdown
Apply same rules as TodoWrite:
- Break complex tasks into smaller steps
- Create specific, actionable items
- Use clear, descriptive names
- Track progress in real-time

## Troubleshooting

### No tasks showing
```bash
# Check if board is active
ktui board list

# Verify tasks exist
ktui task list
```

### Wrong column IDs
```bash
# Get correct column IDs
ktui column list

# Or for a specific board
ktui column list --board BOARD_ID
```

### Task in wrong column
```bash
# Move to correct column
ktui task move TASK_ID CORRECT_COLUMN_ID
```

## Quick Reference

| Action | Command |
|--------|---------|
| Create board | `ktui board create "Name" --set-active` |
| List boards | `ktui board list` |
| List boards (JSON) | `ktui board list --json` |
| List columns | `ktui column list` |
| List columns (JSON) | `ktui column list --json` |
| Create task | `ktui task create "Title" --column ID` |
| Create task with dependencies | `ktui task create "Title" --depends-on ID` |
| Create task with multiple deps | `ktui task create "Title" --depends-on ID1 --depends-on ID2` |
| List tasks | `ktui task list` |
| List tasks (JSON) | `ktui task list --json` |
| List actionable tasks | `ktui task list --actionable` |
| List actionable tasks (JSON) | `ktui task list --actionable --json` |
| Filter tasks by column | `ktui task list --column ID` |
| Move task | `ktui task move TASK_ID COLUMN_ID` |
| Update task | `ktui task update TASK_ID --title "New"` |
| Delete task | `ktui task delete TASK_ID` |
| Delete task (no confirm) | `ktui task delete TASK_ID --no-confirm` |

## Notes
- Always use CLI commands, never launch interactive TUI
- Column IDs are board-specific (get via `ktui column list`)
- Task IDs are unique across all boards
- Archive column is typically hidden by default
- Default columns: Ready, Doing, Done, Archive
- Use `--json` flag for machine-readable output

<!-- This Section is for the `kanban-tui skill update`-command to check if this SKILL.md version matches the tool version and update it if needed, the agent can ignore it -->
<!-- Version: KANBAN_TUI_VERSION -->
