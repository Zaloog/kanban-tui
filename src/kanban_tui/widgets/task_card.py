from textual import on
from textual.reactive import reactive
from textual.events import Enter, Leave, Mount
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, TextArea


class TaskCard(Vertical):
    expanded: reactive[bool] = reactive(False)

    def __init__(self, title: str | None = None, id: str | None = None) -> None:
        self.title = title
        self.can_focus = True
        self.can_focus_children = False
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Label(f"Task_{self.title}")
        yield TextArea(
            "Body",
            # id=f"body_task{self.title}",
            classes="hidden",
            soft_wrap=False,
            read_only=True,
        )
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        # if self.app.cfg.show_task_details:
        # self.query_one(TextArea).remove_class('hidden')
        return super()._on_mount(event)

    @on(Enter)
    @on(Leave)
    def show_details(self) -> None:
        if self.is_mouse_over:
            self.focus()
        else:
            self.parent.focus()

    def on_focus(self):
        self.expanded = True

    def on_blur(self):
        self.expanded = False

    def watch_expanded(self):
        if self.expanded:
            self.query_one(TextArea).remove_class("hidden")
        else:
            self.query_one(TextArea).add_class("hidden")
