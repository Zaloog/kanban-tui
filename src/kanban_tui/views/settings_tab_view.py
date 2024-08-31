from typing import Iterable

from textual.widget import Widget
from textual.containers import Vertical

from kanban_tui.widgets.settings_widgets import (
    AlwaysExpandedSwitch,
    DefaultTaskColorSelector,
    ShowArchiveSwitch,
    DataBasePathInput,
)


class SettingsView(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield AlwaysExpandedSwitch()
        yield DefaultTaskColorSelector()
        yield ShowArchiveSwitch()
        yield DataBasePathInput()
        return super().compose()
