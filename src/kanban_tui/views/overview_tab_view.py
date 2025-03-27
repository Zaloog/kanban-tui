from typing import Iterable
from textual import on
from textual.reactive import reactive
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Select, Switch, TabbedContent, TabPane, Button
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.overview_widgets import (
    TaskPlot,
    CategoryPlotFilter,
    AmountPlotFilter,
    FrequencyPlotFilter,
    LogEventTypeFilter,
    LogObjectTypeFilter,
    LogDateFilter,
    LogTable,
)


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
        return super().compose()

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
        return super().compose()

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
