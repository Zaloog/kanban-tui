from datetime import datetime

from pydantic import BaseModel


class Board(BaseModel):
    board_id: int
    name: str
    icon: str = ""
    creation_date: datetime = datetime.now().replace(microsecond=0)
    reset_column: int | None = None
    start_column: int | None = None
    finish_column: int | None = None

    def to_json(self) -> str:
        return self.model_dump_json(indent=4, exclude_none=True, ensure_ascii=True)

    @property
    def full_name(self):
        return f"{self.icon} {self.name}"
