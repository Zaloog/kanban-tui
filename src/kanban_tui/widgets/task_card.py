from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual import on
from textual.reactive import reactive
from textual.events import Enter, Leave, Mount
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Markdown
from textual.message import Message


class TaskCard(Vertical):
    app: "KanbanTui"
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
        EXAMPLE_MARKDOWN = """\
# Markdown Document

This is an example of Textual's `Markdown` widget.

## Features

Markdown syntax and extensions are supported.

- Typography *emphasis*, **strong**, `inline code` etc.
- Headers
- Lists (bullet and ordered)
- Syntax highlighted code blocks
- Tables!
"""
        yield Label(f"Task_{self.title} {self.position}")
        yield Markdown(
            markdown=EXAMPLE_MARKDOWN,
            # id=f"body_task{self.title}",
            classes="hidden",
        )
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        if self.app.cfg.tasks_always_expanded:
            self.query_one(Markdown).remove_class("hidden")
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
            self.border_title = self.title
            self.query_one(Label).add_class("hidden")
            self.query_one(Markdown).remove_class("hidden")
        else:
            self.query_one(Label).remove_class("hidden")
            self.query_one(Markdown).add_class("hidden")

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
