from pathlib import Path

from textual.app import App

from kanban_tui.views.main_view import MainView


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")
    BINDINGS = [("ctrl+c", "quit", "Quit")]

    SCREENS = {"MainView": MainView}

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None:
        self.push_screen("MainView")
