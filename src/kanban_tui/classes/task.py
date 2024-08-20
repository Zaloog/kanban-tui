from dataclasses import dataclass
from datetime import datetime


@dataclass
class Task:
    title: str
    start_date: datetime = datetime.now().strftime(format="%d/%m/%Y, %H:%M:%S")
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

    def get_days_left_till_due(self):
        return (
            self.due_date - datetime.now().strftime(format="%d/%m/%Y, %H:%M:%S")
        ).days

    def finish_task(self):
        self.finished = True
        self.finish_date = datetime.now().strftime(format="%d/%m/%Y, %H:%M:%S")
