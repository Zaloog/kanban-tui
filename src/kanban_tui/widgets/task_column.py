from typing import Iterable


from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import VerticalScroll, Vertical

from kanban_tui.widgets.task_card import TaskCard


class ReadyColumn(Vertical):
    BINDINGS = [("space", "place_task", "new task")]
    task_amount: reactive[int] = reactive(0)

    def compose(self) -> Iterable[Widget]:
        yield Label("Ready", id="label_ready")
        yield VerticalScroll(id="column_ready")
        return super().compose()

    def action_place_task(self, task: TaskCard | None = None) -> None:
        self.task_amount += 1
        self.query_one(VerticalScroll).mount(TaskCard(title=f"Task {self.task_amount}"))

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


class DoneColumn(Vertical):
    task_amount: reactive[int] = reactive(0)

    def compose(self) -> Iterable[Widget]:
        yield Label("Done", id="label_done")
        yield VerticalScroll(id="column_done")
        return super().compose()
