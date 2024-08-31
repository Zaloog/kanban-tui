from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.widget import Widget
from textual.widgets import Label, Switch, Input
from textual.containers import Horizontal


class DataBasePathInput(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Database File")
        yield Input(value=self.app.cfg.database_path.as_posix())
        return super().compose()


class AlwaysExpandedSwitch(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Always Expand Tasks")
        yield Switch(value=self.app.cfg.tasks_always_expanded, id="switch_expand_tasks")
        return super().compose()


class ShowArchiveSwitch(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Show Archived Tasks")
        yield Switch(value=self.app.cfg.show_archive, id="switch_show_archive")
        return super().compose()


class DefaultTaskColorSelector(Horizontal):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label("Default Task Color")
        # yield Switch(value=False)
        return super().compose()
