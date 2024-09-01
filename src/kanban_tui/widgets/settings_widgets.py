from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Label, Switch, Input, Collapsible
from textual.containers import Horizontal, VerticalScroll


class DataBasePathInput(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Database File")
        with self.prevent(Input.Changed):
            yield Input(value=self.app.cfg.database_path.as_posix())
        return super().compose()


class AlwaysExpandedSwitch(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Always Expand Tasks")
        yield Switch(value=self.app.cfg.tasks_always_expanded, id="switch_expand_tasks")
        return super().compose()

    def on_switch_changed(self, event: Switch.Changed):
        self.app.cfg.tasks_always_expanded = event.value


class DefaultTaskColorSelector(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Default Task Color")
        # yield Switch(value=False)
        return super().compose()


class ChangeColumnVisibilitySwitch(Horizontal):
    app: "KanbanTui"

    def __init__(self, column_name: str) -> None:
        self.column_name = column_name
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        yield Label(f"Show {self.column_name} Column")
        yield Switch(value=self.app.cfg.column_dict[self.column_name])
        return super().compose()


# Widget to Add new columns and change column visibility
# Select Widget, visible Green, not visible red
class ColumnSelector(Collapsible):
    app: "KanbanTui"

    BINDINGS = [
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]
    amount_visible: reactive[int] = reactive(0)

    def __init__(self):
        column_children = []
        for column in self.app.cfg.columns:
            column_children.append(ChangeColumnVisibilitySwitch(column_name=column))
        super().__init__(VerticalScroll(*column_children))
        self.amount_visible = len(self.app.cfg.visible_columns)

    def watch_amount_visible(self):
        self.title = f"Show {self.amount_visible} / {len(self.app.cfg.columns)} Columns"

    def on_switch_changed(self, event: Switch.Changed):
        self.amount_visible += 1 if event.value else -1
