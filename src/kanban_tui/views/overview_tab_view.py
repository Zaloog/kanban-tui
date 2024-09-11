from typing import Iterable
from textual.widget import Widget
from textual.widgets import Placeholder
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.overview_widgets import TaskPlot, PlotFilter


class OverView(Vertical):
    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            yield PlotFilter()
            yield Placeholder("Top Filters")
        yield TaskPlot()
        yield Placeholder("Table?")
        return super().compose()
