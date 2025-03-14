from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.utils import StatusEnum

from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: int
    title: str
    column: int
    creation_date: datetime = datetime.now().replace(microsecond=0)
    days_since_creation: int = Field(default=0, ge=0)
    start_date: datetime | None = None
    finish_date: datetime | None = None
    time_worked_on: int = Field(default=0, ge=0)
    finished: bool = False
    category: str | None = None
    due_date: datetime | None = None
    days_left: int | None = None
    description: str | None = None

    def model_post_init(self, __context):
        self.days_since_creation = self.get_days_since_creation()
        if self.due_date:
            self.days_left = self.get_days_left_till_due()

        if self.finish_date:
            self.finished = True

    def get_days_since_creation(self) -> int:
        return (
            datetime.now().replace(microsecond=0) - self.creation_date
        ) // timedelta(days=1)  # + 1

    def get_days_left_till_due(self):
        if self.due_date:
            return max(
                0,
                (self.due_date - datetime.now().replace(microsecond=0))
                // timedelta(days=1)
                + 1,
            )
        return None

    def update_time_worked_on(self):
        """get duration in hours from start till finish of task"""
        self.time_worked_on += (self.finish_date - self.start_date) // timedelta(
            minutes=1
        ) + 1

    def reset_task(self):
        self.start_date = None
        self.finish_date = None

    def start_task(self):
        self.start_date = datetime.now().replace(microsecond=0)
        self.finish_date = None

    def finish_task(self):
        self.finished = True
        self.finish_date = datetime.now().replace(microsecond=0)
        self.update_time_worked_on()

    def update_task_status(self, new_column: int, update_column_enum: "StatusEnum"):
        """Update Dates on Task Move

        Args:
            new_column (int): Column where the task moved to
        """
        match new_column:
            # Move to Ready
            case update_column_enum.RESET.value:
                self.reset_task()
            # Move to 'Doing'
            case update_column_enum.START.value:
                self.start_task()
            # Move to 'Done'
            case update_column_enum.FINISH.value:
                if self.column == update_column_enum.START.value:
                    self.finish_task()
