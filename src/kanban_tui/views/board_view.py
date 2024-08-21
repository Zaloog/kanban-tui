from typing import Iterable

from textual import on
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Horizontal

from kanban_tui.widgets.task_column import Column
from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.views.task_view import TaskEditScreen

from kanban_tui.constants import COLUMNS


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
        self.app.push_screen(TaskEditScreen())
        # self.query_one("#column_ready", Column).task_amount += 1
        # ta = self.query_one("#column_ready", Column).task_amount
        # card = TaskCard(title=f"Task {ta}", row=ta - 1, column=0)
        # self.query_one("#column_ready", Column).query_one(VerticalScroll).mount(card)

    def key_j(self):
        column = self.query(Column)[self.position[1]]
        row = (self.position[0] + 1) % column.task_amount

        column.query(TaskCard)[row].focus()

    def key_k(self):
        column = self.query(Column)[self.position[1]]
        row = (self.position[0] + column.task_amount - 1) % column.task_amount

        column.query(TaskCard)[row].focus()

    def key_l(self):
        row = self.position[0]
        column = self.query(Column)[(self.position[1] + 1) % len(COLUMNS)]

        try:
            column.query(TaskCard)[row].focus()
        except IndexError:
            column.query(TaskCard)[column.task_amount - 1].focus()

    def key_h(self):
        row = self.position[0]
        column = self.query(Column)[(self.position[1] + 2) % len(COLUMNS)]

        try:
            column.query(TaskCard)[row].focus()
        except IndexError:
            column.query(TaskCard)[column.task_amount - 1].focus()

    @on(TaskCard.Focused)
    def get_current_card_position(self, event: TaskCard.Focused):
        self.position = event.taskcard.position

    def watch_position(self):
        self.log.error(self.position)
