from typing import Iterable
from textual import on
from textual.binding import Binding
from textual.events import Mount
from textual.widget import Widget
from textual.widgets import Select, Switch
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.overview_widgets import (
    TaskPlot,
    CategoryPlotFilter,
    AmountPlotFilter,
    FrequencyPlotFilter,
)


class OverView(Vertical):
    BINDINGS = [
        Binding("H", "scroll_plot_left", "Scroll Left", show=True),
        Binding("L", "scroll_plot_right", "Scroll Right", show=True),
    ]

    def _on_mount(self, event: Mount) -> None:
        # self.watch(self.app, "task_list", self.update_plot_by_filters, init=True)
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_overview_filters"):
            yield CategoryPlotFilter()
            yield AmountPlotFilter()
            yield FrequencyPlotFilter()
        yield TaskPlot()
        return super().compose()

    @on(Switch.Changed)
    @on(Select.Changed)
    async def update_plot_by_filters(
        self, event: Switch.Changed | Select.Changed | None = None
    ):
        category_switch = self.query_one("#switch_plot_category_detail", Switch).value
        amount_select = self.query_one("#select_plot_filter_amount", Select).value
        frequency_select = self.query_one("#select_plot_filter_frequency", Select).value

        await self.query_one(TaskPlot).update_task_plot(
            switch_categories=category_switch,
            select_amount=amount_select,
            select_frequency=frequency_select,
            scroll_reset=False if isinstance(event, Switch.Changed) else True,
        )

    def action_scroll_plot_right(self) -> None:
        return self.query_one(TaskPlot).action_scroll_right()

    def action_scroll_plot_left(self) -> None:
        return self.query_one(TaskPlot).action_scroll_left()
