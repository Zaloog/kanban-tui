from datetime import datetime
from typing import Iterable, TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.reactive import reactive
from textual.events import Blur, Focus, Mount
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Select, Label, Switch
from textual.widgets._select import SelectOverlay
from textual.containers import Horizontal, Vertical

from kanban_tui.classes.task import Task
from kanban_tui.database import create_new_task_db


class TaskEditScreen(ModalScreen):
    app: "KanbanTui"

    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, task: Task | None = None) -> None:
        self.kanban_task = task
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label("Create New Task", id="label_header")
            yield Input(placeholder="enter a Task Title", id="input_title")
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
        title = self.query_one(Input).value
        description = self.query_one(TextArea).text
        category = (
            None if self.query_one(Select).is_blank() else self.query_one(Select).value
        )
        due_date = None

        create_new_task_db(
            title=title,
            description=description,
            category=category,
            due_date=due_date,
            database=self.app.cfg.database_path,
        )

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
        with Horizontal(id="horizontal_due_date"):
            yield Label("has a due Date:")
            yield Switch(value=False)
        yield DueDateInput()

        self.border = "$success"
        self.border_title = "Additional Infos"
        return super().compose()

    def on_switch_changed(self):
        if self.query_one(Switch).value:
            self.query_one(DueDateInput).remove_class("hidden")
        else:
            self.query_one(DueDateInput).add_class("hidden")


class YearInput(Input):
    def __init__(
        self,
        value: int = f"{datetime.now().year}",
        placeholder: str = "YYYY",
        type: Literal["integer"] | Literal["number"] | Literal["text"] = "number",
        max_length: int = 4,
        # validators: Validator | Iterable[Validator] | None = None,
        # validate_on: Iterable[Literal['blur'] | Literal['changed'] | Literal['submitted']] | None = 'changed',
        valid_empty: bool = False,
        id: str | None = "input_year",
    ) -> None:
        super().__init__(
            value,
            placeholder,
            type=type,
            max_length=max_length,
            #  validators=validators,
            #  validate_on=validate_on,
            valid_empty=valid_empty,
            id=id,
        )


class MonthInput(Input):
    def __init__(
        self,
        value: int | None = None,
        placeholder: str = "MM",
        type: Literal["integer"] | Literal["number"] | Literal["text"] = "number",
        max_length: int = 2,
        # validators: Validator | Iterable[Validator] | None = None,
        # validate_on: Iterable[Literal['blur'] | Literal['changed'] | Literal['submitted']] | None = 'changed',
        valid_empty: bool = False,
        id: str | None = "input_month",
    ) -> None:
        super().__init__(
            value,
            placeholder,
            type=type,
            max_length=max_length,
            #  validators=validators,
            #  validate_on=validate_on,
            valid_empty=valid_empty,
            id=id,
        )

    def _on_focus(self, event: Focus) -> None:
        self.clear()
        return super()._on_focus(event)

    def _on_blur(self, event: Blur) -> None:
        if self.value:
            if len(self.value) < 2:
                self.value = f"0{self.value}"
        return super()._on_blur(event)

    def _watch_value(self, value: str) -> None:
        if value:
            if int(value) > 1:
                if len(self.value) < 2:
                    self.value = f"0{self.value}"
                else:
                    self.app.action_focus_next()
        return super()._watch_value(value)


class DayInput(Input):
    def __init__(
        self,
        value: int | None = None,
        placeholder: str = "DD",
        type: Literal["integer"] | Literal["number"] | Literal["text"] = "number",
        max_length: int = 2,
        # validators: Validator | Iterable[Validator] | None = None,
        # validate_on: Iterable[Literal['blur'] | Literal['changed'] | Literal['submitted']] | None = 'changed',
        valid_empty: bool = False,
        id: str | None = "input_day",
    ) -> None:
        super().__init__(
            value,
            placeholder,
            type=type,
            max_length=max_length,
            #  validators=validators,
            #  validate_on=validate_on,
            valid_empty=valid_empty,
            id=id,
        )

    def _on_focus(self, event: Focus) -> None:
        self.clear()
        return super()._on_focus(event)

    def _on_blur(self, event: Blur) -> None:
        if self.value:
            if len(self.value) < 2:
                self.value = f"0{self.value}"
        return super()._on_blur(event)

    def _watch_value(self, value: str) -> None:
        if value:
            if int(value) > 3:
                if len(self.value) < 2:
                    self.value = f"0{self.value}"
                else:
                    self.app.action_focus_next()
        return super()._watch_value(value)


class DueDateInput(Vertical):
    due_date: reactive

    def __init__(self, classes: str | None = "hidden") -> None:
        super().__init__(classes=classes)

    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_due_date_days_left"):
            yield Label("[yellow]??[/] days left", id="label_days_left")
        with Horizontal(id="horizontal_due_date_input"):
            yield YearInput()
            yield Label("/")
            yield MonthInput()
            yield Label("/")
            yield DayInput()
        return super().compose()

    @on(Input.Changed)
    def calculate_days_left(self):
        try:
            year = int(self.query_one(YearInput).value)
            month = int(self.query_one(MonthInput).value)
            day = int(self.query_one(DayInput).value)

            self.due_date = datetime(year=year, month=month, day=day).replace(
                microsecond=0
            )
            delta = (self.due_date - datetime.now()).days
            self.query_one("#label_days_left", Label).update(
                f"[green]{delta}[/] days left"
            )
        except Exception:
            self.query_one("#label_days_left", Label).update("[yellow]??[/] days left")


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
