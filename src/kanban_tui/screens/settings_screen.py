from typing import Iterable

from textual import on
from textual.widget import Widget
from textual.widgets import Header, Input, Switch, Button, Select
from textual.screen import Screen

from kanban_tui.widgets.settings_widgets import SettingsView
from kanban_tui.widgets.custom_widgets import KanbanTuiFooter


class SettingsScreen(Screen):
    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield KanbanTuiFooter()
        yield SettingsView()

    @on(Input.Changed)
    @on(Switch.Changed)
    @on(Button.Pressed)
    @on(Select.Changed)
    def config_changes(self):
        self.app.needs_refresh = True
