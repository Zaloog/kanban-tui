---
name: kanban-tui
description: Task management with dependency tracking for Claude agents. Use for complex multi-step tasks (>5 steps OR task dependencies exist). User can explicitly request with "kanban"/"ktui". DEFAULT to TodoWrite for simple linear tasks (<5 steps, no dependencies). Requires ktui CLI.
---

# Kanban-TUI Agent Skill

## Quick Decision: Which Tool?

```
User mentioned "kanban"/"ktui"? → YES → Use kanban-tui
                ↓ NO
Task has >5 sequential steps? → YES → Use kanban-tui
                ↓ NO
Subtasks depend on each other? → YES → Use kanban-tui
                ↓ NO
Work spans multiple sessions? → YES → Use kanban-tui (persistent board)
                ↓ NO
Simple linear task (<5 steps)? → YES → Use TodoWrite (default)
```

### When to Choose: Comparison

| Scenario | Tool | Why |
|----------|------|-----|
| Fix single bug (3 steps) | TodoWrite | Simple, linear, no dependencies |
| Implement feature (8 steps with dependencies) | kanban-tui | Complex, dependencies needed |
| Refactor across 10+ files | kanban-tui | Long-running, checkpoint tracking |
| Add error handling to one function | TodoWrite | Single concern, fast |
| Build authentication system | kanban-tui | Multi-component, sequential deps |
| Update documentation | TodoWrite | Single file, straightforward |
| Multi-session project work | kanban-tui | Persistent board across sessions |

## Quick Start for Agents

```bash
# SETUP (run once per task/project)
ktui board create "Feature Name" --icon ":rocket:" --set-active

# Extract column IDs (REQUIRED - board-specific)
READY=$(ktui column list --json | jq -r '.[] | select(.name=="Ready") | .column_id')
DOING=$(ktui column list --json | jq -r '.[] | select(.name=="Doing") | .column_id')
DONE=$(ktui column list --json | jq -r '.[] | select(.name=="Done") | .column_id')

# Create tasks with dependencies
ktui task create "Design schema" --column $READY                     # Returns task_id=1
ktui task create "Implement models" --depends-on 1 --column $READY  # Returns task_id=2
ktui task create "Create API" --depends-on 2 --column $READY        # Returns task_id=3

# WORK LOOP (automated dependency handling)
while true; do
  # Get next unblocked task
  NEXT=$(ktui task list --actionable --json | jq -r '.[0] | .task_id')
  [ "$NEXT" = "null" ] && break

  # Execute task
  ktui task move $NEXT $DOING
  # === DO THE ACTUAL WORK HERE ===
  ktui task move $NEXT $DONE
done
```

## Critical Rules

1. **NEVER launch interactive TUI** - CLI only (use --help, --json, --no-confirm flags)
2. **Column IDs are board-specific** - Re-extract after EVERY board switch/creation
3. **Task IDs are globally unique** - Same task_id works across all boards
4. **Default to --json with jq** - Fallback to text parsing if jq unavailable
5. **Keep 1 task in Doing at a time** - Complete before starting next
6. **Use --actionable flag** - Auto-filters blocked tasks
7. **Mark Done immediately** - Don't batch completions

## Core Commands Reference

```bash
# Board Management
ktui board create "Name" --icon ":emoji:" --set-active  # Create + activate
ktui board list [--json]                                # List all boards
ktui board activate <board_id>                          # Switch active board

# Column Operations (board-specific IDs)
ktui column list [--json] [--board]                              # List columns for active board

# Task Operations
ktui task create "Title" --column <col_id> [--description "Details"] [--depends-on <task_id>]
ktui task list [--json] [--actionable]                  # --actionable = unblocked only
ktui task move <task_id> <col_id> [--force]            # Move task between columns
ktui task update <task_id> --title "New" [--description "Details"]
ktui task delete <task_id> --no-confirm                # Delete without prompt
```

## Column ID Rules (Board-Specific)

**Critical concept:** Column IDs are local to each board, NOT global.

```
Board "Frontend" (ID: 1)          Board "Backend" (ID: 2)
  ├─ Ready (column_id: 5)           ├─ Ready (column_id: 9)   ← Different ID!
  ├─ Doing (column_id: 6)           ├─ Doing (column_id: 10)
  └─ Done  (column_id: 7)           └─ Done  (column_id: 11)
```

