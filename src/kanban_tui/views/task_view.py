from typing import Iterable
from datetime import datetime

from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Select, Label, Switch
from textual.containers import Horizontal, Vertical

from kanban_tui.classes.task import Task


class TaskEditScreen(ModalScreen):
    BINDINGS = [("escape", "app.popscreen", "Close")]

    def __init__(self, task: Task | None = None) -> None:
        self.kanban_task = task
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Create New Task", id="label_header")
            yield Input(placeholder="enter a Task Title")
            yield CreationDateInfo()
            with Horizontal(id="horizontal_dates"):
                yield StartDateInfo()
                yield FinishDateInfo()
            with Horizontal(id="horizontal_detail"):
                yield DescriptionInfos()
                yield DetailInfos()
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
        self.dismiss()

    @on(Button.Pressed, "#btn_cancel")
    def close_window(self):
        self.dismiss()


class DescriptionInfos(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield TextArea()
        self.border = "$success"
        self.border_title = "Task Description"
        return super().compose()


class DetailInfos(Vertical):
    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_due_date"):
            yield Label("has a due Date:")
            yield Switch(value=False)
        with Horizontal(id="horizontal_category"):
            yield Label("Category:")
            yield Select(prompt="select Category", options=[])

        self.border = "$success"
        self.border_title = "Additional Infos"
        return super().compose()


class CreationDateInfo(Horizontal):
    def compose(self) -> Iterable[Widget]:
        yield Label(
            f'Task created at: {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}',
            id="label-start_date",
        )
        self.border = "$success"
        self.border_title = "Creation Date"
        return super().compose()


class StartDateInfo(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Label("Started:")
        yield Label("[red]not started yet[/]", id="label-start_date")
        self.border = "$success"
        self.border_title = "Start Date"
        return super().compose()


class FinishDateInfo(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Label("Finished:")
        yield Label("[red]not finished yet[/]", id="label_finish_date")
        self.border = "$success"
        self.border_title = "Finish Date"
        return super().compose()
