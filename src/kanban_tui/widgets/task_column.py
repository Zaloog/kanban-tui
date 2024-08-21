from typing import Iterable


from textual.events import Mount
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import VerticalScroll, Vertical

from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.constants import COLUMN_DICT


class Column(Vertical):
    task_amount: reactive[int] = reactive(0)
    task_list: reactive[list] = reactive([])

    def __init__(self, title: str) -> None:
        self.title = title
        super().__init__(id=f"column_{title.lower()}")

    def compose(self) -> Iterable[Widget]:
        yield Label(self.title, id=f"label_{self.title}")
        yield VerticalScroll(id=f"taskplace{self.title}")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one(f"#taskplace{self.title}", VerticalScroll).can_focus = False
        for _ in range(5):
            self.task_amount += 1
            card = TaskCard(
                title=f"Task {self.task_amount}",
                row=self.task_amount - 1,
                column=COLUMN_DICT[self.title],
            )
            self.query_one(VerticalScroll).mount(card)
        return super()._on_mount(event)

    def watch_task_amount(self) -> None:
        if self.task_amount == 0:
            self.get_child_by_type(Label).update(self.title)
        elif self.task_amount == 1:
            self.get_child_by_type(Label).update(f"{self.title} (1 Task)")
        else:
            self.get_child_by_type(Label).update(
                f"{self.title} ({self.task_amount} Tasks)"
            )
