from pydantic import BaseModel


class Column(BaseModel):
    column_id: int
    name: str
    visible: bool
    position: int
    board_id: int

    def to_json(self) -> str:
        return self.model_dump_json(indent=4, exclude_none=True, ensure_ascii=True)