**MUST re-extract column IDs after:**
- Creating new board with `--set-active`
- Running `ktui board activate <board_id>`
- Any board switch operation

### ID Extraction Pattern

```bash
# With jq (preferred)
READY=$(ktui column list --json | jq -r '.[] | select(.name=="Ready") | .column_id')
DOING=$(ktui column list --json | jq -r '.[] | select(.name=="Doing") | .column_id')
DONE=$(ktui column list --json | jq -r '.[] | select(.name=="Done") | .column_id')

# Without jq (fallback)
READY=$(ktui column list | grep "Ready" | sed 's/.*ID: \([0-9]*\).*/\1/')
DOING=$(ktui column list | grep "Doing" | sed 's/.*ID: \([0-9]*\).*/\1/')
DONE=$(ktui column list | grep "Done" | sed 's/.*ID: \([0-9]*\).*/\1/')

# Validate extraction
if [ -z "$READY" ] || [ -z "$DOING" ] || [ -z "$DONE" ]; then
  echo "ERROR: Column ID extraction failed" >&2
  exit 1
fi
```

## Task JSON Structure

```json
{
  "task_id": 1,           // Globally unique
  "title": "Task title",
  "column": 5,            // Board-specific column ID
  "description": "...",
  "blocked_by": [2, 3],   // Tasks that must complete first
  "blocking": [4, 5],     // Tasks waiting on this one
  "is_blocked": true,     // Can this task start now?
  "has_dependents": true, // Will completing this unblock others?
  "finished": false       // In Done/Archive column?
}
```

## State Extraction Patterns

```bash
# Get active board ID
BOARD_ID=$(ktui board list --json | jq -r '.[] | select(.active==true) | .board_id')

# Get next actionable task
NEXT=$(ktui task list --actionable --json | jq -r '.[0] | .task_id')

# Check if specific task is blocked
IS_BLOCKED=$(ktui task list --json | jq -r '.[] | select(.task_id==5) | .is_blocked')

# Get tasks blocking task 5
BLOCKERS=$(ktui task list --json | jq -r '.[] | select(.task_id==5) | .blocked_by[]')

# Verify active board name
ktui board list --json | jq -r '.[] | select(.active==true) | .name'
```

## Task Naming Standards

**Use imperative mood (command form):**

✅ GOOD:
- "Implement OAuth login"
- "Fix memory leak in parser"
- "Add unit tests for UserService"
- "Refactor database connection pool"

❌ BAD:
- "OAuth" (noun, not actionable)
- "Working on tests" (status description)
- "The parser issue" (vague)
- "Fix stuff" (not specific)

**Break large tasks into dependency chains:**

Instead of: "Implement entire authentication system"

Create chain:
1. "Design auth database schema" (no deps)
2. "Implement User model" (depends on 1)
3. "Create auth API endpoints" (depends on 2)
4. "Add JWT token handling" (depends on 3)
5. "Write auth integration tests" (depends on 4)

## Standard Agent Workflow

### 1. Setup Phase

```bash
# Create/activate board
ktui board create "Feature: User Authentication" --icon ":lock:" --set-active

# Extract column IDs
READY=$(ktui column list --json | jq -r '.[] | select(.name=="Ready") | .column_id')
DOING=$(ktui column list --json | jq -r '.[] | select(.name=="Doing") | .column_id')
DONE=$(ktui column list --json | jq -r '.[] | select(.name=="Done") | .column_id')

# Validate
[ -z "$READY" ] && echo "ERROR: Column extraction failed" && exit 1
```

### 2. Task Creation Phase

```bash
# Parallel tasks (no dependencies)
ktui task create "Setup test environment" --column $READY
ktui task create "Create user fixtures" --column $READY

# Sequential dependency chain
ktui task create "Design schema" --column $READY                      # task_id=1
ktui task create "Implement models" --depends-on 1 --column $READY   # task_id=2
ktui task create "Create endpoints" --depends-on 2 --column $READY   # task_id=3
ktui task create "Add validation" --depends-on 3 --column $READY     # task_id=4
ktui task create "Write tests" --depends-on 4 --column $READY        # task_id=5
```

### 3. Execution Loop

