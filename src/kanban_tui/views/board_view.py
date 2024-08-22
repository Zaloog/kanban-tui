from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from collections import defaultdict

from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Horizontal

from kanban_tui.widgets.task_column import Column
from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.modal.modal_task_screen import TaskEditScreen
from kanban_tui.database import get_all_tasks_db
from kanban_tui.constants import COLUMN_DICT

from kanban_tui.classes.task import Task


class KanbanBoard(Horizontal):
    app: "KanbanTui"
    BINDINGS = [
        ("n", "new_task", "New"),
        ("e", "edit_task", "Edit"),
        # ("shift+j", "reposition_task",)
    ]

    row_focused: reactive[int | None] = reactive(None)
    column_focused: reactive[int | None] = reactive(None)
    position: reactive[tuple[int]] = reactive((0, 0))
    task_dict: reactive[defaultdict[list]] = reactive(defaultdict(list), recompose=True)

    def _on_mount(self, event: Mount) -> None:
        tasks = get_all_tasks_db(database=self.app.cfg.database_path)
        for task in tasks:
            self.task_dict[task["column"]].append(Task(**task))
        self.mutate_reactive(KanbanBoard.task_dict)
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        self.log.error(self.task_dict)
        for column_name, idx in COLUMN_DICT.items():
            yield Column(title=column_name, tasklist=self.task_dict[idx])
        return super().compose()

    def action_new_task(self) -> None:
        self.app.push_screen(TaskEditScreen())

    def action_edit_task(self, task: TaskCard | None = None) -> None:
        self.app.push_screen(TaskEditScreen(task=task))

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
        column = self.query(Column)[(self.position[1] + 1) % len(COLUMN_DICT)]
        try:
            column.query(TaskCard)[row].focus()
        except IndexError:
            column.query(TaskCard)[column.task_amount - 1].focus()

    def key_h(self):
        row = self.position[0]
        column = self.query(Column)[(self.position[1] + 2) % len(COLUMN_DICT)]
        try:
            column.query(TaskCard)[row].focus()
        except IndexError:
            column.query(TaskCard)[column.task_amount - 1].focus()

    @on(TaskCard.Focused)
    def get_current_card_position(self, event: TaskCard.Focused):
        self.position = event.taskcard.position

    def watch_position(self):
        # self.selected_task =
        self.log.error(self.position)

    def watch_task_dict(self): ...
