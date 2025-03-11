from typing import Iterable, Literal

from textual import on
from textual.binding import Binding
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
    BINDINGS = [
        Binding(
            key="ctrl+d", action="quick_focus_setting('db')", show=False, priority=True
        ),
        Binding(
            key="ctrl+e",
            action="quick_focus_setting('expand')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+n",
            action="quick_focus_setting('hours')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+g",
            action="quick_focus_setting('defaultcolor')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+c",
            action="quick_focus_setting('columns')",
            show=False,
            priority=True,
        ),
    ]
    config_has_changed: reactive[bool] = reactive(False, init=False)

    def compose(self) -> Iterable[Widget]:
        yield DataBasePathInput(classes="setting-block")
        with Horizontal(id="horizontal_expand_work_hours"):
            yield AlwaysExpandedSwitch(classes="setting-block")
            yield WorkingHoursSelector(classes="setting-block")
        with Horizontal(id="horizontal_color_column_selector"):
            with Vertical():
                yield DefaultTaskColorSelector(classes="setting-block")
                yield Placeholder("FutureStuff")
            yield ColumnSelector(classes="setting-block")
        return super().compose()

    @on(Input.Changed)
    @on(Switch.Changed)
    @on(Button.Pressed)
    def config_changes(self, event: Input.Changed | Switch.Changed | Button.Pressed):
        self.config_has_changed = True

    def action_quick_focus_setting(
        self, block: Literal["db", "expand", "hours", "defaultcolor", "columns"]
    ):
        match block:
            case "db":
                self.query_one(DataBasePathInput).query_one(Input).focus()
            case "expand":
                self.query_one(AlwaysExpandedSwitch).query_one(Switch).focus()
            case "hours":
                self.query_one(WorkingHoursSelector).query_one(Input).focus()
            case "defaultcolor":
                self.query_one(DefaultTaskColorSelector).query_one(Input).focus()
            case "columns":
                self.query_one(ColumnSelector).focus()