```bash
while true; do
  # Get next unblocked task (--actionable filters automatically)
  NEXT=$(ktui task list --actionable --json | jq -r '.[0] | .task_id')

  # Exit when no tasks remain
  [ "$NEXT" = "null" ] && break

  # Move to Doing (only 1 task in Doing at a time)
  ktui task move $NEXT $DOING

  # === PERFORM ACTUAL WORK ===
  # - Read files, write code, run tests
  # - Only proceed to Done when 100% complete

  # Move to Done (immediately after completion)
  ktui task move $NEXT $DONE

  # Completion automatically unblocks dependent tasks
done

# Inform user
echo "All tasks completed successfully"
```

## Error Handling

### Command Not Found

```bash
# Try ktui directly
if ! command -v ktui &> /dev/null; then
  # Try uvx wrapper
  if command -v uvx &> /dev/null; then
    alias ktui="uvx kanban-tui"
  else
    # Inform user and fallback
    echo "kanban-tui not available. Install: pipx install kanban-tui"
    echo "Falling back to TodoWrite for this session."
    exit 1
  fi
fi
```

### Column Not Found

```bash
# Symptom: "Error: Column ID X does not exist"
# Cause: Wrong board active OR stale column IDs
# Fix: Re-extract column IDs
READY=$(ktui column list --json | jq -r '.[] | select(.name=="Ready") | .column_id')

# Verify correct board is active
ktui board list --json | jq -r '.[] | select(.active==true) | .name'
```

### Task Blocked

```bash
# Symptom: "Error: Task X is blocked by tasks [Y, Z]"
# Option 1: Complete blocking tasks first (PREFERRED)
BLOCKERS=$(ktui task list --json | jq -r '.[] | select(.task_id==5) | .blocked_by[]')
# Work through blockers sequentially

# Option 2: Use --force (ONLY with user authorization)
# Inform user: "Task 5 blocked by tasks [2, 3]. User approved --force override."
ktui task move 5 $DOING --force
```

### jq Not Available

```bash
if ! command -v jq &> /dev/null; then
  # Use text parsing fallback
  READY=$(ktui column list | grep "Ready" | sed 's/.*ID: \([0-9]*\).*/\1/')

  # Or inform user
  echo "Recommend installing jq for better parsing:"
  echo "  macOS: brew install jq"
  echo "  Linux: apt install jq"
fi
```

## Validation Checkpoints

### After Board Creation/Switch

```bash
# Re-extract column IDs (MANDATORY)
READY=$(ktui column list --json | jq -r '.[] | select(.name=="Ready") | .column_id')
DOING=$(ktui column list --json | jq -r '.[] | select(.name=="Doing") | .column_id')
DONE=$(ktui column list --json | jq -r '.[] | select(.name=="Done") | .column_id')

# Verify active board
ACTIVE=$(ktui board list --json | jq -r '.[] | select(.active==true) | .name')
echo "Active board: $ACTIVE"
```

### Before Task Move

```bash
# If not using --actionable, check blocked status
IS_BLOCKED=$(ktui task list --json | jq -r '.[] | select(.task_id==5) | .is_blocked')

if [ "$IS_BLOCKED" = "true" ]; then
  BLOCKERS=$(ktui task list --json | jq -r '.[] | select(.task_id==5) | .blocked_by[]')
  echo "Task 5 blocked by: $BLOCKERS"
  # Complete blockers first OR get user approval for --force
fi
```

### Before Marking Done

**Only mark Done when:**
- Implementation is 100% complete
- Tests pass (if applicable)
- No errors or warnings
- Task requirements fully met

**If incomplete:**
- Keep in Doing
- Inform user of blockers/issues
- NEVER mark Done prematurely

## Force Flag Protocol

### NEVER use --force to:
- Skip prerequisite work
- Hide dependency problems
- Rush through incomplete tasks

### ONLY use --force when:
- User explicitly authorizes: "User approved --force for task 5"
- Blocking task deleted/obsolete: "Task 3 deleted, unblocking task 5"
- Documented reason: "Design changed, old blocker no longer relevant"

### When using --force, ALWAYS:
1. Inform user which task was force-moved
2. List what blocked it (task IDs/titles)
3. Explain why override was necessary
4. Ask user if uncertain

## User Communication

