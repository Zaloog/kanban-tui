from __future__ import annotations
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.reactive import reactive
from textual.binding import Binding
from textual.events import Enter, Leave, Mount, Click
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Markdown
from textual.message import Message

from kanban_tui.classes.task import Task
from kanban_tui.modal.modal_task_screen import (
    ModalTaskEditScreen,
    ModalTaskDeleteScreen,
)


class TaskCard(Vertical):
    app: "KanbanTui"
    expanded: reactive[bool] = reactive(False)
    BINDINGS = [
        Binding("H", "move_task('left')", "<-", show=True, key_display="shift-h"),
        Binding("e", "edit_task", "Edit", show=True),
        Binding("d", "delete_task", "Delete", show=True),
        Binding("L", "move_task('right')", "->", show=True, key_display="shift-l"),
    ]

    class Focused(Message):
        def __init__(self, taskcard: TaskCard) -> None:
            self.taskcard = taskcard
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    class Moved(Message):
        # TODO M
        def __init__(self, taskcard: TaskCard, new_column: str) -> None:
            self.taskcard = taskcard
            self.new_column = new_column
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    class Delete(Message):
        def __init__(self, taskcard: TaskCard) -> None:
            self.taskcard = taskcard
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    def __init__(
        self,
        task: Task,
        row: int,
    ) -> None:
        self.task_ = task
        self.row = row

        self.can_focus = True
        self.can_focus_children = False
        super().__init__(id=f"taskcard_{self.task_.task_id}")

    def _on_mount(self, event: Mount) -> None:
        if self.app.cfg.tasks_always_expanded:
            self.query_one(Markdown).remove_class("hidden")

        return super()._on_mount(event)

    def compose(self) -> ComposeResult:
        self.styles.background = self.app.cfg.category_color_dict.get(
            self.task_.category, self.app.cfg.no_category_task_color
        )
        self.border_title = self.task_.title
        match self.task_.days_left:
            case 0:
                self.border_subtitle = (
                    f":hourglass_done: {self.task_.days_left} days left"
                )
            case 1:
                self.border_subtitle = f":hourglass_not_done: {self.task_.days_left} day left :face_screaming_in_fear:"
            case None:
                self.border_subtitle = ""
            case _:
                self.border_subtitle = (
                    f":hourglass_not_done: {self.task_.days_left} days left"
                )

        yield Label(self.task_.title)
        yield Markdown(
            markdown=self.task_.description,
        )
        return super().compose()

    @on(Enter)
    @on(Leave)
    def show_details(self) -> None:
        if self.is_mouse_over:
            self.focus()
        else:
            self.parent.focus()

    def on_focus(self) -> None:
        self.expanded = True
        self.post_message(self.Focused(taskcard=self))

    def on_blur(self) -> None:
        self.expanded = False

    def watch_expanded(self):
        if self.expanded:
            self.query_one(Label).add_class("hidden")
            self.query_one(Markdown).remove_class("hidden")
        else:
            self.query_one(Label).remove_class("hidden")
            if not self.app.cfg.tasks_always_expanded:
                self.query_one(Markdown).add_class("hidden")

    def action_move_task(self, direction: Literal["left", "right"]):
        match direction:
            case "left":
                if self.app.cfg.visible_columns[0] == self.task_.column:
                    return
                new_column = self.app.cfg.visible_columns[
                    self.app.cfg.visible_columns.index(self.task_.column) - 1
                ]
            case "right":
                if self.app.cfg.visible_columns[-1] == self.task_.column:
                    return
                new_column = self.app.cfg.visible_columns[
                    self.app.cfg.visible_columns.index(self.task_.column) + 1
                ]

        self.task_.update_task_status(new_column=new_column)
        self.post_message(self.Moved(taskcard=self, new_column=new_column))

    @on(Click)
    def action_edit_task(self) -> None:
        self.app.push_screen(
            ModalTaskEditScreen(task=self.task_), callback=self.from_modal_update_task
        )

    def from_modal_update_task(self, updated_task: Task) -> None:
        self.task_ = updated_task
        self.refresh(recompose=True)

    def action_delete_task(self) -> None:
        self.app.push_screen(
            ModalTaskDeleteScreen(task=self.task_), callback=self.from_modal_delete_task
        )

    def from_modal_delete_task(self, delete_yn: bool) -> None:
        if delete_yn:
            self.post_message(self.Delete(taskcard=self))
