from typing import Iterable, TYPE_CHECKING
from collections import Counter

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.events import Mount
from textual.widget import Widget
from textual_plotext import PlotextPlot
from textual.containers import HorizontalScroll


class TaskPlot(HorizontalScroll):
    app: "KanbanTui"

    def _on_mount(self, event: Mount) -> None:
        plt = self.query_one(PlotextPlot).plt
        start_dates = sorted(
            [task.start_date.strftime("%b %Y") for task in self.app.task_list]
        )
        counts = Counter(start_dates)
        self.notify(f"{counts}")

        plt.bar(counts.keys(), counts.values(), width=0.5)
        plt.xlabel("Date")
        plt.ylabel("Count")
        plt.title("Task Amount")
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        yield PlotextPlot()
        return super().compose()
