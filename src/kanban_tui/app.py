from pathlib import Path

from textual.app import App
from textual.reactive import reactive

from kanban_tui.views.main_view import MainView
from kanban_tui.constants import CONFIG_FULL_PATH
from kanban_tui.config import KanbanTuiConfig, init_new_config
from kanban_tui.database import init_new_db, get_all_tasks_db
from kanban_tui.classes.task import Task


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")
    # BINDINGS = [("ctrl+c", "quit", "Quit")]

    SCREENS = {"MainView": MainView}

    cfg: KanbanTuiConfig
    task_list: reactive[list[Task]] = reactive([], init=False)

    def __init__(self) -> None:
        init_new_config(config_path=CONFIG_FULL_PATH)
        self.cfg = KanbanTuiConfig(config_path=CONFIG_FULL_PATH)

        init_new_db(database=self.cfg.database_path)
        super().__init__()

    def on_mount(self) -> None:
        self.update_task_list()
        self.push_screen("MainView")

    def update_task_list(self):
        tasks = get_all_tasks_db(database=self.app.cfg.database_path)
        # self.task_list = [Task(**task) for task in tasks]
        self.task_list = tasks
