from pathlib import Path

from textual.app import App
from textual.reactive import reactive

from kanban_tui.views.main_view import MainView
from kanban_tui.config import KanbanTuiConfig, init_new_config
from kanban_tui.database import (
    init_new_db,
    get_all_boards_db,
    get_all_tasks_on_board_db,
    init_first_board,
)
from kanban_tui.classes.task import Task
from kanban_tui.classes.board import Board
from kanban_tui.constants import DB_FULL_PATH, CONFIG_FULL_PATH


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")
    # BINDINGS = [("ctrl+c", "quit", "Quit")]

    SCREENS = {"MainView": MainView}

    cfg: KanbanTuiConfig
    task_list: reactive[list[Task]] = reactive([], init=False)
    board_list: reactive[list[Board]] = reactive([], init=False)
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
        self.update_board_list()
        # self.update_task_list()
        self.push_screen("MainView")

    def update_task_list(self):
        tasks = get_all_tasks_on_board_db(
            database=self.app.cfg.database_path, board_id=self.active_board.board_id
        )
        self.task_list = tasks

    def update_board_list(self):
        boards = get_all_boards_db(database=self.app.cfg.database_path)
        self.board_list = boards
        self.active_board = self.get_active_board()
        self.update_task_list()

    def get_active_board(self) -> None | Board:
        for board in self.board_list:
            if board.board_id == self.cfg.active_board:
                return board
        return None
