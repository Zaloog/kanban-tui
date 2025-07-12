from __future__ import annotations

import calendar
import pendulum

from textual.app import ComposeResult
from textual.widget import Widget, RenderableType, events
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.css.query import NoMatches
from textual.message import Message

# from textual import log


class MonthControl(Button, can_focus=True):
    DEFAULT_CSS = """
    MonthControl {
        height: 1;
        border: none;
    }
    MonthControl.-active,
    MonthControl:hover {
        border: none;
    }
    """
    pass


class MonthHeader(Static):
    DEFAULT_CSS = """
    MonthHeader {
        width: 20;
        content-align: center top;
        text-align: center;
        text-style: bold;
    }
    MonthHeader:focus {
        text-style: bold reverse;
    }
    """

    # the date format to use for displaying the label
    format = "MMMM\nYYYY"

    def __init__(
        self,
        date: pendulum.DateTime,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.renderable = date.format(self.format)

    def update(self, date: pendulum.DateTime) -> None:
        super().update(date.format(self.format))

    # def on_key(self, event: events.Key) -> None:
    #     if event.key == "enter":
    #         self.emit_no_wait(self.Selected(self))

    # class Selected(Message):
    #     """The MonthHeader was selected."""
    #     pass


class WeekdayContainer(Horizontal):
    pass


class DayContainer(Horizontal):
    pass


class WeekdayLabel(Static):
    pass


class DayLabel(Widget):
    def __init__(
        self,
        label: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.label = label
        if int(label) == 0:
            self.can_focus = False
        else:
            self.can_focus = True
            self.add_class("--day")

    @property
    def day(self):
        if int(self.label) > 0:
            return int(self.label)
        return None

    def render(self) -> RenderableType:
        if int(self.label) == 0:
            output = "  "
        else:
            output = f"{self.label:>2}"

        return output

    def update(self, label: str) -> None:
        if int(label) == 0:
            if self.has_focus:
                self.post_message(self.FocusLost(self, int(self.label)))
            self.can_focus = False
            self.remove_class("--day")
        else:
            self.can_focus = True
            self.add_class("--day")
        self.label = label
        self.refresh(layout=True)

    def on_focus(self, _event: events.Focus) -> None:
        self.post_message(self.Focused(self))

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.post_message(self.Selected(self, int(self.label)))

    def on_click(self, event: events.MouseEvent) -> None:
        if int(self.label) == 0:
            return

        self.post_message(self.Selected(self, int(self.label)))

    class Focused(Message):
        def __init__(self, sender):
            super().__init__()
            self.sender = sender

    class FocusLost(Message):
        """A focusable day have become an unfocusable one."""

        def __init__(self, sender: DayLabel, day: int) -> None:
            # day: the old day which had the focus
            self.day = day
            super().__init__()

    class Selected(Message):
        """A day was selected."""

        def __init__(self, sender: DayLabel, day: int) -> None:
            self.day = day
            super().__init__()


class DatePicker(Widget):
    DEFAULT_CSS = """
    DatePicker {
        width: 26;
        height: 15;
        box-sizing: content-box;
        /*border: solid $panel;*/
        padding: 0 1;
    }
    DatePicker .header {
        height: 2;
    }
    DatePicker WeekdayContainer,
    DatePicker DayContainer {
        layout: grid;
        grid-size: 7;
        grid-columns: 2;
        grid-rows: 1;
        grid-gutter: 1 2;
    }
    DatePicker MonthControl {
        width: 3;
        max-width: 3;
    }
    DatePicker WeekdayContainer {
        height: 2;
    }
    DatePicker WeekdayLabel {
        color: $text-muted;
    }
    DatePicker DayLabel {
        content-align: right top;
    }
    DatePicker DayLabel:focus {
        text-style: bold reverse;
    }
    DatePicker DayLabel.--today {
        color: $secondary-lighten-1;
        text-style: bold;
    }
    DatePicker DayLabel.--today:focus {
        text-style: bold reverse;
    }
    DatePicker DayLabel.--day:hover {
        background: $surface-lighten-2;
    }
    """

    # label on the top with month and year
    month_label = Static("", classes="month")

    # the displayed month (always the first of the month)
    date = reactive(pendulum.today().start_of("month"))

    # The index of the focused day as int (including empty leading days)
    focused: int | None

    # The selected date (on enter, click)
    selected_date: pendulum.DateTime | None

    # Container with all the selectable days
    day_container = None

    # A target widget where to send the message for a selected date
    target: Widget | None = None

    def __init__(self):
        super().__init__()

    @property
    def focused_day(self) -> DayLabel | None:
        try:
            return self.query_one("DayLabel:focus")
        except NoMatches:
            return None

    def compose(self) -> ComposeResult:
        self.day_container = DayContainer(*self._build_day_widgets())
        yield Vertical(
            Horizontal(
                MonthControl("<", classes="left"),
                MonthHeader(date=self.date),
                MonthControl(">", classes="right"),
                classes="header",
            ),
            WeekdayContainer(*self._build_weekday_widgets()),
            self.day_container,
        )

    def watch_date(self, _old_date, _new_date) -> None:
        self._update_month_label()
        self._update_day_widgets()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.has_class("left"):
            self._prev_month()
        if event.button.has_class("right"):
            self._next_month()

    def on_day_label_focused(self, event: DayLabel.Focused) -> None:
        self.focused = self.day_container.children.index(event.sender)

    def on_day_label_focus_lost(self, event: DayLabel.FocusLost) -> None:
        """The previous focused day is no longer focusable on this position.
        If it was at the end of a month, set it to end of the 4th row, there
        is always a focusable day. Otherwise to the first on the 2nd row.
        """
        if event.day >= 28:
            self.day_container.children[27].focus()
        else:
            self.day_container.children[7].focus()

    def on_day_label_selected(self, event: DayLabel.Selected) -> None:
        self.selected_date = pendulum.datetime(
            self.date.year, self.date.month, event.day
        )

        self.post_message(self.Selected(self, self.selected_date))

        if self.target is not None:
            self.target.post_message(self.Selected(self, self.selected_date))

    def on_key(self, event: events.Key) -> None:
        if event.key == "pageup":
            event.prevent_default()
            self._prev_month()
        if event.key == "pagedown":
            event.prevent_default()
            self._next_month()
        if event.key == "left":
            event.prevent_default()
            self._handle_left()
        if event.key == "right":
            event.prevent_default()
            self._handle_right()
        if event.key == "down":
            event.prevent_default()
            self._handle_down()
        if event.key == "up":
            event.prevent_default()
            self._handle_up()
        if event.key == "home":
            event.prevent_default()
            self._handle_home()

    def _prev_month(self) -> None:
        self._move_month(-1)

    def _next_month(self) -> None:
        self._move_month(1)

    def _move_month(self, month_count: int) -> None:
        self.date = pendulum.datetime(self.date.year, self.date.month, 1).add(
            months=month_count
        )

    def _handle_left(self) -> None:
        focused_day = self.focused_day
        if focused_day is None:
            return

        nudging = False

        if focused_day.day == 1:
            nudging = True
        elif self.focused % 7 == 0:
            nudging = True

        if nudging:
            self._prev_month()
        else:
            self.day_container.children[self.focused - 1].focus()

    def _handle_right(self) -> None:
        focused_day = self.focused_day
        if focused_day is None:
            return

        nudging = False

        if self.focused % 7 == 6:
            nudging = True
        elif focused_day.day >= 28:
            # 28 could be last day of month, check for an empty day at next index.
            # index can't be out of range because there is always an empty day
            # at the right
            if self.day_container.children[self.focused + 1].day is None:
                nudging = True

        if nudging:
            self._next_month()
        else:
            self.day_container.children[self.focused + 1].focus()

    def _handle_down(self) -> None:
        focused_day = self.focused_day
        if focused_day is None:
            return

        nudging = False

        if focused_day.day >= 28 - 7:
            # from 21, we always can go to 28. only check for days after.
            try:
                # if day at index +7 is None, it's nudging
                # also if there is no index
                if self.day_container.children[self.focused + 7].day is None:
                    nudging = True
            except IndexError:
                nudging = True

        if nudging:
            return

        self.day_container.children[self.focused + 7].focus()

    def _handle_up(self) -> None:
        focused_day = self.focused_day
        if focused_day is None:
            return

        nudging = False

        if focused_day.day <= 7:
            nudging = True

        if nudging:
            return

        self.day_container.children[self.focused - 7].focus()

    def _handle_home(self) -> None:
        self.date = pendulum.today()
        self.query_one("DayLabel.--today").focus()

    def _update_month_label(self) -> None:
        try:
            month_label = self.query_one(MonthHeader)
        except NoMatches:
            # not yet composed, do nothing
            return
        month_label.update(date=self.date)

    def _build_weekday_widgets(self) -> [WeekdayLabel]:
        widgets = []
        weekdays = calendar.weekheader(2).split(" ")
        for day in weekdays:
            widgets.append(WeekdayLabel(day))

        return widgets

    def _build_day_widgets(self) -> [DayLabel]:
        day_widgets = []
        today_day = self._today_in_month()

        days = calendar.monthcalendar(year=self.date.year, month=self.date.month)
        days = [day for week in days for day in week]

        for idx in range(42):
            # 42: 6 rows with 7 days
            if idx < len(days):
                if today_day == days[idx]:
                    classes = "--today"
                else:
                    classes = ""
                day_widgets.append(DayLabel(days[idx], classes=classes))
            else:
                day_widgets.append(DayLabel(0))

        return day_widgets

    def _update_day_widgets(self) -> None:
        today_day = self._today_in_month()

        days = calendar.monthcalendar(year=self.date.year, month=self.date.month)
        days = [day for week in days for day in week]

        for idx, day_label in enumerate(self.query("DayContainer DayLabel")):
            if idx < len(days):
                day_label.set_class(today_day == days[idx], "--today")
                day_label.update(days[idx])
            else:
                day_label.update(0)

    def _today_in_month(self) -> int | None:
        """Returns todays day, if today is in the current month (self.date).
        None otherwise."""

        today = pendulum.today()
        if today.year == self.date.year and today.month == self.date.month:
            return today.day

        return None

    class Selected(Message):
        """A date was selected."""

        def __init__(self, sender: DatePicker, date: pendulum.DateTime) -> None:
            self.date = date
            super().__init__()
