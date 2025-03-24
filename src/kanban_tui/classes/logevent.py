from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LogEvent(BaseModel):
    event_id: int
    event_timestamp: datetime
    event_type: Literal["CREATE", "UPDATE", "DELETE"] | None = None
    object_type: Literal["task", "board", "column"] | None = None
    object_id: int | None = None
    object_field: str | None = None
    value_old: str | None = None
    value_new: str | None = None
