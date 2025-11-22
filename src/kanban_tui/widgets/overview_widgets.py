import datetime
from typing import Iterable, TYPE_CHECKING
from collections import Counter


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Label,
    Switch,
    Button,
    Select,
    TabbedContent,
    TabPane,
)
from textual.reactive import reactive
from textual.containers import Horizontal, HorizontalScroll, Vertical
from textual.widgets._select import SelectOverlay
from textual_plotext import PlotextPlot

from kanban_tui.utils import getrgb, get_time_range
from kanban_tui.classes.logevent import LogEvent
from kanban_tui.widgets.modal_task_widgets import VimSelect


class TaskPlot(HorizontalScroll):
    app: "KanbanTui"
    can_focus = False

    def compose(self) -> Iterable[Widget]:
        yield PlotextPlot(id="plot_widget")
        self.border_title = "Task Amount"
        return super().compose()

    async def update_task_plot(
        self,
        switch_categories: bool,
        select_amount: str,
        select_frequency: str,
        scroll_reset: bool = True,
    ):
        await self.recompose()
        plt = self.query_one(PlotextPlot).plt

        ordered_tasks = self.app.backend.get_ordered_tasks(
            order_by=select_amount,
        )
        if not ordered_tasks:
            self.query_one(PlotextPlot).styles.width = "1fr"
            return

        earliest: datetime.datetime = min([task["date"] for task in ordered_tasks])
        latest: datetime.datetime = max([task["date"] for task in ordered_tasks])
        match select_frequency:
            case "day":
                plt.date_form("d-b-Y")
                plt.xlabel("Date")
                date_range = get_time_range(interval="day", start=earliest, end=latest)
            case "week":
                plt.date_form("V-Y")
                plt.xlabel("Week-Year")
                date_range = get_time_range(interval="week", start=earliest, end=latest)
            case "month":
                plt.date_form("b-Y")
                plt.xlabel("Month-Year")
                date_range = get_time_range(
                    interval="month", start=earliest, end=latest
                )

        date_range = plt.datetimes_to_strings(date_range)
        # Adjust Plotext size, if there are only a few entries
        if len(date_range) < 12:
            self.query_one(PlotextPlot).styles.width = "1fr"
        else:
            self.query_one(PlotextPlot).styles.width = len(date_range) * 15

        plot_values = {date: 0 for date in date_range}

        if switch_categories:
            category_value_dict = {}

            for category in set(task.category for task in self.app.task_list):
                category_value_dict[category] = plot_values.copy()

                task_counter = Counter(
                    [
                        plt.datetime_to_string(task["date"])
                        for task in ordered_tasks
                        if task["category"] == category
                    ]
                )
                category_value_dict[category].update(task_counter)

            # plot
            plt.stacked_bar(
                list(plot_values.keys()),
                [
                    category_values.values()
                    for _category, category_values in category_value_dict.items()
                    if sum(category_values.values()) > 0
                ],
                labels=[
                    self.app.backend.get_category_by_id(category_id).name
                    if category_id
                    else "No Category"
                    for category_id, category_values in category_value_dict.items()
                    if sum(category_values.values()) > 0
                ],
                color=[
                    getrgb(
                        self.app.backend.get_category_by_id(category).color
                        if category
                        else self.app.config.task.default_color
                    )
                    for category, category_values in category_value_dict.items()
                    if sum(category_values.values()) > 0
                ],
                width=0.5,
                yside="2",
                reset_ticks=True,
                fill=True,
                minimum=0,
            )

        else:
            task_dates = plt.datetimes_to_strings(
                {task["date"] for task in ordered_tasks}
            )
            task_counter = Counter(task_dates)
            plot_values.update(task_counter)

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

    def compose(self) -> Iterable[Widget]:
        yield Label(
            Text.from_markup(":magnifying_glass_tilted_right: Select Category Detail")
        )
        yield Switch(
            value=False,
            id="switch_plot_category_detail",
        )
        return super().compose()


class FrequencyPlotFilter(Vertical):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label(
            Text.from_markup(":magnifying_glass_tilted_right: Select Detail Level")
        )
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

    def compose(self) -> Iterable[Widget]:
        yield Label(Text.from_markup(":magnifying_glass_tilted_right: Select KPI"))
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


class PlotOptionSelector(VimSelect):
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


class LogFilterButton(Button):
    active: reactive[bool] = reactive(True)

    def watch_active(self):
        self.variant = "success" if self.active else "error"

    def on_button_pressed(self):
        self.active = not self.active


class LogEventTypeFilter(Vertical):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label(Text.from_markup(":magnifying_glass_tilted_right: Select Event"))
        with Horizontal():
            yield LogFilterButton("CREATE", variant="success")
            yield LogFilterButton("UPDATE", variant="success")
            yield LogFilterButton("DELETE", variant="success")


class LogObjectTypeFilter(Vertical):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label(Text.from_markup(":magnifying_glass_tilted_right: Select Object"))
        with Horizontal():
            yield LogFilterButton("board", variant="success")
            yield LogFilterButton("column", variant="success")
            yield LogFilterButton("task", variant="success")


