-- Migration v0.19.0: Add position field to tasks table
ALTER TABLE tasks ADD COLUMN position INTEGER NOT NULL DEFAULT 0;

-- Backfill positions per column (0-based order by task_id)
WITH ranked AS (
    SELECT
        task_id,
        ROW_NUMBER() OVER (PARTITION BY "column" ORDER BY task_id) - 1 AS pos
    FROM tasks
)
UPDATE tasks
SET position = (SELECT pos FROM ranked WHERE ranked.task_id = tasks.task_id);
