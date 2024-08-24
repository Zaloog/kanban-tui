from typing import Iterable

from textual.widget import Widget
from textual.widgets import Placeholder, Button
from textual.containers import Vertical


class FilterOverlay(Vertical):
    can_focus: bool = False
    can_focus_children: bool = False
    classes: str = "-hidden"

    def __init__(self) -> None:
        super().__init__(classes=self.classes)

    def compose(self) -> Iterable[Widget]:
        yield Placeholder("Cool Filter")
        yield Button("Cool button")
        yield Button("Cool button2")
        return super().compose()
