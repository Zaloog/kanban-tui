from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Task:
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
            self.days_left = self.get_days_left_till_due()
        if self.finish_date:
            self.duration = self.get_duration()

    def get_days_left_till_due(self):
        due_date = datetime.strptime(self.due_date, "%Y-%m-%d %H:%M:%S").replace(
            microsecond=0
        )
        return max(
            0,
            (due_date - datetime.now().replace(microsecond=0)) // timedelta(days=1) + 1,
        )

    def get_duration(self):
        return (self.finish_date - self.start_date) / timedelta(hours=1)

    def finish(self):
        self.finished = True
        self.finish_date = datetime.now().replace(microsecond=0)
        self.duration = self.get_duration()
