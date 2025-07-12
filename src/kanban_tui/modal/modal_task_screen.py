from typing import Iterable, TYPE_CHECKING
from datetime import datetime


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


import pendulum
from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Button, Select, Label, Switch, Footer
from textual.containers import Horizontal, Vertical

from kanban_tui.textual_datepicker import DateSelect
from kanban_tui.classes.task import Task
from kanban_tui.database import create_new_task_db, update_task_entry_db
from kanban_tui.widgets.modal_task_widgets import (
    CreationDateInfo,
    CategorySelector,
    StartDateInfo,
    FinishDateInfo,
    DetailInfos,
    DescriptionInfos,
)


class ModalTaskEditScreen(ModalScreen):
    app: "KanbanTui"

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("ctrl+j", "update_task", "Save/Edit Task", priority=True),
    ]

    def __init__(self, task: Task | None = None) -> None:
        self.kanban_task = task
        super().__init__()

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
                self.detail_infos = DetailInfos(id="detail_infos")
                yield self.detail_infos
            with Horizontal(id="horizontal_buttons"):
                yield Button("Create Task", id="btn_continue", variant="success")
                yield Button("Cancel", id="btn_cancel", variant="error")
            yield Footer()
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.watch(
            self.detail_infos.query_one(CategorySelector),
            "value",
            self.update_description_background,
        )
        if self.kanban_task:
            self.query_one("#btn_continue", Button).label = "Edit Task"
            self.query_one("#label_header", Label).update("Edit Task")
            self.read_values_from_task()
        return super()._on_mount(event)

    @on(Button.Pressed, "#btn_continue")
    def action_update_task(self):
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

        if not self.kanban_task:
            # create new task
            create_new_task_db(
                title=title,
                description=description,
                column=list(self.app.visible_column_dict.keys())[0],
                start_date=datetime.now()
                if (list(self.app.visible_column_dict.keys())[0] == "Doing")
                else None,
                category=category,
                due_date=due_date,
                board_id=self.app.cfg.active_board,
                database=self.app.cfg.database_path,
            )

            self.app.update_task_list()
            self.dismiss(result=self.app.task_list[-1])

        else:
            self.kanban_task.title = title
            if due_date is not None:
                self.kanban_task.due_date = datetime.fromisoformat(due_date)
                self.kanban_task.days_left = self.kanban_task.get_days_left_till_due()
            else:
                self.kanban_task.due_date = None
                self.kanban_task.days_left = self.kanban_task.get_days_left_till_due()

            self.kanban_task.description = description
            self.kanban_task.category = category

            update_task_entry_db(
                task_id=self.kanban_task.task_id,
                title=self.kanban_task.title,
                due_date=self.kanban_task.due_date,
                description=self.kanban_task.description,
                category=self.kanban_task.category,
                database=self.app.cfg.database_path,
            )

            self.dismiss(result=self.kanban_task)

    @on(Button.Pressed, "#btn_cancel")
    def close_window(self):
        self.app.pop_screen()

    def update_description_background(self, category: str):
        if category != CategorySelector.NEW:
            self.query_one(
                TextArea
            ).styles.background = self.app.cfg.category_color_dict.get(
                category, self.app.cfg.no_category_task_color
            )
            self.query_one(TextArea).styles.background = self.query_one(
                TextArea
            ).styles.background.darken(0.2)

    def read_values_from_task(self):
        self.query_one("#input_title", Input).value = self.kanban_task.title
        self.query_one(TextArea).text = self.kanban_task.description
        # self.update_description_background(category=self.kanban_task.category)

        self.query_one(Select).value = (
            self.kanban_task.category if self.kanban_task.category else Select.BLANK
        )
        self.query_one("#label_create_date", Label).update(
            f"Task created at: {self.kanban_task.creation_date.isoformat(sep=' ', timespec='seconds')}"
        )
        if self.kanban_task.due_date:
            # toggle switch
            self.query_one(Switch).value = True
            # set date in widget
            self.query_one(DateSelect).date = pendulum.instance(
                # self.query_one(CustomDateSelect).date = pendulum.instance(
                self.kanban_task.due_date
            )
            self.query_one(DetailInfos).due_date = self.kanban_task.due_date.replace(
                microsecond=0, tzinfo=None
            )

        if self.kanban_task.start_date:
            self.query_one("#label_start_date", Label).update(
                self.kanban_task.start_date.isoformat(sep=" ", timespec="seconds")
            )
        if self.kanban_task.finish_date:
            self.query_one("#label_finish_date", Label).update(
                self.kanban_task.finish_date.isoformat(sep=" ", timespec="seconds")
            )


class ModalConfirmScreen(ModalScreen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, text: str) -> None:
        self.display_text = text
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Label(self.display_text)
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Confirm Delete", id="btn_continue_delete", variant="success"
                )
                yield Button("Cancel Delete", id="btn_cancel_delete", variant="error")
            return super().compose()

    @on(Button.Pressed, "#btn_continue_delete")
    def confirm_delete(self):
        self.dismiss(result=True)

    @on(Button.Pressed, "#btn_cancel_delete")
    def cancel_delete(self):
        self.dismiss(result=False)
