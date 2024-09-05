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
        self.border_title = "work_hours.settings"

        yield Label("Working Hours")
        with Horizontal():
            yield HourMinute(id="hour_minute_start")
            yield Label("to")
            yield HourMinute(id="hour_minute_end")
        return super().compose()


class HourMinute(Horizontal):
    def compose(self) -> Iterable[Widget]:
        yield Input(placeholder="HH")
        yield Label(":")
        yield Input(placeholder="MM")
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
        self.notify(f"{self.app.cfg}")


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
            self.app.cfg.set_no_category_task_color(new_value=event.input.value)
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
        col_name = "Placeholder"
        self.app.cfg.add_new_column(
            new_column=col_name, position=event.addrule.position
        )
        for rule in self.query_one(VerticalScroll).query(AddRule):
            if rule.position > event.addrule.position:
                rule.position += 1
        self.query_one(VerticalScroll).mount(
            AddRule(id=col_name, position=event.addrule.position),
            after=f"#{event.addrule.id}",
        )
        self.query_one(VerticalScroll).mount(
            ChangeColumnVisibilitySwitch(column_name=col_name),
            after=f"#{event.addrule.id}",
        )
        self.amount_visible += 1

    def watch_amount_visible(self):
        self.query_one("#label_amount_visible", Label).update(
            f"Show {self.amount_visible} / {len(self.app.cfg.columns)} Columns"
        )

    def on_switch_changed(self, event: Switch.Changed):
        self.amount_visible += 1 if event.value else -1
        column = event.switch.id.split("_")[-1]

        self.app.cfg.set_column_dict(column_name=column)
