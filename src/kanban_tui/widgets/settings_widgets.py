from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.events import Mount
from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Label, Switch, Input, Collapsible
from textual.containers import Horizontal, VerticalScroll, Vertical

from kanban_tui.modal.modal_color_pick import ColorTable


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
            yield Input(placeholder="Start")
            yield Label("to")
            yield Input(placeholder="End")
        return super().compose()


class AlwaysExpandedSwitch(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.tasks_always_expanded"

        yield Label("Always Expand Tasks")
        yield Switch(value=self.app.cfg.tasks_always_expanded, id="switch_expand_tasks")
        return super().compose()

    def on_switch_changed(self, event: Switch.Changed):
        self.app.cfg.tasks_always_expanded = event.value


class DefaultTaskColorSelector(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        self.border_title = "kanban.settings.default_task_color"

        yield Label("Default Task Color")
        with Collapsible(title="Pick Color"):
            yield ColorTable()

        return super().compose()


class ChangeColumnVisibilitySwitch(Horizontal):
    app: "KanbanTui"

    def __init__(self, column_name: str) -> None:
        self.column_name = column_name
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        yield Label(f"Show [blue]{self.column_name}[/]")
        yield Switch(value=self.app.cfg.column_dict[self.column_name])
        return super().compose()


# Widget to Add new columns and change column visibility
# Select Widget, visible Green, not visible red
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
            for column in self.app.cfg.columns:
                yield ChangeColumnVisibilitySwitch(column_name=column)

        return super().compose()

    def watch_amount_visible(self):
        self.query_one("#label_amount_visible", Label).update(
            f"Show {self.amount_visible} / {len(self.app.cfg.columns)} Columns"
        )

    def on_switch_changed(self, event: Switch.Changed):
        self.amount_visible += 1 if event.value else -1
