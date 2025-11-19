from pydantic import BaseModel


class Category(BaseModel):
    category_id: int
    name: str
    color: str
