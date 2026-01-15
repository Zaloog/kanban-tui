from datetime import datetime, timedelta

from pydantic import BaseModel, computed_field


class Task(BaseModel):
    task_id: int
    title: str
    column: int
    creation_date: datetime = datetime.now().replace(microsecond=0)
    start_date: datetime | None = None
    finish_date: datetime | None = None
    category: int | None = None
    due_date: datetime | None = None
    description: str | None = None

    def get_days_since_creation(self) -> int:
        return (
            datetime.now().replace(microsecond=0) - self.creation_date
        ) // timedelta(days=1)  # + 1

    def get_days_left_till_due(self) -> int | None:
        if self.due_date:
            return max(
                0,
                (self.due_date - datetime.now().replace(microsecond=0))
                // timedelta(days=1)
                + 1,
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
                # only can finish properly if start column was previous column
                if self.column == update_column_dict["start"]:
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
