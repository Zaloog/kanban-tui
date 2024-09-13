from typing import Iterable, TYPE_CHECKING
from collections import Counter

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.binding import Binding
from textual.events import Mount
from textual.widget import Widget
from textual.widgets import Label, Switch, Select
from textual_plotext import PlotextPlot
from textual.containers import HorizontalScroll, Vertical
from textual.widgets._select import SelectOverlay

from kanban_tui.database import get_ordered_tasks_db


class TaskPlot(HorizontalScroll):
    app: "KanbanTui"

    def _on_mount(self, event: Mount) -> None:
        # self.update_task_plot(show_categories=True)
        self.watch(
            self.app, "task_list", lambda: self.update_task_plot(show_categories=False)
        )
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        yield PlotextPlot()
        self.border_title = "Tasks Completed"
        return super().compose()

    async def update_task_plot(self, show_categories: bool = False):
        await self.query_one(PlotextPlot).remove()
        await self.mount(PlotextPlot())
        plt = self.query_one(PlotextPlot).plt
        plt.date_form("b-Y")

        if show_categories:
            ordered_tasks = get_ordered_tasks_db(
                order_by="start_date", database=self.app.cfg.database_path
            )
            self.log.error(f"{ordered_tasks}")
            if not ordered_tasks:
                return

            # start_dates = sorted(list(set(task['month'] for task in ordered_tasks)))
            start_dates = plt.datetimes_to_string(
                sorted({task["start_date"] for task in ordered_tasks})
            )

            # for date in dates:
            #     for i_color, color in enumerate(self.app.cfg.category_color_dict.values()):
            #         entry_dict[entry]

            # start_dates = [
            #     task.start_date.strftime("%b %Y")
            #     for task in ordered_tasks
            #     if task.start_date
            # ]
            if not start_dates:
                return

            counts1 = [
                [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
                [2, 3, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1],
            ]

            plt.stacked_bar(
                start_dates,
                counts1,
                label=["A", "B", "C"],
                width=0.5,
                # reset_ticks=True,
                minimum=0,
            )

        else:
            ordered_tasks = get_ordered_tasks_db(
                order_by="start_date", database=self.app.cfg.database_path
            )
            if not ordered_tasks:
                return
            start_dates = plt.datetimes_to_string(
                sorted({task["start_date"] for task in ordered_tasks})
            )
            counts = Counter(start_dates)

            plt.bar(
                counts.keys(), counts.values(), width=0.5, reset_ticks=True, minimum=0
            )
        # plt.horizontal_line(coordinate=2, color="red")
        # plt.yfrequency(frequency=len(), yside=1)
        plt.xlabel("Date")
        # plt.title("Task Amount")


class CategoryPlotFilter(Vertical):
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


class FrequencyPlotFilter(Vertical):
    app: "KanbanTui"

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        yield Label("Select Detail Level")
        yield PlotOptionSelector(
            options=[
                ("Day", "day"),
                ("Week", "week"),
                ("Month", "month"),
            ],
            start_value="month",
        )
        return super().compose()


class AmountPlotFilter(Vertical):
    app: "KanbanTui"

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        yield Label("Select KPI")
        yield PlotOptionSelector(
            options=[
                ("Creation Date", "creation_date"),
                ("Start Date", "start_date"),
                ("Completion Date", "completion_date"),
            ],
            start_value="start_date",
        )
        return super().compose()


class PlotOptionSelector(Select):
    app: "KanbanTui"
    # thanks Darren (https://github.com/darrenburns/posting/blob/main/src/posting/widgets/select.py)
    BINDINGS = [
        Binding("enter,space,l", "show_overlay", "Show Overlay", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]

    def __init__(self, options: Iterable, start_value: str):
        super().__init__(options=options, allow_blank=False, value=start_value)

    def action_cursor_up(self):
        if self.expanded:
            self.query_one(SelectOverlay).action_cursor_up()
        else:
            self.screen.focus_previous()

    def action_cursor_down(self):
        if self.expanded:
            self.query_one(SelectOverlay).action_cursor_down()
        else:
            self.screen.focus_next()
