from typing import Iterable

from textual import on
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Switch
from textual.containers import Vertical

from kanban_tui.widgets.settings_widgets import (
    AlwaysExpandedSwitch,
    DefaultTaskColorSelector,
    ShowArchiveSwitch,
    DataBasePathInput,
)


class SettingsView(Vertical):
    config_has_changed: reactive[bool] = reactive(False)

    def compose(self) -> Iterable[Widget]:
        yield DataBasePathInput()
        yield AlwaysExpandedSwitch()
        yield DefaultTaskColorSelector()
        yield ShowArchiveSwitch()
        return super().compose()

    @on(Input.Changed)
    @on(Switch.Changed)
    def config_changes(self, _event: Input.Changed | Switch.Changed):
        self.config_has_changed = True
