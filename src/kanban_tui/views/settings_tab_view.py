from typing import Iterable

from textual import on
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Switch, Placeholder
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.settings_widgets import (
    AlwaysExpandedSwitch,
    DefaultTaskColorSelector,
    DataBasePathInput,
    WorkingHoursSelector,
    ColumnSelector,
)


class SettingsView(Vertical):
    config_has_changed: reactive[bool] = reactive(False)

    def compose(self) -> Iterable[Widget]:
        yield DataBasePathInput()
        with Horizontal(id="horizontal_expand_work_hours"):
            yield AlwaysExpandedSwitch()
            yield WorkingHoursSelector()
        with Horizontal(id="horizontal_color_column_selector"):
            yield DefaultTaskColorSelector()
            yield ColumnSelector()
        yield Placeholder("FutureStuff")
        return super().compose()

    @on(Input.Changed)
    @on(Switch.Changed)
    def config_changes(self, _event: Input.Changed | Switch.Changed):
        self.config_has_changed = True
        self.notify("Has Changed config")
