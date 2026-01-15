from pydantic import BaseModel


class Column(BaseModel):
    column_id: int
    name: str
    visible: bool
    position: int
    board_id: int
