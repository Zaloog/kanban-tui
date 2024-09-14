import datetime
from typing import Iterable, TYPE_CHECKING
from collections import Counter

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual.binding import Binding

# from rich.color import Color
from textual.widget import Widget
from textual.widgets import Label, Switch, Select
from textual_plotext import PlotextPlot
from textual.containers import HorizontalScroll, Vertical
from textual.widgets._select import SelectOverlay

from kanban_tui.database import get_ordered_tasks_db
from kanban_tui.color_converter import getrgb


class TaskPlot(HorizontalScroll):
    app: "KanbanTui"
    can_focus = False

    def compose(self) -> Iterable[Widget]:
        yield PlotextPlot()
        self.border_title = "Tasks Completed"
        return super().compose()

    async def update_task_plot(
        self,
        switch_categories: bool,
        select_frequency: str,
        select_amount: str,
        scroll_reset: bool = True,
    ):
        await self.recompose()
        plt = self.query_one(PlotextPlot).plt

        ordered_tasks = get_ordered_tasks_db(
            order_by=select_amount, database=self.app.cfg.database_path
        )
        self.log.error(f"{ordered_tasks}")
        if not ordered_tasks:
            self.query_one(PlotextPlot).styles.width = "1fr"
            return

        earliest: datetime.datetime = min([task["date"] for task in ordered_tasks])
        match select_frequency:
            case "day":
                plt.date_form("d-b-Y")
                plt.xlabel("Date")
                date_range = [
                    earliest + datetime.timedelta(days=day)
                    for day in range(0, (datetime.datetime.now() - earliest).days + 1)
                ]
                date_range = plt.datetimes_to_string(date_range)
            case "week":
                plt.date_form("V-Y")
                plt.xlabel("Week-Year")
                date_range = [
                    earliest + datetime.timedelta(weeks=week)
                    for week in range(
                        0, (datetime.datetime.now() - earliest).days // 7 + 1
                    )
                ]
                date_range = plt.datetimes_to_string(date_range)
            case "month":
                plt.date_form("b-Y")
                plt.xlabel("Month-Year")
                date_range = [
                    earliest.replace(month=earliest.month + month)
                    for month in range(
                        0, (datetime.datetime.now().month - earliest.month) + 1
                    )
                ]
                date_range = plt.datetimes_to_string(date_range)

        self.query_one(PlotextPlot).styles.width = len(date_range) * 15

        plot_values = {date: 0 for date in date_range}

        if switch_categories:
            category_value_dict = {}
            # Add None Values
            for category in self.app.cfg.category_color_dict.keys():
                category_value_dict[category] = plot_values.copy()
                # self.log.error(f"valdict {category}: {val_dict[category]}")

                category_value_dict[category].update(
                    Counter(
                        [
                            plt.datetime_to_string(task["date"])
                            for task in ordered_tasks
                            if task["category"] == category
                        ]
                    )
                )
            #     self.log.error(f"valdict {category}: {category_value_dict[category]}")
            #     self.log.error(f"len {len(plot_values.keys())}")

            # self.log.error(f"valdict {len(category_value_dict)}: {[(cat, len(val)) for cat, val in category_value_dict.items()]}")
            plt.stacked_bar(
                plot_values.keys(),
                [
                    category_values.values()
                    for category_values in category_value_dict.values()
                ],
                label=[category for category in category_value_dict.keys()],
                color=[
                    getrgb(self.app.cfg.category_color_dict[category])
                    for category in category_value_dict.keys()
                ],
                width=0.5,
                minimum=0,
            )

        else:
            task_dates = plt.datetimes_to_string(
                sorted({task["date"] for task in ordered_tasks})
            )
            task_counts = Counter(task_dates)
            plot_values.update(task_counts)

            plt.bar(
                plot_values.keys(),
                plot_values.values(),
                width=0.5,
                reset_ticks=True,
                minimum=0,
            )

        if scroll_reset:
            self.set_timer(
                delay=0.1,
                callback=lambda: self.scroll_to(x=self.max_scroll_x, animate=False),
            )

    def scroll_left(
        self,
        *,
        animate: bool = True,
        speed: float | None = None,
        duration: float | None = None,
        easing: str | None = None,
        force: bool = False,
        on_complete: None = None,
        level="basic",
    ) -> None:
        self.scroll_to(
            x=self.scroll_target_x - 3,
            animate=animate,
            speed=speed,
            duration=duration,
            easing=easing,
            force=force,
            on_complete=on_complete,
            level=level,
        )

    def scroll_right(
        self,
        *,
        animate: bool = True,
        speed: float | None = None,
        duration: float | None = None,
        easing: str | None = None,
        force: bool = False,
        on_complete: None = None,
        level="basic",
    ) -> None:
        self.scroll_to(
            x=self.scroll_target_x + 3,
            animate=animate,
            speed=speed,
            duration=duration,
            easing=easing,
            force=force,
            on_complete=on_complete,
            level=level,
        )


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
            id="select_plot_filter_frequency",
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
                ("Completion Date", "finish_date"),
            ],
            start_value="start_date",
            id="select_plot_filter_amount",
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

    def __init__(self, options: Iterable, start_value: str, id: str | None = None):
        super().__init__(options=options, allow_blank=False, value=start_value, id=id)

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
