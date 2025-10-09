from typing import Iterable

from textual import on
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Header, Footer, Input, Switch, Button, Select
from textual.screen import Screen

from kanban_tui.widgets.settings_widgets import SettingsView


class SettingsScreen(Screen):
    config_has_changed: reactive[bool] = reactive(False, init=False)

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield Footer()
        yield SettingsView()

    @on(Input.Changed)
    @on(Switch.Changed)
    @on(Button.Pressed)
    @on(Select.Changed)
    def config_changes(self):
        self.app.config_has_changed = True
