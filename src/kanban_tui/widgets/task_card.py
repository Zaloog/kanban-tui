from textual import on
from textual.reactive import reactive
from textual.events import Enter, Leave
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, TextArea


class TaskCard(Vertical):
    expanded: reactive[bool] = reactive(False)

    def __init__(self, title: str | None = None, id: str | None = None) -> None:
        self.title = title
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Label(f"Task_{self.title}")
        yield TextArea(
            "Body",
            # id=f"body_task{self.title}",
            classes="hide",
        )
        return super().compose()

    @on(Enter)
    @on(Leave)
    def show_details(self) -> None:
        if self.is_mouse_over:
            self.expanded = True
        else:
            self.expanded = False

    def watch_expanded(self):
        if self.expanded:
            self.query_one(TextArea).remove_class("hide")
        else:
            self.query_one(TextArea).add_class("hide")
