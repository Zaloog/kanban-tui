from typing import Any, Iterable, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Select, Label, Switch, Footer
from textual.containers import Vertical, VerticalScroll

from kanban_tui.textual_datepicker import DateSelect
from kanban_tui.classes.task import Task
from kanban_tui.widgets.modal_task_widgets import (
    TaskAdditionalInfos,
    TaskDueDateSelector,
    TaskTitleInput,
    CategorySelector,
    TaskDescription,
    TaskDependencyManager,
)
from kanban_tui.widgets.custom_widgets import ButtonRow


class ModalTaskEditScreen(ModalScreen[Task | None]):
    app: "KanbanTui"

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("ctrl+j", "update_task", "Save/Edit Task", priority=True),
    ]

    def __init__(self, task: Task | None = None, *args, **kwargs) -> None:
        self.kanban_task = task
        super().__init__(*args, **kwargs)

    def compose(self) -> Iterable[Widget]:
        with Vertical(id="vertical_modal"):
            with VerticalScroll(can_focus=False):
                yield TaskTitleInput()
                yield TaskDescription(classes="task-field")
                yield TaskAdditionalInfos()
                # Only show dependency manager when editing existing task
                if self.kanban_task is not None:
                    yield TaskDependencyManager(
                        current_task_id=self.kanban_task.task_id, classes="task-field"
                    )
            yield ButtonRow(id="horizontal_buttons")
            yield Footer()

    def on_mount(self, event: Mount) -> None:
        self.query_one("#vertical_modal", Vertical).border_title = "Create Task"
        if self.kanban_task is not None:
            self.query_one("#vertical_modal", Vertical).border_title = "Edit Task"
            self.read_values_from_task()
            self.query_one("#btn_continue", Button).label = "Edit Task"
            self.query_one("#btn_continue", Button).disabled = False
            self.watch(
                self.query_one(TaskAdditionalInfos).query_one(CategorySelector),
                "value",
                self.update_description_background,
            )

    @on(Input.Changed, "#input_title")
    def disable_continue_button(self, event: Input.Changed):
        if event.validation_result:
            self.query_one(
                "#btn_continue", Button
            ).disabled = not event.validation_result.is_valid
        # if event.validation_result:

    @on(Button.Pressed, "#btn_continue")
    def action_update_task(self):
        title = self.query_one("#input_title", Input).value
        if not title:
            return
        # Read from Textarea cause TaskDescription.text mightve
        # not been updated when using shortcut
        description = self.query_one(TextArea).text
        category = (
            None
            if self.query_one(CategorySelector).is_blank()
            else self.query_one(CategorySelector).value
        )
        due_date = (
            self.query_one(TaskDueDateSelector).due_date.isoformat(
                sep=" ", timespec="seconds"
            )
            if self.query_one(TaskDueDateSelector).due_date
            else None
        )

        # create new task
        if not self.kanban_task:
            new_task = self.app.backend.create_new_task(
                title=title,
                description=description,
                column=next(iter(self.app.visible_column_dict)),
                category=category,
                due_date=due_date,
            )

            self.app.update_task_list()
            self.dismiss(result=new_task)

        else:
            self.kanban_task.title = title
            self.kanban_task.due_date = (
                datetime.fromisoformat(due_date) if due_date else None
            )

            self.kanban_task.description = description
            self.kanban_task.category = category

            updated_task = self.app.backend.update_task_entry(
                task_id=self.kanban_task.task_id,
                title=self.kanban_task.title,
                description=self.kanban_task.description,
                category=self.kanban_task.category,
                due_date=self.kanban_task.due_date,
            )
            self.dismiss(result=updated_task)

    @on(Button.Pressed, "#btn_cancel")
    def close_window(self):
        self.app.pop_screen()

    def update_description_background(self, category_id: int | Any):
        text_area = self.query_one(TaskDescription).editor
        text_preview = self.query_one(TaskDescription).preview
        if category_id not in (CategorySelector.BLANK, CategorySelector.NEW):
            category = self.app.backend.get_category_by_id(category_id)
            category_color = category.color
            text_area.styles.background = category_color
            text_preview.styles.background = category_color
        else:
            text_area.styles.background = self.app.config.task.default_color
            text_preview.styles.background = self.app.config.task.default_color
        text_area.styles.background = text_area.styles.background.darken(0.2)
        text_preview.styles.background = text_preview.styles.background.darken(0.2)

    def read_values_from_task(self):
        self.query_one("#input_title", Input).value = self.kanban_task.title
        self.query_one(TaskDescription).text = self.kanban_task.description

        if category_id := self.kanban_task.category:
            self.update_description_background(category_id=category_id)

        self.query_one(Select).value = (
            self.kanban_task.category if self.kanban_task.category else Select.BLANK
        )
        self.query_one("#label_create_date", Label).update(
            f"{self.kanban_task.creation_date.isoformat(sep=' ', timespec='seconds')}"
        )
        if self.kanban_task.due_date:
            # toggle switch
            self.query_one(Switch).value = True
            # set date in widget
            self.query_one(DateSelect).date = self.kanban_task.due_date
            self.query_one(
                TaskDueDateSelector
            ).due_date = self.kanban_task.due_date.replace(microsecond=0, tzinfo=None)

        if self.kanban_task.start_date:
            self.query_one("#label_start_date", Label).update(
                self.kanban_task.start_date.isoformat(sep=" ", timespec="seconds")
            )
        if self.kanban_task.finish_date:
            self.query_one("#label_finish_date", Label).update(
                self.kanban_task.finish_date.isoformat(sep=" ", timespec="seconds")
            )
