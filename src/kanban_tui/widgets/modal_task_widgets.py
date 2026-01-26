import subprocess
from shutil import which
import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Iterable, TYPE_CHECKING


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on
from textual.binding import Binding
from textual.events import DescendantBlur, DescendantFocus
from textual.reactive import reactive
from textual.widget import Widget
from textual.validation import Length
from textual.widgets import (
    Input,
    Markdown,
    Rule,
    TextArea,
    Label,
    DataTable,
    Switch,
)
from textual.containers import Horizontal, Vertical, VerticalScroll

from kanban_tui.modal.modal_category_screen import ModalCategoryManageScreen
from kanban_tui.widgets.date_select import CustomDateSelect
from kanban_tui.widgets.custom_widgets import VimSelect


class TaskTitleInput(Input):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            id="input_title",
            validators=Length(minimum=1, failure_description="Enter a valid title"),
            valid_empty=False,
            placeholder="enter a task title",
            **kwargs,
        )

    def on_mount(self):
        self.validate(self.value)
        self.show_validation_hint()

    @on(Input.Changed)
    @on(Input.Blurred)
    @on(Input.Submitted)
    def show_validation_hint(self):
        if self.is_valid:
            self.border_subtitle = ""
        else:
            self.border_subtitle = "a title is required"


class TaskDescription(VerticalScroll):
    can_focus = False
    edit_mode: reactive[bool] = reactive(False)
    text: reactive[str] = reactive("", init=False)

    def compose(self) -> Iterable[Widget]:
        self.preview = Markdown(self.text, classes="description-widgets")
        self.preview.can_focus = True
        yield self.preview

        self.editor = SuspendableTextArea(self.text, classes="description-widgets")
        self.editor.display = False
        yield self.editor

    def on_mount(self):
        self.border_title = "Description"

    @on(DescendantFocus)
    def start_editing(self, event: DescendantFocus):
        self.edit_mode = True

    @on(DescendantBlur)
    def stop_editing(self, event: DescendantBlur):
        self.edit_mode = False

    async def watch_text(self):
        self.editor.text = self.text
        await self.preview.update(self.text)

    def watch_edit_mode(self):
        self.text = self.editor.text
        self.preview.display = not self.edit_mode
        self.editor.display = self.edit_mode
        self.border_subtitle = (
            Text.from_markup(":pen: edit")
            if self.edit_mode
            else Text.from_markup(":eye:  preview (click/focus to edit)")
        )


class SuspendableTextArea(TextArea):
    BINDINGS = [
        Binding(key="ctrl+g", action="suspend_to_editor", description="$EDITOR")
    ]

    def action_suspend_to_editor(self):
        edited_text = self._suspend_and_go_to_editor_if_set()
        if edited_text:
            self.text = edited_text

    def _suspend_and_go_to_editor_if_set(self) -> str | None:  # type: ignore[return]
        editor = os.getenv("EDITOR", "vim")
        if not which(editor):
            self.notify(
                title=f"{editor} not found",
                message=f"[$warning]{editor}[/] is not available in your [$warning]$PATH[/], set [$success]$EDITOR[/] to use.",
                severity="warning",
            )
            return None

        with tempfile.NamedTemporaryFile(
            mode="w+",
            encoding="utf-8",
            prefix="kanban-tui-",
            suffix=".md",
            delete=False,
        ) as tf:
            temp_path = Path(tf.name)

            # Prefill the file with current description
            if self.text:
                tf.write(self.text)
        try:
            with self.app.suspend():
                result = subprocess.run(args=[editor, temp_path.as_posix()], text=True)

            if result.returncode == 0 and temp_path.exists():
                content = temp_path.read_text(encoding="utf-8")
                return content
            else:
                return None
        except Exception as e:
            self.notify(
                title="Error occured during editing",
                message=f"message: {e}",
                severity="error",
            )

        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except (OSError, PermissionError) as e:
                self.notify(
                    title="Error occured during deletion of temporary file",
                    message=f"message: {e}",
                    severity="error",
                )


class TaskCategorySelector(Horizontal):
    def compose(self):
        yield CategorySelector()

    def on_mount(self):
        self.border_title = "Category"


