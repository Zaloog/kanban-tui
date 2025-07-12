from __future__ import annotations

import pendulum

from textual.app import ComposeResult
from textual.widget import Widget, events
from textual.containers import Vertical
from textual.reactive import reactive
from textual.css.query import NoMatches

# from textual import log

from . import DatePicker


class DatePickerDialog(Widget):
    """The dialog/menu which opens below the DateSelect."""

    DEFAULT_CSS = """
    DatePickerDialog {
        layer: dialog;
        background: $boost;
        width: 30;
        height: 17;
        border: tall $accent;
        display: none;
    }
    """

    # The DatePicker mounted in this dialog.
    date_picker = None

    # A target where to send the message for a selected date
    target = None

    def compose(self) -> ComposeResult:
        self.date_picker = DatePicker()
        self.date_picker.target = self.target
        yield Vertical(self.date_picker)

    def on_descendant_blur(self, event: events.DescendantBlur) -> None:
        if len(self.query("*:focus-within")) == 0:
            self.display = False

    def on_date_picker_selected(self, event: DatePicker.Selected) -> None:
        self.display = False

        if self.target is not None:
            self.target.focus()


class DateSelect(Widget, can_focus=True):
    """A select widget which opens the DatePicker and displays the selected date."""

    DEFAULT_CSS = """
    DateSelect {
      background: $boost;
      color: $text;
      padding: 0 2;
      border: tall $background;
      height: 1;
      min-height: 1;
    }
    DateSelect:focus {
      border: tall $accent;
    }
    """

    # The value displayed in the select (which is the date)
    # value = reactive("", layout=True, init=False)

    # Date of the month which shall be shown when opening the dialog
    date: reactive[pendulum.DateTime | None] = reactive(None)

    def __init__(
        self,
        picker_mount: str,
        date: pendulum.DateTime | None = None,
        format: str = "YYYY-MM-DD",
        placeholder: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.picker_mount = picker_mount
        self.placeholder = placeholder
        self.format = format

        if date is not None:
            self.date = date

        # DatePickerDialog widget
        self.dialog = None

    @property
    def value(self) -> pendulum.DateTime:
        """Value of the current date."""
        return self.date

    def render(self) -> str:
        chevron = "\u25bc"
        width = self.content_size.width
        text_space = width - 2

        if text_space < 0:
            text_space = 0

        if not self.date:
            text = self.placeholder
        else:
            text = self.date.format(self.format)

        if len(text) > text_space:
            text = text[0:text_space]

        text = f"{text:{text_space}} {chevron}"

        return text

    def on_mount(self) -> None:
        if self.dialog is None:
            self.dialog = DatePickerDialog()
            self.dialog.target = self
            self.app.screen.query_one(self.picker_mount).mount(self.dialog)

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self._show_date_picker()

    def on_click(self, event: events.MouseEvent) -> None:
        self._show_date_picker()

    def on_blur(self) -> None:
        pass

    def on_date_picker_selected(self, event: DatePicker.Selected) -> None:
        self.date = event.date

    def _show_date_picker(self) -> None:
        mnt_widget = self.app.screen.query_one(self.picker_mount)
        self.dialog.display = True

        # calculate offset of DateSelect and apply it to DatePickerDialog
        self.dialog.offset = self.region.offset - mnt_widget.content_region.offset

        # move down 3 (height of input)
        # TODO: should be dynamic for smaller inputs
        self.dialog.offset = (self.dialog.offset.x, self.dialog.offset.y + 3)

        if self.date is not None:
            if self.date is not None:
                self.dialog.date_picker.date = self.date
            for day in self.dialog.query("DayLabel.--day"):
                if day.day == self.date.day:
                    day.focus()
                    break
        else:
            try:
                self.dialog.query_one("DayLabel.--today").focus()
            except NoMatches:  # pragma: no cover
                # should never happen, because DatePicker always opens this
                # month without a given date. just to be sure,
                # catching query_one fails.
                self.dialog.query("DayLabel.--day").first().focus()
