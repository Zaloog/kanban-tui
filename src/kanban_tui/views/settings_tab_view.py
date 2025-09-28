from typing import Iterable, Literal

from textual import on
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Switch, Button, Select
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.settings_widgets import (
    BoardColumnsInView,
    TaskAlwaysExpandedSwitch,
    DefaultTaskColorSelector,
    DataBasePathInput,
    TaskMovementSelector,
    ColumnSelector,
    StatusColumnSelector,
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
            action="quick_focus_setting('movement_mode')",
            show=False,
            priority=True,
        ),
        Binding(
            key="ctrl+b",
            action="quick_focus_setting('columns_in_view')",
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
        Binding(
            key="ctrl+s",
            action="quick_focus_setting('status')",
            show=False,
            priority=True,
        ),
    ]
    config_has_changed: reactive[bool] = reactive(False, init=False)

    def compose(self) -> Iterable[Widget]:
        yield DataBasePathInput(classes="setting-block")
        with Horizontal(id="horizontal_expand_movement"):
            yield TaskAlwaysExpandedSwitch(classes="setting-block")
            yield TaskMovementSelector(classes="setting-block")
            yield BoardColumnsInView(classes="setting-block")
        with Horizontal(id="horizontal_color_column_selector"):
            with Vertical(id="vertical_column_status"):
                yield DefaultTaskColorSelector(classes="setting-block")
                yield StatusColumnSelector(classes="setting-block")
            yield ColumnSelector(classes="setting-block")

    @on(Input.Changed)
    @on(Switch.Changed)
    @on(Button.Pressed)
    @on(Select.Changed)
    def config_changes(self):
        self.config_has_changed = True

    def action_quick_focus_setting(
        self,
        block: Literal[
            "db",
            "expand",
            "movement_mode",
            "defaultcolor",
            "columns",
            "status",
            "columns_in_view",
        ],
    ):
        match block:
            case "db":
                self.query_one(DataBasePathInput).query_one(Input).focus()
            case "expand":
                self.query_one(TaskAlwaysExpandedSwitch).query_one(Switch).focus()
            case "columns_in_view":
                self.query_one(BoardColumnsInView).query_one(Select).focus()
            case "movement_mode":
                self.query_one(TaskMovementSelector).query_one(Select).focus()
            case "defaultcolor":
                self.query_one(DefaultTaskColorSelector).query_one(Input).focus()
            case "columns":
                self.query_one(ColumnSelector).focus()
            case "status":
                self.query_one(StatusColumnSelector).query(Select).focus()
