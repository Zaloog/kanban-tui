from typing import Iterable

from textual.widget import Widget
from textual.containers import Horizontal

from kanban_tui.widgets.task_column import ReadyColumn, DoingColumn, DoneColumn


class KanbanBoard(Horizontal):
    def compose(self) -> Iterable[Widget]:
        yield ReadyColumn()
        yield DoingColumn()
        yield DoneColumn()
        return super().compose()