class TaskDueDateSelector(Horizontal):
    app: "KanbanTui"
    due_date: reactive[datetime | None] = reactive(None)

    def compose(self):
        yield Label("has a due Date:")
        with self.prevent(Switch.Changed):
            yield Switch(value=False, id="switch_due_date", animate=False)

        self.due_date_select = CustomDateSelect(
            placeholder="Select Due Date",
            format="%Y-%m-%d",
            picker_mount="#vertical_modal",
            id="dateselect_due_date",
        )
        self.due_date_select.display = False
        yield self.due_date_select

    def on_mount(self):
        self.border_title = "Due Date"
        self.border_subtitle = "[yellow]??[/] days left"

    @on(Switch.Changed)
    def show_due_date_info(self, event: Switch.Changed):
        self.due_date_select.display = event.value

        if not event.value:
            self.due_date = None
            self.due_date_select.date = self.due_date

    def on_date_picker_selected(self):
        self.due_date = self.query_one(CustomDateSelect).date.replace(
            microsecond=0, tzinfo=None
        )

    def watch_due_date(self):
        if not self.due_date:
            self.border_subtitle = ""
            return

        # Delta Calculation
        if self.due_date.date() <= datetime.now().date():
            delta = 0
        else:
            delta = (self.due_date - datetime.now()).days + 1

        # Border Sub Title Update for singular and plural
        if delta == 1:
            days_left_text = f"[yellow]{delta}[/] day left"
        elif delta == 0:
            days_left_text = f"[red]{delta}[/] days left"
        else:
            days_left_text = f"[green]{delta}[/] days left"
        self.border_subtitle = days_left_text


class TaskAdditionalInfos(Vertical):
    def compose(self):
        yield Rule()
        yield TaskCategorySelector(id="horizontal_category", classes="task-field")
        yield TaskDueDateSelector(id="vertical_due_date_choice", classes="task-field")
        yield DateRow(id="horizontal_dates")


class NewCategorySelection:
    def __repr__(self) -> str:
        return "Select.NewCategory"


NEW = NewCategorySelection()


class CategorySelector(VimSelect):
    app: "KanbanTui"
    # thanks Darren (https://github.com/darrenburns/posting/blob/main/src/posting/widgets/select.py)
    NEW = NEW

    def __init__(self, *args, **kwargs):
        options = self.get_available_categories()
        super().__init__(
            options=options,
            prompt="No Category",
            allow_blank=True,
            type_to_search=False,
            *args,
            **kwargs,
        )

    def watch_value(self, old_value, new_value):
        if new_value == self.NEW:
            self.app.push_screen(
                ModalCategoryManageScreen(current_category_id=old_value),
                callback=self.update_values,
            )

    def update_values(self, category_id: int | None = None) -> None:
        options = self.get_available_categories()
        self.set_options(options=options)
        if category_id:
            self.value = category_id
        else:
            self.value = self.BLANK

    def get_available_categories(self):
        options = [
            (f"[on {category.color}]  [/] {category.name}", category.category_id)
            for category in self.app.backend.get_all_categories()
        ]
        options.insert(0, ("Add/Edit/Delete categories", self.NEW))
        return options


class DateRow(Horizontal):
    def compose(self):
        yield CreationDateInfo(classes="date-container")
        yield StartDateInfo(classes="date-container")
        yield FinishDateInfo(classes="date-container")


class CreationDateInfo(Horizontal):
    def compose(self) -> Iterable[Widget]:
        yield Label(
            f"{datetime.now().replace(microsecond=0)}",
            id="label_create_date",
        )
        self.border = "$success"
        self.border_title = "Creation Date"
        return super().compose()


