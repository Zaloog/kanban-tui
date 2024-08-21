from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Task:
    title: str
    column: int
    creation_date: datetime = datetime.now().strftime(format="%d/%m/%Y, %H:%M:%S")
    start_date: datetime | None = None
    finish_date: datetime | None = None
    duration: int | None = None
    finished: bool = False
    category: str | None = None
    due_date: datetime | None = None
    days_left: int | None = None
    description: str | None = None

    def __post_init__(self):
        if self.due_date:
            self.days_left = self.get_days_left_till_due()
        if self.finish_date:
            self.duration = self.get_duration()

    def get_days_left_till_due(self):
        return min(
            0,
            (self.due_date - datetime.now().strftime(format="%d/%m/%Y, %H:%M:%S"))
            / timedelta(days=1),
        )

    def get_duration(self):
        return (self.finish_date - self.start_date) / timedelta(hours=1)

    def finish(self):
        self.finished = True
        self.finish_date = datetime.now().strftime(format="%d/%m/%Y, %H:%M:%S")
        self.duration = self.get_duration()
