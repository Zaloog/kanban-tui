from pathlib import Path

from textual.app import App

from kanban_tui.views.main_view import MainView
from kanban_tui.constants import CONFIG_FULL_PATH
from kanban_tui.config import KanbanTuiConfig, init_new_config
from kanban_tui.database import init_new_db


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")
    # BINDINGS = [("ctrl+c", "quit", "Quit")]

    SCREENS = {"MainView": MainView}

    cfg: KanbanTuiConfig

    def __init__(self) -> None:
        init_new_config(config_path=CONFIG_FULL_PATH)
        self.cfg = KanbanTuiConfig(config_path=CONFIG_FULL_PATH)

        init_new_db(database=self.cfg.database_path)

        super().__init__()

    def on_mount(self) -> None:
        self.push_screen("MainView")