class StartDateInfo(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Label("[red]not started yet[/]", id="label_start_date")
        self.border = "$success"
        self.border_title = "Start Date"
        return super().compose()


class FinishDateInfo(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Label("[red]not finished yet[/]", id="label_finish_date")
        self.border = "$success"
        self.border_title = "Finish Date"
        return super().compose()


class TaskDependencyManager(Vertical):
    """Widget for managing task dependencies with dropdown and table display."""

    app: "KanbanTui"

    def __init__(self, current_task_id: int | None = None, *args, **kwargs):
        self.current_task_id = current_task_id
        super().__init__(*args, **kwargs)

    def compose(self) -> Iterable[Widget]:
        # Add dependency section
        with Horizontal(id="add_dependency_section"):
            yield Label("Add Dependency:")
            yield DependencySelector(current_task_id=self.current_task_id)

        table = DataTable(id="dependencies_table")
        table.add_columns("ID", "Title", "Status", "Action")
        table.cursor_type = "row"
        yield table

    def on_mount(self):
        self.border_title = "Task Dependencies"
        self.refresh_dependencies_table()

    def refresh_dependencies_table(self):
        """Refresh the dependencies table with current data."""
        if not self.current_task_id:
            return

        table = self.query_one("#dependencies_table", DataTable)
        table.clear()

        task = self.app.backend.get_task_by_id(self.current_task_id)
        if not task or not task.blocked_by:
            return

        # Fetch all dependency tasks in a single query to avoid N+1 queries
        dep_tasks = self.app.backend.get_tasks_by_ids(task.blocked_by)
        for dep_task in dep_tasks:
            # Use proper Rich markup for status with emojis
            if dep_task.finished:
                status = Text.from_markup("[green]:heavy_check_mark: Done[/]")
            else:
                status = Text.from_markup("[yellow]:warning: Pending[/]")
            table.add_row(
                f"#{dep_task.task_id}",
                dep_task.title[:30],  # Truncate long titles
                status,
                "Remove",
                key=str(dep_task.task_id),
            )

    def _refresh_board_task_cards(self):
        """Refresh all task cards on the board screen to show updated dependency status."""
        self.app.needs_refresh = True

    @on(DataTable.RowSelected)
    def remove_dependency(self, event: DataTable.RowSelected):
        """Remove selected dependency when row is clicked."""
        dep_id = int(event.row_key.value)
        self.app.backend.delete_task_dependency(
            task_id=self.current_task_id, depends_on_task_id=dep_id
        )
        self.refresh_dependencies_table()
        # Refresh the selector options
        self.query_one(DependencySelector).refresh_options()
        # Update task list to reflect dependency changes
        self.app.update_task_list()
        # Refresh all task cards on the board to show updated dependency status
        self._refresh_board_task_cards()


class DependencySelector(VimSelect):
    """Dropdown selector for adding task dependencies."""

    app: "KanbanTui"

    def __init__(self, current_task_id: int | None = None, *args, **kwargs):
        self.current_task_id = current_task_id
        options = self.get_available_tasks()
        super().__init__(
            options=options,
            prompt="Select task to add as dependency",
            allow_blank=True,
            type_to_search=True,
            id="dependency_selector",
            *args,
            **kwargs,
        )

    def watch_value(self, old_value, new_value):
        """Handle task selection - add as dependency."""
        if new_value == self.BLANK or not self.current_task_id:
            return

        # Check for circular dependency
        if self.app.backend.would_create_dependency_cycle(
            self.current_task_id, new_value
        ):
            self.app.notify(
                title="Cannot Add Dependency",
                message=f"Adding task #{new_value} would create a circular dependency",
                severity="warning",
                timeout=5,
            )
            self.value = self.BLANK
            return

        # Add dependency
        try:
            self.app.backend.create_task_dependency(
                task_id=self.current_task_id, depends_on_task_id=new_value
            )
            self.app.notify(
                title="Dependency Added",
                message=f"Task now depends on #{new_value}",
                severity="information",
                timeout=3,
            )
            # Refresh table in parent widget
            self.parent.parent.refresh_dependencies_table()
            # Reset selector and refresh options
            self.value = self.BLANK
            self.refresh_options()
            # Update task list and refresh all task cards
            self.app.update_task_list()
            self.parent.parent._refresh_board_task_cards()
        except Exception as e:
            self.app.notify(
                title="Error Adding Dependency",
                message=str(e),
                severity="error",
                timeout=5,
            )

    def refresh_options(self):
        """Refresh the available tasks list."""
        options = self.get_available_tasks()
        self.set_options(options)

    def get_available_tasks(self) -> list[tuple[str, int]]:
        """Get list of tasks that can be added as dependencies."""
        if not self.current_task_id:
            return []

        all_tasks = self.app.backend.get_tasks_on_active_board()
        current_task = self.app.backend.get_task_by_id(self.current_task_id)

        # Filter out invalid tasks
        available_tasks = []
        for task in all_tasks:
            # Skip current task
            if task.task_id == self.current_task_id:
                continue

            # Skip if already a dependency
            if current_task and task.task_id in current_task.blocked_by:
                continue

            # Get column name for display
            column = self.app.backend.get_column_by_id(task.column)
            column_name = column.name if column else "Unknown"

            # Format: "#ID - Title [Column]"
            display_text = f"#{task.task_id} - {task.title[:40]} [{column_name}]"
            available_tasks.append((display_text, task.task_id))

        return available_tasks


# class ButtonRow(Horizontal):
#     def compose(self):
#         yield Button("Create Task", id="btn_continue", variant="success", disabled=True)
#         yield Button("Cancel", id="btn_cancel", variant="error")
