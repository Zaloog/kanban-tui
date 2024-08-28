from typing import Iterable, TYPE_CHECKING


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Select, Label
from textual.containers import Horizontal, Vertical

from kanban_tui.classes.task import Task
from kanban_tui.database import create_new_task_db
from kanban_tui.widgets.modal_task_widgets import (
    CreationDateInfo,
    StartDateInfo,
    FinishDateInfo,
    DetailInfos,
    DescriptionInfos,
)


class TaskEditScreen(ModalScreen):
    app: "KanbanTui"

    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, task: Task | None = None) -> None:
        self.kanban_task = task
        super().__init__(id="test_modal")

    def compose(self) -> Iterable[Widget]:
        with Vertical(id="vertical_modal"):
            yield Label("Create New Task", id="label_header")
            yield Input(placeholder="enter a Task Title", id="input_title")
            yield CreationDateInfo()
            with Horizontal(id="horizontal_dates"):
                yield StartDateInfo()
                yield FinishDateInfo()
            with Horizontal(id="horizontal_detail"):
                yield DescriptionInfos()
                yield DetailInfos(id="detail_infos")
            with Horizontal(id="horizontal_buttons"):
                yield Button("Create Task", id="btn_continue", variant="success")
                yield Button("Cancel", id="btn_cancel", variant="error")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        if self.kanban_task:
            ...
        return super()._on_mount(event)

    @on(Button.Pressed, "#btn_continue")
    def update_task(self):
        title = self.query_one("#input_title", Input).value
        description = self.query_one(TextArea).text
        category = (
            None if self.query_one(Select).is_blank() else self.query_one(Select).value
        )
        due_date = (
            self.query_one(DetailInfos).due_date.isoformat(sep=" ", timespec="seconds")
            if self.query_one(DetailInfos).due_date
            else None
        )

        create_new_task_db(
            title=title,
            description=description,
            column=self.app.cfg.start_column,
            category=category,
            due_date=due_date,
            database=self.app.cfg.database_path,
        )

        self.app.update_task_list()
        self.dismiss(result=self.app.task_list[-1])

    @on(Button.Pressed, "#btn_cancel")
    def close_window(self):
        self.app.pop_screen()  # .dismiss()
