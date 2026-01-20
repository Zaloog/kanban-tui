PRAGMA foreign_keys = OFF;

CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_on DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS  dependencies (
    dependency_id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    CHECK (task_id != depends_on_task_id),
    UNIQUE(task_id, depends_on_task_id)
);

-- Alter boards table to add ON DELETE SET NULL for status columns
-- Create new boards table with proper constraints
CREATE TABLE IF NOT EXISTS boards_new (
    board_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    creation_date DATETIME NOT NULL,
    reset_column INTEGER DEFAULT NULL,
    start_column INTEGER DEFAULT NULL,
    finish_column INTEGER DEFAULT NULL,
    FOREIGN KEY (reset_column) REFERENCES columns(column_id) ON DELETE SET NULL,
    FOREIGN KEY (start_column) REFERENCES columns(column_id) ON DELETE SET NULL,
    FOREIGN KEY (finish_column) REFERENCES columns(column_id) ON DELETE SET NULL,
    CHECK (name <> "")
);

-- Copy existing data
INSERT INTO boards_new SELECT * FROM boards;

-- Drop old table (this also drops the triggers)
DROP TABLE boards;

-- Rename new table
ALTER TABLE boards_new RENAME TO boards;

-- Recreate triggers for boards table
CREATE TRIGGER board_creation
AFTER INSERT on boards
FOR EACH ROW
BEGIN
    INSERT into audits (
        event_timestamp,
        event_type,
        object_type,
        object_id
        )
    VALUES (
        datetime('now'),
        'CREATE',
        'board',
        NEW.board_id
    );
END;

CREATE TRIGGER board_deletion
AFTER DELETE on boards
FOR EACH ROW
BEGIN
    INSERT into audits (
        event_timestamp,
        event_type,
        object_type,
        object_id
        )
    VALUES (
        datetime('now'),
        'DELETE',
        'board',
        OLD.board_id
    );
END;

PRAGMA foreign_keys_check;

PRAGMA foreign_keys = ON;

CREATE TRIGGER board_update
AFTER UPDATE on boards
FOR EACH ROW
BEGIN
    INSERT into audits (
        event_timestamp,
        event_type,
        object_type,
        object_id,
        object_field,
        value_old,
        value_new
        )
    SELECT
        datetime('now'),
        'UPDATE',
        'board',
        OLD.board_id,
        'name',
        OLD.name,
        NEW.name
    WHERE OLD.name IS NOT NEW.name;

    INSERT into audits (
        event_timestamp,
        event_type,
        object_type,
        object_id,
        object_field,
        value_old,
        value_new
        )
    SELECT
        datetime('now'),
        'UPDATE',
        'board',
        OLD.board_id,
        'icon',
        OLD.icon,
        NEW.icon
    WHERE OLD.icon IS NOT NEW.icon;

    INSERT into audits (
        event_timestamp,
        event_type,
        object_type,
        object_id,
        object_field,
        value_old,
        value_new
        )
    SELECT
        datetime('now'),
        'UPDATE',
        'board',
        OLD.board_id,
        'reset_column',
        OLD.reset_column,
        NEW.reset_column
    WHERE OLD.reset_column IS NOT NEW.reset_column;

    INSERT into audits (
        event_timestamp,
        event_type,
        object_type,
        object_id,
        object_field,
        value_old,
        value_new
        )
    SELECT
        datetime('now'),
        'UPDATE',
        'board',
        OLD.board_id,
        'start_column',
        OLD.start_column,
        NEW.start_column
    WHERE OLD.start_column IS NOT NEW.start_column;

    INSERT into audits (
        event_timestamp,
        event_type,
        object_type,
        object_id,
        object_field,
        value_old,
        value_new
        )
    SELECT
        datetime('now'),
        'UPDATE',
        'board',
        OLD.board_id,
        'finish_column',
        OLD.finish_column,
        NEW.finish_column
    WHERE OLD.finish_column IS NOT NEW.finish_column;
END;
