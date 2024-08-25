from typing import Iterable

from textual.widget import Widget
from textual.reactive import reactive
from textual.widgets import Placeholder, Button, Label
from textual.message import Message
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.date_select import CustomDateSelect


class FilterOverlay(Vertical):
    can_focus: bool = False
    can_focus_children: bool = False
    classes: str = "-hidden"
    filter: reactive[dict] = reactive({"categories": [], "order": "", "due_date": (0,)})

    class Apply(Message):
        def __init__(self) -> None:
            super().__init__()

    def __init__(self) -> None:
        super().__init__(classes=self.classes, id="overlay_filter")

    def compose(self) -> Iterable[Widget]:
        yield Placeholder("Cool Filter")
        # Filters:
        # - Categories: select list? /Checkbox in Collapsible
        # - Sort by: Days Left, creation_date, Categories

        # Apply Button (Preview like show 7/29 cards)
        yield Label("Filter Tasks")
        yield DateFilter()
        # Or a Switch
        yield Button("Cool button", id="btn_test")
        # Reset Filter Button
        yield Button("Cool button2")
        return super().compose()


class DateFilter(Vertical):
    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            yield Label("From")
            yield CustomDateSelect(
                placeholder="please select",
                format="YYYY-MM-DD",
                picker_mount="#overlay_filter",
                id="dateselect_start",
            )
        with Horizontal():
            yield Label("To")
            yield CustomDateSelect(
                placeholder="please select",
                format="YYYY-MM-DD",
                picker_mount="#overlay_filter",
                id="dateselect_end",
            )
        return super().compose()
