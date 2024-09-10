from typing import Iterable
from textual.widget import Widget
from textual.widgets import Placeholder
from textual.containers import Vertical

from kanban_tui.widgets.overview_widgets import TaskPlot


class OverView(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Placeholder("Top Filters")
        yield TaskPlot()
        yield Placeholder("Table?")
        return super().compose()
