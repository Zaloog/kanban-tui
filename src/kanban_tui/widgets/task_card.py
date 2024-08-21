from __future__ import annotations

from textual import on
from textual.reactive import reactive
from textual.events import Enter, Leave, Mount
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, TextArea
from textual.message import Message


class TaskCard(Vertical):
    expanded: reactive[bool] = reactive(False)
    picked: reactive[bool] = reactive(False)
    position: reactive[tuple[int]]

    class Focused(Message):
        def __init__(self, taskcard: TaskCard) -> None:
            self.taskcard = taskcard
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    def __init__(
        self,
        title: str,
        row: int,
        column: int,
        id: str | None = None,
    ) -> None:
        self.title = title
        self.position = (row, column)

        self.can_focus = True
        self.can_focus_children = False
        super().__init__(id=id)

    def compose(self) -> ComposeResult:
        yield Label(f"Task_{self.title} {self.position}")
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

    def on_focus(self) -> None:
        self.post_message(self.Focused(taskcard=self))
        self.expanded = True

    def on_blur(self) -> None:
        self.expanded = False

    def watch_expanded(self):
        if self.expanded:
            self.query_one(TextArea).remove_class("hidden")
        else:
            self.query_one(TextArea).add_class("hidden")

    # def on_mouse_down(self, event:MouseDown):
    #     self.log.error(f'widget pos: {self.offset}')
    #     self.picked = True
    #     # self.set_styles('layer:above;')
    #     self.offset = event.screen_offset - self.parent.region.offset - Offset(self.region.width//2, self.region.height//2)
    #     self.log.error(f'mouse pos: {self.app.mouse_position}')
    #     self.log.error(f'parent offset: {self.parent.offset}')
    #     self.log.error(f'event: offset {event.offset}')
    #     self.log.error(f'event: screen offset {event.screen_offset}')

    # def on_mouse_up(self, event:MouseUp):
    #     self.picked = False
    #     # self.set_styles('layer:none;')
    #     self.offset = event.screen_offset - self.parent.region.offset - Offset(self.region.width//2, self.region.height//2)

    # def on_mouse_move(self, event:MouseMove):
    #     if self.picked:
    #         self.offset = event.screen_offset - self.parent.region.offset - Offset(self.region.width//2, self.region.height//2)
