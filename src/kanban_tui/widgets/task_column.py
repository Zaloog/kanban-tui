from typing import Iterable

from rich.text import Text
from textual.events import Mount
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import VerticalScroll, Vertical

from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.classes.task import Task


class Column(Vertical):
    task_amount: reactive[int] = reactive(0)
    task_list: reactive[list[Task]] = reactive([])

    def __init__(self, title: str, id_num: int, tasklist: list[Task] = []) -> None:
        self.title = title
        super().__init__(id=f"column_{id_num}")
        self.task_list = tasklist
        self.can_focus: bool = False

    def compose(self) -> Iterable[Widget]:
        yield Label(Text.from_markup(self.title), id=f"label_{self.id}")
        yield VerticalScroll(id=f"vscroll_{self.id}")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one(f"#vscroll_{self.id}", VerticalScroll).can_focus = False
        for task in self.task_list:
            self.place_task(task=task)
        return super()._on_mount(event)

    def watch_task_amount(self) -> None:
        if self.task_amount == 0:
            self.get_child_by_type(Label).update(Text.from_markup(self.title))
        elif self.task_amount == 1:
            self.get_child_by_type(Label).update(
                Text.from_markup(f"{self.title} (1 Task)")
            )
        else:
            self.get_child_by_type(Label).update(
                Text.from_markup(f"{self.title} ({self.task_amount} Tasks)")
            )

    def place_task(self, task: Task) -> None:
        card = TaskCard(
            task=task,
            row=self.task_amount,
        )
        self.task_amount += 1
        self.query_one(VerticalScroll).mount(card)

    async def remove_task(self, task: Task) -> None:
        self.task_amount -= 1
        await self.query_one(f"#taskcard_{task.task_id}", TaskCard).remove()

        for idx, task_card in enumerate(self.query(TaskCard)):
            task_card.row = idx
