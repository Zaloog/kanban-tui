from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import VerticalScroll, Vertical

from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.classes.task import Task


class Column(Vertical):
    app: "KanbanTui"
    task_amount: reactive[int] = reactive(0)
    task_list: list[Task]

    def __init__(
        self, title: str, id_num: int, task_list: list[Task] | None = None
    ) -> None:
        self.title = title
        self.task_list = task_list or []
        super().__init__(id=f"column_{id_num}")
        self.can_focus: bool = False
        self.styles.width = f"{1 / self.app.config.board.columns_in_view * 100:.2f}%"

    def compose(self) -> Iterable[Widget]:
        yield Label(Text.from_markup(self.title), id=f"label_{self.id}")
        yield VerticalScroll(id=f"vscroll_{self.id}", can_focus=False)

    async def on_mount(self) -> None:
        for task in self.task_list:
            await self.place_task(task=task)
        self.border_title = "move task here"

    def watch_task_amount(self) -> None:
        column_label = self.get_child_by_type(Label)
        match self.task_amount:
            case 0:
                column_label.update(Text.from_markup(self.title))
            case 1:
                column_label.update(Text.from_markup(f"{self.title} (1 Task)"))
            case _:
                column_label.update(
                    Text.from_markup(f"{self.title} ({self.task_amount} Tasks)")
                )

    async def place_task(self, task: Task) -> None:
        card = TaskCard(
            task=task,
            row=self.task_amount,
        )
        await self.query_one(VerticalScroll).mount(card)
        self.task_amount += 1

    async def remove_task(self, task: Task) -> None:
        await self.query_one(f"#taskcard_{task.task_id}", TaskCard).remove()
        self.task_amount -= 1

        # Update row attribute of other TaskCards
        for row_position, task_card in enumerate(self.query(TaskCard)):
            task_card.row = row_position
