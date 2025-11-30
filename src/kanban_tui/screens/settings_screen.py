from typing import Iterable

from textual import on
from textual.binding import Binding
from textual.events import ScreenResume
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Header, Input, Switch, Button, Select
from textual.screen import Screen
from textual_jumper import Jumper

from kanban_tui.widgets.settings_widgets import SettingsView
from kanban_tui.widgets.custom_widgets import KanbanTuiFooter


class SettingsScreen(Screen):
    needs_refresh: reactive[bool] = reactive(False, init=False)

    BINDINGS = [Binding("ctrl+o", "show_overlay", "Jump", priority=True)]

    def compose(self) -> Iterable[Widget]:
        yield Header()
        yield KanbanTuiFooter()
        yield SettingsView()
        yield Jumper(
            ids_to_keys={
                "switch_expand_tasks": "e",
                "select_columns_in_view": "b",
                "task_color_preview": "g",
                "select_movement_mode": "n",
                "select_reset": "s",
                "column_list": "c",
            }
        )

    @on(Input.Changed)
    @on(Switch.Changed)
    @on(Button.Pressed)
    @on(Select.Changed)
    def config_changes(self, event):
        self.app.needs_refresh = True

    @on(ScreenResume)
    def update_settings(self):
        if self.needs_refresh:
            self.query_one(SettingsView).refresh(recompose=True)
            self.needs_refresh = False

    def action_show_overlay(self) -> None:
        self.query_one(Jumper).show()
