from typing import Iterable
from textual.widget import Widget
from textual.widgets import Placeholder
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.overview_widgets import (
    TaskPlot,
    CategoryPlotFilter,
    AmountPlotFilter,
    FrequencyPlotFilter,
)


class OverView(Vertical):
    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_overview_filters"):
            yield CategoryPlotFilter()
            yield AmountPlotFilter()
            yield FrequencyPlotFilter()
        yield TaskPlot()
        yield Placeholder("Table?")
        return super().compose()
