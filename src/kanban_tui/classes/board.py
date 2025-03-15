from datetime import datetime

from pydantic import BaseModel


class Board(BaseModel):
    board_id: int
    name: str
    icon: str | None = None
    creation_date: datetime = datetime.now().replace(microsecond=0)
    reset_column: int | None = None
    start_column: int | None = None
    finish_column: int | None = None

    @property
    def full_name(self):
        return f"{self.icon} {self.name}"
