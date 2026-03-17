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
        await self.replace_tasks(self.task_list)
        self.border_title = "move task here"

    def set_title(self, title: str) -> None:
        self.title = title
        self.watch_task_amount()

    def sync_width(self) -> None:
        self.styles.width = f"{1 / self.app.config.board.columns_in_view * 100:.2f}%"

    def get_rendered_cards(self) -> list[TaskCard]:
        return list(self.query(TaskCard).results())

    def watch_task_amount(self) -> None:
        labels = list(self.query(Label).results()) if self.is_mounted else []
        if not labels:
            return
        column_label = labels[0]
        match self.task_amount:
            case 0:
                column_label.update(Text.from_markup(self.title))
            case 1:
                column_label.update(Text.from_markup(f"{self.title} (1 Task)"))
            case _:
                column_label.update(
                    Text.from_markup(f"{self.title} ({self.task_amount} Tasks)")
                )

    async def place_task(self, task: Task, target_position: int | None = None) -> None:
        scroll = self.query_one(VerticalScroll)
        row = (
            self.task_amount
            if target_position is None
            else max(0, min(target_position, self.task_amount))
        )

        task.position = row
        card = TaskCard(task=task, row=row)
        if row == self.task_amount:
            await scroll.mount(card)
            self.task_amount += 1
        else:
            await scroll.mount(card, before=row)
            self.task_amount += 1
            # Keep row and in-memory task.position aligned with rendered order.
            for row_position, task_card in enumerate(self.query(TaskCard)):
                task_card.row = row_position
                task_card.task_.position = row_position

    async def replace_tasks(self, task_list: list[Task]) -> None:
        scroll = self.query_one(VerticalScroll)
        await scroll.remove_children()

        cards: list[TaskCard] = []
        for row_position, task in enumerate(task_list):
            task.position = row_position
            cards.append(TaskCard(task=task, row=row_position))

        if cards:
            await scroll.mount(*cards)

        self.task_list = task_list
        self.task_amount = len(task_list)

    async def sync_tasks(self, task_list: list[Task]) -> None:
        existing_cards = self.get_rendered_cards()
        existing_ids = [task_card.task_.task_id for task_card in existing_cards]
        desired_ids = [task.task_id for task in task_list]

        if desired_ids == existing_ids:
            self._update_existing_cards(existing_cards, task_list)
            return

        if self._is_subsequence(desired_ids, existing_ids):
            desired_id_set = set(desired_ids)
            for task_card in existing_cards:
                if task_card.task_.task_id not in desired_id_set:
                    await task_card.remove()

            task_cards_by_id = {
                task_card.task_.task_id: task_card
                for task_card in self.get_rendered_cards()
            }
            ordered_cards = [task_cards_by_id[task.task_id] for task in task_list]
            self._update_existing_cards(ordered_cards, task_list)
            return

        if existing_ids == desired_ids[: len(existing_ids)]:
            scroll = self.query_one(VerticalScroll)
            new_cards: list[TaskCard] = []
            for row_position, task in enumerate(
                task_list[len(existing_ids) :], start=len(existing_ids)
            ):
                task.position = row_position
                new_cards.append(TaskCard(task=task, row=row_position))

            if new_cards:
                await scroll.mount(*new_cards)

            self._update_existing_cards(existing_cards + new_cards, task_list)
            return

        await self.replace_tasks(task_list)

    def _update_existing_cards(
        self, task_cards: list[TaskCard], task_list: list[Task]
    ) -> None:
        for row_position, (task_card, task) in enumerate(zip(task_cards, task_list)):
            task.position = row_position
            if task_card.task_ != task:
                task_card.task_ = task
                task_card.refresh(recompose=True)
            task_card.row = row_position
            task_card.task_.position = row_position

        self.task_list = task_list
        self.task_amount = len(task_list)

    def _is_subsequence(self, subset_ids: list[int], full_ids: list[int]) -> bool:
        subset_index = 0
        for task_id in full_ids:
            if subset_index < len(subset_ids) and subset_ids[subset_index] == task_id:
                subset_index += 1
        return subset_index == len(subset_ids)

    async def remove_task(self, task: Task) -> None:
        await self.query_one(f"#taskcard_{task.task_id}", TaskCard).remove()
        self.task_amount -= 1

        # Update row attribute of other TaskCards
        for row_position, task_card in enumerate(self.query(TaskCard)):
            task_card.row = row_position
            task_card.task_.position = row_position
