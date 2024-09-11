from typing import Iterable, TYPE_CHECKING
from collections import Counter

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.events import Mount
from textual.widget import Widget
from textual.widgets import Label, Switch
from textual_plotext import PlotextPlot
from textual.containers import HorizontalScroll, Horizontal

from kanban_tui.database import get_ordered_tasks_db


class TaskPlot(HorizontalScroll):
    app: "KanbanTui"

    def _on_mount(self, event: Mount) -> None:
        self.update_task_plot(show_categories=True)
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        yield PlotextPlot()
        self.border_title = "Tasks Completed"
        return super().compose()

    def update_task_plot(self, show_categories: bool = False):
        plt = self.query_one(PlotextPlot).plt
        if show_categories:
            ordered_tasks = get_ordered_tasks_db(
                order_by="start_date", database=self.app.cfg.database_path
            )
            if not ordered_tasks:
                return

            start_dates = [
                task.start_date.strftime("%b %Y")
                for task in ordered_tasks
                if task.start_date
            ]
            if not start_dates:
                return

            counts1 = [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1],
                [2, 3, 0, 1, 0, 1, 0, 1, 1, 1, 1],
            ]

            plt.stacked_bar(
                start_dates,
                counts1,
                label=["A", "B", "C"],
                width=0.5,
                reset_ticks=True,
                minimum=0,
            )

        else:
            ordered_tasks = get_ordered_tasks_db(
                order_by="start_date", database=self.app.cfg.database_path
            )
            if not ordered_tasks:
                return
            start_dates = [
                task.start_date.strftime("%b %Y")
                for task in ordered_tasks
                if task.start_date
            ]
            counts = Counter(start_dates)

            plt.bar(
                counts.keys(), counts.values(), width=0.5, reset_ticks=True, minimum=0
            )
        plt.horizontal_line(coordinate=2, color="red")
        plt.yfrequency(frequency=5)
        plt.xlabel("Date")
        plt.ylabel("Count")
        # plt.title("Task Amount")


class PlotFilter(Horizontal):
    app: "KanbanTui"

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        yield Label("Show Category Detail")
        yield Switch(
            value=False,
            id="switch_plot_category_detail",
        )
        return super().compose()
