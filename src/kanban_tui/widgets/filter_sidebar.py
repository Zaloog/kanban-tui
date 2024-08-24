from typing import Iterable

from textual.widget import Widget
from textual.widgets import Placeholder, Button
from textual.containers import Vertical


class FilterOverlay(Vertical):
    def compose(self) -> Iterable[Widget]:
        yield Placeholder("Cool Filter")
        yield Button("Cool button")
        return super().compose()
