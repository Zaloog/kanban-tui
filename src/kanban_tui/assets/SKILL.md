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
# List all boards
ktui board list

# List all boards (JSON format for programmatic use)
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
# List columns on active board
ktui column list

# List columns (JSON format)
ktui column list --json

# List columns for a specific board
ktui column list --board BOARD_ID
```

### Task Management
```bash
# Create task
ktui task create "Task Title" --description "Task details" --column COLUMN_ID

# Create task with due date
ktui task create "Task Title" --description "Details" --column COLUMN_ID --due-date 2026-12-31

# List all tasks
ktui task list

# List all tasks (JSON format for programmatic use)
ktui task list --json

# List tasks in a specific column
ktui task list --column COLUMN_ID

# Move task to different column
ktui task move TASK_ID COLUMN_ID

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
- Only populated fields (null values omitted)

Example output:
```json
[
    {
        "task_id": 1,
        "title": "Implement feature",
        "column": 5,
        "creation_date": "2026-01-11T22:53:12",
        "description": "Feature details",
        "days_since_creation": 3,
        "finished": false
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

# Check default columns (Ready, Doing, Done, Archive)
ktui column list
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
# View all tasks and their status
ktui task list

# View tasks in JSON format for parsing
ktui task list --json

# View only tasks in a specific column
ktui task list --column COLUMN_ID
```

## Best Practices

### Task Management
1. **Create Specific Tasks**: Break complex work into clear, actionable items
2. **Use Descriptions**: Add context about what needs to be done, markdown is supported
3. **One Active Task**: Keep only 1-2 tasks in Doing column at a time
4. **Immediate Updates**: Move tasks as soon as status changes
5. **Complete First**: Finish current tasks before starting new ones

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
ktui column list  # Get column IDs

# Plan tasks
ktui task create "Design authentication flow" --column 5
ktui task create "Implement login endpoint" --column 5
ktui task create "Add JWT token generation" --column 5
ktui task create "Write auth middleware" --column 5
ktui task create "Add tests for auth flow" --column 5

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

# Work through systematically
ktui task list  # Check status regularly
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
| List tasks | `ktui task list` |
| List tasks (JSON) | `ktui task list --json` |
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