### Inform User When:
- Board created/switched (name, column count)
- Task blocked by dependencies (list blocking task IDs)
- Using --force flag (explain reason)
- Error encountered (provide fix steps)
- All tasks completed (summary)
- ktui unavailable (installation instructions)

### Work Silently When:
- Moving tasks between columns (routine ops)
- Extracting IDs (internal state)
- Validating state (automated checks)

### Never:
- Hide errors to "keep working"
- Mark incomplete tasks as Done
- Use --force without justification
- Create vague task names

## Anti-Patterns

❌ **Caching column IDs across boards** - IDs are board-specific
❌ **Hardcoding IDs** - `ktui task move 5 7` (unmaintainable)
❌ **Skipping validation** - Always check command success
❌ **Batch completing tasks** - Mark Done immediately after completion
❌ **Vague task titles** - Must be specific and actionable
❌ **Launching interactive TUI** - Use CLI flags only
❌ **Multiple tasks in Doing** - Complete current task first

## Quick Troubleshooting

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| "Column not found" | Wrong board active or stale IDs | `ktui column list --json \| jq ...` |
| "Task is blocked" | Dependencies not complete | Check: `jq '.[] \| select(.task_id==X) \| .blocked_by'` |
| "Board not active" | No active board set | `ktui board activate <board_id>` |
| "Command not found" | ktui not installed | Try `uvx kanban-tui` or inform user |
| JSON parse fails | Missing --json flag | Add --json, check jq installed |
| Tasks not showing | Wrong board active | Verify: `ktui board list --json` |

## Success Indicators

Commands return exit codes:
- **0** = Success
- **Non-zero** = Error (check stderr)

Always check exit codes for critical operations:
```bash
if ! ktui task move 5 $DONE; then
  echo "Failed to move task 5 to Done" >&2
  # Diagnose: Is it blocked? Wrong column ID? Wrong board?
  IS_BLOCKED=$(ktui task list --json | jq -r '.[] | select(.task_id==5) | .is_blocked')
  echo "Task blocked: $IS_BLOCKED"
fi
```

## Complete Example: Feature Implementation

```bash
# 1. SETUP
ktui board create "Feature: API Rate Limiting" --icon ":stopwatch:" --set-active
READY=$(ktui column list --json | jq -r '.[] | select(.name=="Ready") | .column_id')
DOING=$(ktui column list --json | jq -r '.[] | select(.name=="Doing") | .column_id')
DONE=$(ktui column list --json | jq -r '.[] | select(.name=="Done") | .column_id')

# 2. CREATE TASK CHAIN
ktui task create "Design rate limit config schema" --column $READY                    # ID: 1
ktui task create "Implement RateLimiter middleware" --depends-on 1 --column $READY   # ID: 2
ktui task create "Add Redis caching for limits" --depends-on 2 --column $READY       # ID: 3
ktui task create "Create rate limit API endpoints" --depends-on 3 --column $READY    # ID: 4
ktui task create "Write integration tests" --depends-on 4 --column $READY            # ID: 5
ktui task create "Update API documentation" --depends-on 5 --column $READY           # ID: 6

# 3. EXECUTE (automatic dependency handling)
while true; do
  NEXT=$(ktui task list --actionable --json | jq -r '.[0] | .task_id')
  [ "$NEXT" = "null" ] && break

  ktui task move $NEXT $DOING
  # Agent performs implementation work here
  ktui task move $NEXT $DONE
done

echo "Feature complete: API Rate Limiting (6 tasks)"
```

## Summary

1. **Choose Tool**: Use kanban-tui for >5 steps OR dependencies; TodoWrite for simple tasks
2. **Setup**: Create board → Extract column IDs → Validate
3. **Plan**: Create tasks with imperative titles + dependencies
4. **Execute**: Loop through --actionable tasks → Doing → Work → Done
5. **Validate**: Re-extract IDs after board switches, check exit codes
6. **Communicate**: Inform user at checkpoints, explain --force usage
7. **Persist**: Board survives across sessions for long-running work

**Benefits over TodoWrite:**
- Dependency tracking prevents ordering errors
- Persistent state across sessions
- Automatic blocking/unblocking
- Better for complex multi-step implementations

<!-- Version: KANBAN_TUI_VERSION -->
