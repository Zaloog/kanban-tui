from pathlib import Path

from textual.app import App
from textual.reactive import reactive

from kanban_tui.views.main_view import MainView
from kanban_tui.config import KanbanTuiConfig, init_new_config
from kanban_tui.database import (
    init_new_db,
    get_all_boards_db,
    get_all_tasks_on_board_db,
    get_all_columns_on_board_db,
    init_first_board,
)
from kanban_tui.classes.task import Task
from kanban_tui.classes.board import Board
from kanban_tui.classes.column import Column
from kanban_tui.constants import DB_FULL_PATH, CONFIG_FULL_PATH


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")
    # BINDINGS = [("ctrl+c", "quit", "Quit")]

    SCREENS = {"MainView": MainView}

    cfg: KanbanTuiConfig
    task_list: reactive[list[Task]] = reactive([], init=False)
    board_list: reactive[list[Board]] = reactive([], init=False)
    column_list: reactive[list[Board]] = reactive([], init=False)
    active_board: Board = None

    def __init__(
        self,
        config_path: Path = CONFIG_FULL_PATH,
        database_path: Path = DB_FULL_PATH,
        demo_mode: bool = False,
    ) -> None:
        init_new_config(config_path=config_path, database=database_path)
        self.cfg = KanbanTuiConfig(config_path=config_path, database_path=database_path)
        self.demo_mode = demo_mode

        init_new_db(database=self.cfg.database_path)
        init_first_board(database=self.cfg.database_path)
        super().__init__()

    def on_mount(self) -> None:
        self.theme = "dracula"
        # After boards got updated and active board
        # is set, also updates tasks
        self.update_board_list()
        self.push_screen("MainView")

    def update_board_list(self):
        self.board_list = get_all_boards_db(database=self.app.cfg.database_path)
        self.active_board = self.get_active_board()
        self.update_task_list()
        self.update_column_list()
        # self.notify(f"{self.column_list}")

    def update_task_list(self):
        self.task_list = get_all_tasks_on_board_db(
            database=self.app.cfg.database_path, board_id=self.active_board.board_id
        )

    def update_column_list(self):
        self.column_list = get_all_columns_on_board_db(
            database=self.app.cfg.database_path, board_id=self.active_board.board_id
        )

    def get_active_board(self) -> None | Board:
        for board in self.board_list:
            if board.board_id == self.cfg.active_board:
                return board
        return None

    @property
    def visible_column_list(self) -> list[Column]:
        return [col.name for col in self.column_list if col.visible]