class LogDateFilter(Vertical):
    app: "KanbanTui"

    def compose(self) -> Iterable[Widget]:
        yield Label(Text.from_markup(":magnifying_glass_tilted_right: Select Time"))
        yield VimSelect(
            options=[
                ("all", datetime.datetime(1970, 1, 1)),
                (
                    "yesterday",
                    (datetime.datetime.now() - datetime.timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                ),
                (
                    "last week",
                    (datetime.datetime.now() - datetime.timedelta(days=7)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                ),
                (
                    "last month",
                    (datetime.datetime.now() - datetime.timedelta(days=30)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                ),
            ],
            id="select_logdate_filter",
            allow_blank=False,
        )


class LogTable(Vertical):
    app: "KanbanTui"
    events: reactive[list[LogEvent]] = reactive([])

    def compose(self):
        yield DataTable(cursor_type="row", zebra_stripes=True, id="datatable_logs")

    def on_mount(self):
        self.border_title = "Audit Log"
        self.query_one(DataTable).add_columns(
            "event_time",
            "event_type",
            "object_type",
            "object_id",
            "object_field",
            "old",
            "new",
        )

    def load_events(self, events: list[str], objects: list[str], time: str):
        filter_dict = {"events": events, "objects": objects, "time": time}
        self.events = self.app.backend.get_filtered_events(
            filter=filter_dict,
        )

    def watch_events(self):
        self.query_one(DataTable).clear()

        for event in self.events:
            event_dict = event.__dict__
            self.query_one(DataTable).add_row(
                *list(event_dict.values())[1:], label=list(event_dict.values())[0]
            )

        self.query_one(DataTable).move_cursor(row=len(self.events))


class OverView(Horizontal):
    BINDINGS = [
        Binding("P", 'show_tab("tab_plot")', "Plot", show=True),
        Binding("L", 'show_tab("tab_log")', "Log", show=True),
    ]

    def compose(self):
        with TabbedContent(initial="tab_log", id="tabbed_content_overview"):
            with TabPane("[yellow on black]P[/]lot", id="tab_plot"):
                yield OverViewPlot()
            with TabPane("[yellow on black]L[/]og", id="tab_log"):
                yield OverViewLog()

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.query_one("#tabbed_content_overview").active = tab
        self.app.action_focus_next()


class OverViewPlot(Vertical):
    BINDINGS = [
        Binding("J", "scroll_plot_left", "Scroll Left", show=True),
        Binding("K", "scroll_plot_right", "Scroll Right", show=True),
    ]

    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_overview_filters"):
            yield CategoryPlotFilter(classes="overview-filter")
            yield AmountPlotFilter(classes="overview-filter")
            yield FrequencyPlotFilter(classes="overview-filter")
        yield TaskPlot()

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


class OverViewLog(Vertical):
    BINDINGS = [
        Binding("j", "table_down", "Scroll Down", show=True, priority=True),
        Binding("k", "table_up", "Scroll UP", show=True, priority=True),
    ]

    active_event_types: reactive[list[str]] = reactive(["CREATE", "UPDATE", "DELETE"])
    active_object_types: reactive[list[str]] = reactive(["board", "task", "column"])
    active_timestamp: reactive[str] = reactive("1970-01-01 00:00:00")

    def on_mount(self):
        self.query_one(LogTable).load_events(
            events=self.active_event_types,
            objects=self.active_object_types,
            time=self.active_timestamp,
        )

    def compose(self) -> Iterable[Widget]:
        with Horizontal(id="horizontal_overview_filters"):
            yield LogDateFilter(classes="overview-filter")
            yield LogEventTypeFilter(classes="overview-filter")
            yield LogObjectTypeFilter(classes="overview-filter")
        yield LogTable()

    def on_button_pressed(self, event: Button.Pressed):
        tmp_event_list = []
        for button in self.query_one(LogEventTypeFilter).query(Button):
            if button.active:
                tmp_event_list.append(f"{button.label}")

        tmp_object_list = []
        for button in self.query_one(LogObjectTypeFilter).query(Button):
            if button.active:
                tmp_object_list.append(f"{button.label}")

        self.active_event_types = tmp_event_list
        self.active_object_types = tmp_object_list

    def on_select_changed(self, event: Select.Changed):
        self.active_timestamp = event.select.value

    def action_table_down(self):
        self.query_one("#datatable_logs").action_cursor_down()

    def action_table_up(self):
        self.query_one("#datatable_logs").action_cursor_up()

    def watch_active_event_types(self):
        self.query_one(LogTable).load_events(
            events=self.active_event_types,
            objects=self.active_object_types,
            time=self.active_timestamp,
        )

    def watch_active_object_types(self):
        self.query_one(LogTable).load_events(
            events=self.active_event_types,
            objects=self.active_object_types,
            time=self.active_timestamp,
        )

    def watch_active_timestamp(self):
        self.query_one(LogTable).load_events(
            events=self.active_event_types,
            objects=self.active_object_types,
            time=self.active_timestamp,
        )
