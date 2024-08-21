from datetime import datetime
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Select, Label, Switch
from textual.widgets._select import SelectOverlay
from textual.containers import Horizontal, Vertical

from kanban_tui.classes.task import Task


class TaskEditScreen(ModalScreen):
    app: "KanbanTui"

    BINDINGS = [Binding("escape", "app.popscreen", "Close")]

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
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_due_date"):
            yield Label("has a due Date:")
            yield Switch(value=False)
        with Horizontal(id="horizontal_category"):
            yield Label("Category:")
            yield CategorySelector(
                prompt="select Category",
                allow_blank=True,
                options=[
                    (f"[on {color}]{category}[/]", category)
                    for category, color in self.app.cfg.category_color_dict.items()
                ],
            )

        self.border = "$success"
        self.border_title = "Additional Infos"
        return super().compose()


class CategorySelector(Select):
    # thanks Darren (https://github.com/darrenburns/posting/blob/main/src/posting/widgets/select.py)
    BINDINGS = [
        Binding("enter,space,l", "show_overlay", "Show Overlay", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]

    def action_cursor_up(self):
        if self.expanded:
            self.query_one(SelectOverlay).action_cursor_up()
        else:
            self.screen.focus_previous()

    def action_cursor_down(self):
        if self.expanded:
            self.query_one(SelectOverlay).action_cursor_down()
        else:
            self.screen.focus_next()


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
