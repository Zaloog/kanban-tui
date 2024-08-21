from typing import Iterable


from textual.events import Mount
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import VerticalScroll, Vertical

from kanban_tui.widgets.task_card import TaskCard


class ReadyColumn(Vertical):
    task_amount: reactive[int] = reactive(0)

    def compose(self) -> Iterable[Widget]:
        yield Label("Ready", id="label_ready")
        yield VerticalScroll(id="column_ready")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one(VerticalScroll).can_focus = False
        return super()._on_mount(event)

    def watch_task_amount(self) -> None:
        if self.task_amount == 0:
            self.query_one("#label_ready", Label).update("Ready")
        elif self.task_amount == 1:
            self.query_one("#label_ready", Label).update("Ready (1 Task)")
        else:
            self.query_one("#label_ready", Label).update(
                f"Ready ({self.task_amount} Tasks)"
            )


class DoingColumn(Vertical):
    task_amount: reactive[int] = reactive(0)

    def compose(self) -> Iterable[Widget]:
        yield Label("Doing", id="label_doing")
        yield VerticalScroll(id="column_doing")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one(VerticalScroll).can_focus = False
        for i in range(5):
            self.task_amount += 1
            card = TaskCard(
                title=f"Task {self.task_amount}", row=self.task_amount, column=2
            )
            self.query_one(VerticalScroll).mount(card)
        return super()._on_mount(event)

    def watch_task_amount(self) -> None:
        if self.task_amount == 0:
            self.query_one("#label_doing", Label).update("Doing")
        elif self.task_amount == 1:
            self.query_one("#label_doing", Label).update("Doing (1 Task)")
        else:
            self.query_one("#label_doing", Label).update(
                f"Doing ({self.task_amount} Tasks)"
            )


class DoneColumn(Vertical):
    task_amount: reactive[int] = reactive(0)

    def compose(self) -> Iterable[Widget]:
        yield Label("Done", id="label_done")
        yield VerticalScroll(id="column_done")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.query_one(VerticalScroll).can_focus = False
        for i in range(5):
            self.task_amount += 1
            card = TaskCard(
                title=f"Task {self.task_amount}", row=self.task_amount, column=3
            )
            self.query_one(VerticalScroll).mount(card)
        return super()._on_mount(event)
