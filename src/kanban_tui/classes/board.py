from datetime import datetime

from pydantic import BaseModel


class Board(BaseModel):
    board_id: int
    name: str
    icon: str | None = None
    creation_date: datetime = datetime.now().replace(microsecond=0)
