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
from kanban_tui.widgets.filter_sidebar import FilterOverlay
from kanban_tui.database import get_all_tasks_db, update_task_column_db
from kanban_tui.constants import COLUMNS

from kanban_tui.classes.task import Task


class KanbanBoard(Horizontal):
    app: "KanbanTui"

    BINDINGS = [
        Binding("n", "new_task", "New", priority=True, show=True),
        Binding("j,down", "movement('down')", "Down", show=False),
        Binding("k, up", "movement('up')", "Up", show=False),
        Binding("h, left", "movement('left')", "Left", show=False),
        Binding("l, right", "movement('right')", "Right", show=False),
        Binding("f1", "toggle_filter", "Filter", key_display="F1"),
    ]
    position: reactive[tuple[int]] = reactive((0, 0), init=False)
    task_dict: reactive[defaultdict[list]] = reactive(
        defaultdict(list), recompose=True, init=False
    )
    selected_task: reactive[Task | None] = reactive(None, init=False)

    def _on_mount(self, event: Mount) -> None:
        self.update_task_dict(needs_update=True)

        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        for idx, column_name in enumerate(COLUMNS):
            yield Column(title=column_name, tasklist=self.task_dict[idx])
        yield FilterOverlay(task_list=self.task_dict.values())
        return super().compose()

    def action_new_task(self) -> None:
        self.app.push_screen(TaskEditScreen(), callback=self.update_task_dict)

    def action_edit_task(self, task: TaskCard | None = None) -> None:
        self.app.push_screen(TaskEditScreen(task=task))

    # Movement
    def action_movement(self, direction: Literal["up", "right", "down", "left"]):
        current_column = self.query(Column)[self.selected_task.column]
        row_idx = self.query_one(
            f"#taskcard_{self.selected_task.task_id}", TaskCard
        ).row
        match direction:
            case "up":
                try:
                    new_row_idx = (
                        row_idx + current_column.task_amount - 1
                    ) % current_column.task_amount
                    current_column.query(TaskCard)[new_row_idx].focus()
                except ZeroDivisionError:
                    self.app.action_focus_previous()
            case "down":
                try:
                    new_row_idx = (row_idx + 1) % current_column.task_amount
                    current_column.query(TaskCard)[new_row_idx].focus()
                except ZeroDivisionError:
                    self.app.action_focus_next()
            case "right":
                try:
                    new_column = self.query(Column)[
                        (self.selected_task.column + 1) % len(COLUMNS)
                    ]
                    new_column.query(TaskCard)[row_idx].focus()
                except IndexError:
                    new_column.query(TaskCard)[new_column.task_amount - 1].focus()
            case "left":
                try:
                    new_column = self.query(Column)[
                        (self.selected_task.column + 2) % len(COLUMNS)
                    ]
                    new_column.query(TaskCard)[row_idx].focus()
                except IndexError:
                    new_column.query(TaskCard)[new_column.task_amount - 1].focus()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "movement":
            if (parameters[0] == "right") and (
                self.query(Column)[
                    (self.selected_task.column + 1) % len(COLUMNS)
                ].task_amount
                == 0
            ):
                return False
            if (parameters[0] == "left") and (
                self.query(Column)[
                    (self.selected_task.column + 2) % len(COLUMNS)
                ].task_amount
                == 0
            ):
                return False
        return super().check_action(action, parameters)

    @on(TaskCard.Focused)
    def get_current_card_position(self, event: TaskCard.Focused):
        self.selected_task = event.taskcard.task_

    @on(TaskCard.Moved)
    def move_card_to_other_column(self, event: TaskCard.Moved):
        if event.direction == "left":
            new_column = (self.selected_task.column + 2) % len(COLUMNS)
        elif event.direction == "right":
            new_column = (self.selected_task.column + 1) % len(COLUMNS)

        update_task_column_db(task_id=self.selected_task.task_id, column=new_column)
        self.update_task_dict(needs_update=True)
        # self.query_one(f'#taskcard_{self.selected_task.task_id}').remove()
        # self.query(Column)[new_column].place_task(self.selected_task)

    def update_task_dict(self, needs_update: bool = False):
        if needs_update:
            self.task_dict.clear()
            tasks = get_all_tasks_db(database=self.app.cfg.database_path)
            for task in tasks:
                self.task_dict[task["column"]].append(Task(**task))
            self.mutate_reactive(KanbanBoard.task_dict)

    def watch_task_dict(self):
        # Make it smooth when starting without any Tasks
        if not self.task_dict:
            self.can_focus = True
            self.notify(
                title="Welcome to Kanban Tui",
                message="Looks like you are new, press [blue]<space>[/] to create your first Card",
            )
        else:
            self.can_focus = False
            if self.selected_task:
                self.set_timer(
                    delay=0.01,
                    callback=lambda: self.query_one(
                        f"#taskcard_{self.selected_task.task_id}", TaskCard
                    ).focus(),
                )

    def action_toggle_filter(self) -> None:
        filter = self.query_one(FilterOverlay)
        if filter.has_class("-hidden"):
            self.query(TaskCard).set(disabled=True)

            filter.can_focus_children = True
            # Focus the first Widget on Filter
            filter.query_one("#category_filter").focus()
            filter.remove_class("-hidden")
        else:
            self.query(TaskCard).set(disabled=False)
            filter.can_focus_children = False
            if self.selected_task:
                self.query_one(
                    f"#taskcard_{self.selected_task.task_id}", TaskCard
                ).focus()
            else:
                self.app.action_focus_next()

            filter.add_class("-hidden")
