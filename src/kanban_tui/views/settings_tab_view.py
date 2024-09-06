from typing import Iterable

from textual import on
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Switch, Placeholder, Button
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.settings_widgets import (
    AlwaysExpandedSwitch,
    DefaultTaskColorSelector,
    DataBasePathInput,
    WorkingHoursSelector,
    ColumnSelector,
)


class SettingsView(Vertical):
    config_has_changed: reactive[bool] = reactive(False, init=False)

    def compose(self) -> Iterable[Widget]:
        yield DataBasePathInput()
        with Horizontal(id="horizontal_expand_work_hours"):
            yield AlwaysExpandedSwitch()
            yield WorkingHoursSelector()
        with Horizontal(id="horizontal_color_column_selector"):
            with Vertical():
                yield DefaultTaskColorSelector()
                yield Placeholder("FutureStuff")
            yield ColumnSelector()
        return super().compose()

    @on(Input.Changed)
    @on(Switch.Changed)
    @on(Button.Pressed)
    def config_changes(self, event: Input.Changed | Switch.Changed | Button.Pressed):
        self.config_has_changed = True
