from typing import Iterable, TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from collections import defaultdict

from textual import on
from textual.binding import Binding
from textual.events import Mount
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Horizontal

from kanban_tui.widgets.task_column import Column
from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.modal.modal_task_screen import TaskEditScreen
from kanban_tui.database import get_all_tasks_db, update_task_column_db
from kanban_tui.constants import COLUMNS

from kanban_tui.classes.task import Task


class KanbanBoard(Horizontal):
    app: "KanbanTui"
    can_focus: bool = True

    BINDINGS = [
        Binding("space, n", "new_task", "New", priority=True, show=True),
        Binding("j,down", "movement('down')", "Down", show=False),
        Binding("k, up", "movement('up')", "Up", show=False),
        Binding("h, left", "movement('left')", "Left", show=False),
        Binding("l, right", "movement('right')", "Right", show=False),
    ]
    position: reactive[tuple[int]] = reactive((0, 0))
    task_dict: reactive[defaultdict[list]] = reactive(defaultdict(list), recompose=True)

    def _on_mount(self, event: Mount) -> None:
        self.update_task_dict(needs_update=True)
        self.focus()
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        for idx, column_name in enumerate(COLUMNS):
            yield Column(title=column_name, tasklist=self.task_dict[idx])
        return super().compose()

    def action_new_task(self) -> None:
        self.app.push_screen(TaskEditScreen(), callback=self.update_task_dict)

    def action_edit_task(self, task: TaskCard | None = None) -> None:
        self.app.push_screen(TaskEditScreen(task=task))

    # Movement
    def action_movement(self, direction: Literal["up", "right", "down", "left"]):
        match direction:
            case "up":
                try:
                    column = self.query(Column)[self.position[1]]
                    row = (
                        self.position[0] + column.task_amount - 1
                    ) % column.task_amount
                    column.query(TaskCard)[row].focus()
                except ZeroDivisionError:
                    self.app.action_focus_previous()
            case "down":
                try:
                    column = self.query(Column)[self.position[1]]
                    row = (self.position[0] + 1) % column.task_amount
                    column.query(TaskCard)[row].focus()
                except ZeroDivisionError:
                    self.app.action_focus_next()
            case "right":
                row = self.position[0]
                column = self.query(Column)[(self.position[1] + 1) % len(COLUMNS)]
                try:
                    column.query(TaskCard)[row].focus()
                except IndexError:
                    column.query(TaskCard)[column.task_amount - 1].focus()
            case "left":
                row = self.position[0]
                column = self.query(Column)[(self.position[1] + 2) % len(COLUMNS)]
                try:
                    column.query(TaskCard)[row].focus()
                except IndexError:
                    column.query(TaskCard)[column.task_amount - 1].focus()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "movement":
            if (parameters[0] == "right") and (
                self.query(Column)[(self.position[1] + 1) % len(COLUMNS)].task_amount
                == 0
            ):
                return False
            if (parameters[0] == "left") and (
                self.query(Column)[(self.position[1] + 2) % len(COLUMNS)].task_amount
                == 0
            ):
                return False
        return super().check_action(action, parameters)

    @on(TaskCard.Focused)
    def get_current_card_position(self, event: TaskCard.Focused):
        self.position = event.taskcard.position

    @on(TaskCard.Moved)
    def move_card_to_other_column(self, event: TaskCard.Moved):
        task_id = event.taskcard.task_.task_id
        if event.direction == "left":
            new_column = (self.position[1] + 2) % len(COLUMNS)
        elif event.direction == "right":
            new_column = (self.position[1] + 1) % len(COLUMNS)

        update_task_column_db(task_id=task_id, column=new_column)
        self.update_task_dict(needs_update=True)

        # Ugly
        self.set_timer(
            delay=0.10, callback=self.query_one(f"#taskcard_{task_id}", TaskCard).focus
        )
        # self.query_one(f"#taskcard_{task_id}", TaskCard).focus()

        # self.position = (0, new_column)

    def update_task_dict(self, needs_update: bool = False):
        if needs_update:
            self.task_dict.clear()
            tasks = get_all_tasks_db(database=self.app.cfg.database_path)
            for task in tasks:
                self.task_dict[task["column"]].append(Task(**task))
            self.mutate_reactive(KanbanBoard.task_dict)

    def watch_position(self):
        # get task for infos, if edit with 'e'
        # self.selected_task =
        self.log.error(self.position)

    def watch_task_dict(self): ...
