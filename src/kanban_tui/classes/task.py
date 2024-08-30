from datetime import datetime, timedelta

from pydantic import BaseModel


# @dataclass
class Task(BaseModel):
    title: str
    column: int
    creation_date: datetime = datetime.now().replace(microsecond=0)
    start_date: datetime | None = None
    finish_date: datetime | None = None
    duration: int | None = None
    finished: bool = False
    category: str | None = None
    due_date: datetime | None = None
    days_left: int | None = None
    description: str | None = None
    task_id: int | None = None

    def __post_init__(self):
        if self.due_date:
            self.due_date = datetime.strptime(
                self.due_date, "%Y-%m-%d %H:%M:%S"
            ).replace(microsecond=0)
            self.get_days_left_till_due()

        if self.finish_date:
            self.finished = True
            self.get_duration()

    def get_days_left_till_due(self):
        self.days_left = max(
            0,
            (self.due_date - datetime.now().replace(microsecond=0)) // timedelta(days=1)
            + 1,
        )

    def get_duration(self):
        """get duration in hours from start till finish of task"""
        self.duration = (self.finish_date - self.start_date) / timedelta(hours=1)

    def start_task(self):
        self.start_date = datetime.now().replace(microsecond=0)

    def finish_task(self):
        self.finished = True
        self.finish_date = datetime.now().replace(microsecond=0)
        self.get_duration()

    def update_task_status(self, new_column: int):
        match new_column:
            case 1:
                self.start_task()
            case 2:
                self.finish_task()
