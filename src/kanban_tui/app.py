from typing import Iterable
from pathlib import Path

from textual.app import App
from textual.widget import Widget
from textual.containers import VerticalScroll, Horizontal

from kanban_tui.widgets.task_card import TaskCard


class KanbanTui(App):
    CSS_PATH = Path("assets/style.tcss")

    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            with VerticalScroll():
                for i in range(5):
                    yield TaskCard(title=i)
            with VerticalScroll():
                for i in range(5):
                    yield TaskCard(title=i)
            with VerticalScroll():
                for i in range(5):
                    yield TaskCard(title=i)
        return super().compose()
