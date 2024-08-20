from typing import Iterable

from textual.widget import Widget
from textual.containers import Horizontal

from kanban_tui.widgets.task_column import ReadyColumn, DoingColumn, DoneColumn
from kanban_tui.widgets.task_card import TaskCard


class KanbanBoard(Horizontal):
    def compose(self) -> Iterable[Widget]:
        yield ReadyColumn()
        yield DoingColumn()
        yield DoneColumn()
        return super().compose()

    def key_space(self):
        self.query_one(ReadyColumn).place_task(TaskCard(title="test"))
