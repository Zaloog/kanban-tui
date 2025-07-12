from pendulum import DateTime

from textual.binding import Binding

from kanban_tui.textual_datepicker import DateSelect, DatePicker
from kanban_tui.textual_datepicker._date_select import DatePickerDialog


class CustomDatePickerDialog(DatePickerDialog):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
        Binding("escape", "close_dialog", "Close", show=False),
    ]

    def action_close_dialog(self):
        self.display = False
        self.target.focus()

    def action_cursor_up(self):
        if self.display:
            self.query_one(DatePicker)._handle_up()
        else:
            self.screen.focus_previous()

    def action_cursor_down(self):
        if self.display:
            self.query_one(DatePicker)._handle_down()
        else:
            self.screen.focus_next()

    def action_cursor_right(self):
        if self.display:
            self.query_one(DatePicker)._handle_right()
        else:
            self.screen.focus_next()

    def action_cursor_left(self):
        if self.display:
            self.query_one(DatePicker)._handle_left()
        else:
            self.screen.focus_next()


class CustomDateSelect(DateSelect):
    BINDINGS = [
        Binding("space,l", "show_overlay", "Show Overlay", show=False),
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]

    def __init__(
        self,
        picker_mount: str,
        date: DateTime | None = None,
        format: str = "YYYY-MM-DD",
        placeholder: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(picker_mount, date, format, placeholder, name, id, classes)
        self.dialog = CustomDatePickerDialog()
        self.dialog.target = self
        self.app.screen.query_one(self.picker_mount).mount(self.dialog)

    def action_show_overlay(self):
        if self.dialog.display:
            self.dialog.display = False
        else:
            self._show_date_picker()

    def action_cursor_up(self):
        self.screen.focus_previous()

    def action_cursor_down(self):
        self.screen.focus_next()
