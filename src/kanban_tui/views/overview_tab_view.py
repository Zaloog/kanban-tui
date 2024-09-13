from typing import Iterable
from textual import on
from textual.events import Mount
from textual.widget import Widget
from textual.widgets import Placeholder, Select, Switch
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.overview_widgets import (
    TaskPlot,
    CategoryPlotFilter,
    AmountPlotFilter,
    FrequencyPlotFilter,
)


class OverView(Vertical):
    def _on_mount(self, event: Mount) -> None:
        self.watch(self.app, "task_list", self.update_plot_by_filters, init=False)
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_overview_filters"):
            yield CategoryPlotFilter()
            yield AmountPlotFilter()
            yield FrequencyPlotFilter()
        yield TaskPlot()
        yield Placeholder("Table?")
        return super().compose()

    @on(Switch.Changed)
    @on(Select.Changed)
    async def update_plot_by_filters(self, _event: Switch.Changed | Select.Changed):
        category_switch = self.query_one("#switch_plot_category_detail", Switch).value
        amount_select = self.query_one("#select_plot_filter_amount", Select).value
        frequency_select = self.query_one("#select_plot_filter_frequency", Select).value

        await self.query_one(TaskPlot).update_task_plot(
            switch_categories=category_switch,
            select_amount=amount_select,
            select_frequency=frequency_select,
        )
