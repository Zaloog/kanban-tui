from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field, computed_field


class Task(BaseModel):
    task_id: int
    title: str
    column: int
    creation_date: datetime
    start_date: datetime | None = None
    finish_date: datetime | None = None
    category: int | None = None
    due_date: datetime | None = None
    description: str = ""
    blocked_by: list[int] = []  # Task IDs this task depends on
    blocking: list[int] = []  # Task IDs that depend on this task
    metadata: dict[str, Any] = Field(default_factory=dict)  # Backend-specific extras

    def get_days_since_creation(self) -> int:
        now = datetime.now().replace(microsecond=0)
        # Handle both timezone-aware and naive datetimes
        creation = (
            self.creation_date.replace(tzinfo=None)
            if self.creation_date.tzinfo
            else self.creation_date
        )
        return (now - creation) // timedelta(days=1)  # + 1

    def get_days_left_till_due(self) -> int | None:
        if self.due_date:
            now = datetime.now().replace(microsecond=0)
            # Handle both timezone-aware and naive datetimes
            due = (
                self.due_date.replace(tzinfo=None)
                if self.due_date.tzinfo
                else self.due_date
            )
            return max(
                0,
                (due - now) // timedelta(days=1) + 1,
            )
        return None

    def reset_task(self):
        self.start_date = None
        self.finish_date = None

    def start_task(self):
        self.start_date = datetime.now().replace(microsecond=0)
        self.finish_date = None

    def finish_task(self):
        # if the start_column is set while the task
        # is inside it already, the creation_date will be taken
        # as the start date, when attempting to finish the task
        if not self.start_date:
            self.start_date = self.creation_date
        self.finish_date = datetime.now().replace(microsecond=0)

    def update_task_status(
        self, new_column: int, update_column_dict: dict[str, int | None]
    ):
        """Update Dates on Task Move

        Args:
            new_column (int): Column where the task moved to
        """
        match new_column:
            # Move to Ready
            case new_column if new_column == update_column_dict["reset"]:
                self.reset_task()
            # Move to 'Doing'
            case new_column if new_column == update_column_dict["start"]:
                self.start_task()
            # Move to 'Done'
            case new_column if new_column == update_column_dict["finish"]:
                # Mark task as finished when moving to finish column
                self.finish_task()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days_left(self) -> int | None:
        return self.get_days_left_till_due()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def days_since_creation(self) -> int:
        return self.get_days_since_creation()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def finished(self) -> bool:
        return bool(self.finish_date)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_blocked(self) -> bool:
        """Returns True if this task has any dependencies (regardless of their status)."""
        return len(self.blocked_by) > 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_dependents(self) -> bool:
        """Returns True if any other tasks depend on this one."""
        return len(self.blocking) > 0

    def can_move_to_column(
        self, target_column: int, start_column: int | None, backend
    ) -> tuple[bool, str]:
        """Check if task can move to target column based on dependencies.

        Args:
            target_column: Column where the task wants to move to
            start_column: The board's start column (e.g., "Doing")
            backend: Backend instance to fetch dependency task details

        Returns:
            (can_move, reason): Boolean and message explaining why/why not
        """
        # Only enforce blocking if moving to the start column and it's configured
        if start_column is None or target_column != start_column:
            return True, "OK"

        # Check if any blocking tasks are unfinished
        if not self.blocked_by:
            return True, "OK"

        # Fetch all dependency tasks in a single query to avoid N+1 queries
        dependency_tasks = backend.get_tasks_by_ids(self.blocked_by)
        unfinished_tasks = [t for t in dependency_tasks if not t.finished]

        if unfinished_tasks:
            task_titles = ", ".join(
                f"#{t.task_id} '{t.title}'" for t in unfinished_tasks
            )
            return False, f"Task is blocked by unfinished dependencies: {task_titles}"

        return True, "OK"

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key with optional default.

        Args:
            key: Metadata key to retrieve
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value by key.

        Args:
            key: Metadata key to set
            value: Value to store
        """
        self.metadata[key] = value

    @property
    def jira_key(self) -> str | None:
        """Get Jira issue key from metadata (e.g., 'KTUI-123')."""
        return self.get_metadata("jira_key")

    @property
    def assignee(self) -> str | None:
        """Get task assignee from metadata (Jira-specific)."""
        return self.get_metadata("assignee")
