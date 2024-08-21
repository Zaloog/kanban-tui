from typing import Iterable

from textual import on
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Horizontal, VerticalScroll

from kanban_tui.widgets.task_column import Column
from kanban_tui.widgets.task_card import TaskCard


class KanbanBoard(Horizontal):
    BINDINGS = [
        ("space", "place_task", "new task")
        # ("shift+j", "reposition_task",)
    ]

    row_focused: reactive[int | None] = reactive(None)
    column_focused: reactive[int | None] = reactive(None)
    position: reactive[tuple[int]] = reactive((0, 0))

    def compose(self) -> Iterable[Widget]:
        for column in ["Ready", "Doing", "Done"]:
            yield Column(title=column)
        return super().compose()

    def action_place_task(self, task: TaskCard | None = None) -> None:
        ta = self.query_one("#column_ready", Column).task_amount
        self.query_one("#column_ready", Column).task_amount += 1
        card = TaskCard(title=f"Task {ta}", row=ta, column=1)
        self.query_one("#column_ready", Column).query_one(VerticalScroll).mount(card)

    def key_j(self):
        self.app.action_focus_next()

    def key_k(self):
        self.app.action_focus_previous()

    def key_l(self):
        for task in self.query(TaskCard):
            if task.position == (self.position[0], self.position[1] + 1):
                task.focus()

    @on(TaskCard.Focused)
    def get_current_card_position(self, event: TaskCard.Focused):
        self.position = event.taskcard.position

    def watch_position(self):
        self.log.error(self.position)
