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
