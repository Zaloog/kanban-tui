from typing import Iterable, TYPE_CHECKING
from collections import Counter

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.events import Mount
from textual.widget import Widget
from textual.widgets import Label, Switch
from textual_plotext import PlotextPlot
from textual.containers import HorizontalScroll, Horizontal


class TaskPlot(HorizontalScroll):
    app: "KanbanTui"

    def _on_mount(self, event: Mount) -> None:
        self.update_task_plot()
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        yield PlotextPlot()
        return super().compose()

    def update_task_plot(self, show_categories: bool = False):
        plt = self.query_one(PlotextPlot).plt
        start_dates = [
            task.strftime("%b %Y")
            for task in sorted([task.start_date for task in self.app.task_list])
        ]
        counts = Counter(start_dates)
        self.notify(f"{counts}")

        plt.bar(counts.keys(), counts.values(), width=0.5, reset_ticks=True, minimum=0)
        plt.horizontal_line(coordinate=2, color="red")
        plt.yfrequency(frequency=5)
        plt.xlabel("Date")
        plt.ylabel("Count")
        plt.title("Task Amount")


class PlotFilter(Horizontal):
    app: "KanbanTui"

    def __init__(self, column_name: str) -> None:
        self.column_name = column_name
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        yield Label("Show Category Detail")
        yield Switch(
            value=False,
            id="switch_plot_category_detail",
        )
        return super().compose()
