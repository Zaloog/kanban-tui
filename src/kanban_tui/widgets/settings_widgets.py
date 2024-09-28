from __future__ import annotations
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.message import Message
from textual.events import Mount, DescendantBlur
from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Label, Switch, Input, Collapsible, DataTable, Rule, Button
from textual.containers import Horizontal, VerticalScroll, Vertical

from kanban_tui.modal.modal_color_pick import ColorTable, TitleInput
from kanban_tui.modal.modal_settings import ModalNewColumnScreen
from kanban_tui.modal.modal_task_screen import ModalConfirmScreen


class DataBasePathInput(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "database.database_path"

        yield Label("Database File")
        with self.prevent(Input.Changed):
            yield Input(value=self.app.cfg.database_path.as_posix())
        return super().compose()


class WorkingHoursSelector(Vertical):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.work_hours"

        yield Label("Working Hours (coming soon)")
        with Horizontal():
            # yield HourMinute(hour_value=self.app.cfg.work_hour_dict['start_hour'], min_value=self.app.cfg.work_hour_dict['start_min'], id="hour_minute_start")
            yield HourMinute(id="hour_minute_start")
            yield Label("to")
            # yield HourMinute(hour_value=self.app.cfg.work_hour_dict['end_hour'], min_value=self.app.cfg.work_hour_dict['end_min'], id="hour_minute_end")
            yield HourMinute(id="hour_minute_end")
        return super().compose()


class HourMinute(Horizontal):
    def __init__(
        self, hour_value: str = "00", min_value: str = "00", id: str | None = None
    ) -> None:
        self.hour_value = hour_value
        self.min_value = min_value
        super().__init__(id=id)

    def compose(self) -> Iterable[Widget]:
        with self.prevent(Input.Changed):
            yield Input(value=self.hour_value, placeholder="HH")
            # yield Input(placeholder="HH")
            yield Label(":")
            yield Input(value=self.min_value, placeholder="MM")
            # yield Input(placeholder="MM")
        return super().compose()


class AlwaysExpandedSwitch(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.tasks_always_expanded"

        yield Label("Always Expand Tasks")
        yield Switch(value=self.app.cfg.tasks_always_expanded, id="switch_expand_tasks")
        return super().compose()

    def on_switch_changed(self, event: Switch.Changed):
        self.app.cfg.set_tasks_always_expanded(new_value=event.value)


class DefaultTaskColorSelector(Horizontal):
    app: "KanbanTui"

    def _on_mount(self, event: Mount) -> None:
        self.query_one(TitleInput).value = self.app.cfg.no_category_task_color
        self.query_one(TitleInput).background = self.app.cfg.no_category_task_color
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.default_task_color"

        with Vertical():
            yield Label("Default Task Color")
            with self.prevent(Input.Changed):
                yield TitleInput(
                    value=self.app.cfg.no_category_task_color, id="task_color_preview"
                )
        with Collapsible(title="Pick Color"):
            with self.prevent(DataTable.CellHighlighted):
                yield ColorTable()

        return super().compose()

    @on(DataTable.CellHighlighted)
    def change_input_str_on_color_pick(self, event: DataTable.CellHighlighted):
        self.query_one(TitleInput).value = event.data_table.get_cell_at(
            event.coordinate
        ).color_value

    @on(Input.Changed)
    def update_input_color(self, event: Input.Changed):
        try:
            self.query_one(TitleInput).background = event.input.value
            self.app.cfg.set_no_category_task_color(new_color=event.input.value)
            event.input.styles.border = "tall", "green"
            event.input.border_subtitle = None
            event.input.border_title = None
        # Todo add validator to input?
        except Exception:
            event.input.styles.border = "tall", "red"
            event.input.border_subtitle = "invalid color value"
            event.input.border_title = (
                f"last valid: {self.app.cfg.no_category_task_color}"
            )

    @on(DescendantBlur)
    def reset_color(self):
        self.query_one(TitleInput).value = self.app.cfg.no_category_task_color


class ChangeColumnVisibilitySwitch(Horizontal):
    app: "KanbanTui"

    def __init__(self, column_name: str) -> None:
        self.column_name = column_name
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        yield Label(f"Show [blue]{self.column_name}[/]")
        yield Switch(
            value=self.app.cfg.column_dict[self.column_name],
            id=f"switch_col_vis_{self.column_name}",
            # disabled=True if self.column_name in COLUMNS[:3] else False,
        )
        yield Button(
            label="Delete",
            id=f"button_col_del_{self.column_name}",
            variant="error",
            # disabled=True if self.column_name in COLUMNS else False,
        )
        return super().compose()


# Widget to Add new columns and change column visibility
# Select Widget, visible Green, not visible red
class AddRule(Rule):
    class Pressed(Message):
        def __init__(self, addrule: AddRule) -> None:
            self.addrule = addrule
            super().__init__()

        @property
        def control(self):
            return self.addrule

    def __init__(self, position: int, id: str | None = None) -> None:
        self.position = position
        super().__init__(id=id)

    def compose(self) -> Iterable[Widget]:
        yield Button("+")
        return super().compose()

    def on_button_pressed(self):
        self.post_message(self.Pressed(self))


class ColumnSelector(Vertical):
    app: "KanbanTui"

    BINDINGS = [
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]
    amount_visible: reactive[int] = reactive(0)

    def _on_mount(self, event: Mount) -> None:
        self.amount_visible = len(self.app.cfg.visible_columns)
        self.border_title = "column.visibility"
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        yield Label(id="label_amount_visible")
        with VerticalScroll():
            for position, column in enumerate(self.app.cfg.columns, start=1):
                yield ChangeColumnVisibilitySwitch(column_name=column)
                yield AddRule(id=column, position=position)

        return super().compose()

    @on(AddRule.Pressed)
    def add_new_column(self, event: AddRule.Pressed):
        # Implement Modal
        self.app.push_screen(
            ModalNewColumnScreen(event=event), callback=self.modal_add_new_column
        )

    def modal_add_new_column(self, event_col_name: tuple[AddRule.Pressed, str] | None):
        if event_col_name:
            event, col_name = event_col_name
            self.app.cfg.add_new_column(
                new_column=col_name, position=event.addrule.position
            )
            # for rule in self.query_one(VerticalScroll).query(AddRule):
            #     if rule.position > event.addrule.position:
            #         rule.position += 1
            self.query_one(VerticalScroll).mount(
                AddRule(id=col_name, position=event.addrule.position),
                after=f"#{event.addrule.id}",
            )
            self.query_one(VerticalScroll).mount(
                ChangeColumnVisibilitySwitch(column_name=col_name),
                after=f"#{event.addrule.id}",
            )

            for new_position, rule in enumerate(self.query(AddRule), start=1):
                rule.position = new_position

            self.notify(
                title="Columns Updated",
                message=f"Column [blue]{col_name}[/] created",
                timeout=2,
            )
            self.amount_visible += 1

    @on(Button.Pressed)
    def delete_column(self, event: Button.Pressed):
        # Implement Modal
        if not event.button.id:
            return
        # TODO check if column empty
        column_name = event.button.id.split("_")[-1]
        if (
            len([task for task in self.app.task_list if task.column == column_name])
            != 0
        ):
            self.notify(
                title="Column not empty",
                message=f"Remove all tasks in column [blue]{column_name}[/] before deletion",
                timeout=1,
                severity="error",
            )
            return

        self.app.push_screen(
            ModalConfirmScreen(text=f"Delete Column [blue]{column_name}[/]"),
            callback=lambda x: self.modal_delete_column(event=event, delete_yn=x),
        )

    def modal_delete_column(self, event: Button.Pressed, delete_yn: bool) -> None:
        if delete_yn:
            column_name = event.button.id.split("_")[-1]

            if column_name in self.app.cfg.visible_columns:
                self.app.cfg.delete_column(column_to_delete=column_name)
                self.amount_visible -= 1
            else:
                self.app.cfg.delete_column(column_to_delete=column_name)
                self.watch_amount_visible()

            event.button.parent.remove()
            self.query_one(f"#{column_name}").remove()

            for new_position, rule in enumerate(self.query(AddRule), start=1):
                rule.position = new_position

            self.notify(
                title="Columns Updated",
                message=f"Column [blue]{column_name}[/] deleted",
                timeout=2,
            )

    def watch_amount_visible(self):
        self.query_one("#label_amount_visible", Label).update(
            f"Show {self.amount_visible} / {len(self.app.cfg.columns)} Columns"
        )

    def on_switch_changed(self, event: Switch.Changed):
        self.amount_visible += 1 if event.value else -1
        column = event.switch.id.split("_")[-1]

        self.app.cfg.set_column_dict(column_name=column)
