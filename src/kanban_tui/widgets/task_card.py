from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from kanban_tui.config import MovementModes, Backends

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on, work
from textual.reactive import reactive
from textual.binding import Binding
from textual.events import Click
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Markdown
from textual.message import Message


from kanban_tui.classes.task import Task
from kanban_tui.utils import get_column_status_dict
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
from kanban_tui.modal.modal_confirm_screen import ModalConfirmScreen


class TaskCard(Vertical):
    app: "KanbanTui"
    expanded: reactive[bool] = reactive(False, bindings=True)
    mouse_down: reactive[bool] = reactive(False)
    task_: reactive[Task | None] = reactive(None, bindings=True, init=False)

    BINDINGS = [
        Binding("H", "move_task('left')", description="👈", show=True, key_display="H"),
        Binding("e", "edit_task", description="Edit", show=True),
        Binding("d", "delete_task", description="Delete", show=True),
        Binding("i", "show_blocking_tasks", description="Show Deps", show=True),
        Binding(
            "L",
            "move_task('right')",
            description="👉",
            show=True,
            key_display="L",
        ),
    ]

    class Focused(Message):
        def __init__(self, taskcard: TaskCard) -> None:
            self.taskcard = taskcard
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    class Target(Message):
        def __init__(
            self, taskcard: TaskCard, direction: Literal["left", "right"]
        ) -> None:
            self.taskcard = taskcard
            self.direction = direction
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    class Moved(Message):
        def __init__(self, taskcard: TaskCard, new_column: int) -> None:
            self.taskcard = taskcard
            self.new_column = new_column
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    class Delete(Message):
        def __init__(self, taskcard: TaskCard) -> None:
            self.taskcard = taskcard
            super().__init__()

        @property
        def control(self) -> TaskCard:
            return self.taskcard

    def __init__(
        self,
        task: Task,
        row: int,
    ) -> None:
        self.row = row

        self.can_focus = True
        self.can_focus_children = False
        super().__init__(id=f"taskcard_{task.task_id}")
        self.task_ = task

    def compose(self) -> ComposeResult:
        yield Label(self.task_.title, classes="label-title")
        yield Label(self.get_compact_metadata_str(), classes="label-metadata")
        self.description = Markdown(
            markdown=self.task_.description,
        )
        yield self.description

        # Handle Coloring
        self.color_task()

    def color_task(self):
        if category_id := self.task_.category:
            self.styles.background = self.app.backend.get_category_by_id(
                category_id
            ).color
        else:
            self.styles.background = self.app.config.task.default_color
        self.description.styles.background = self.styles.background.darken(0.2)  # type: ignore
        self.description.display = self.app.config.task.always_expanded

    # Remove those, cause it messes with tab selection
    # @on(Enter)
    # @on(Leave)
    def show_details(self) -> None:
        if self.is_mouse_over:
            self.focus()
        else:
            self.parent.focus()

    def on_focus(self) -> None:
        self.expanded = True
        self.scroll_visible()
        self.post_message(self.Focused(taskcard=self))

    def on_blur(self) -> None:
        self.expanded = False

    def watch_expanded(self):
        # Only toggle description visibility - single batch update
        is_visible = self.app.config.task.always_expanded or self.expanded
        self.description.display = is_visible

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if self.app.config.backend.mode == Backends.JIRA:
            if action not in ("edit_task"):
                return False

        column_id_list = list(self.app.visible_column_dict.keys())
        if action == "move_task":
            if parameters == ("left",):
                if column_id_list[0] == self.task_.column:
                    return self.app.config.task.movement_mode == MovementModes.JUMP
            else:
                if column_id_list[-1] == self.task_.column:
                    return self.app.config.task.movement_mode == MovementModes.JUMP
        return True

    def action_move_task(self, direction: Literal["left", "right"]):
        if self.app.config.task.movement_mode == MovementModes.JUMP:
            self.post_message(self.Target(self, direction))
            return
        current_column_id = self.task_.column
        match direction:
            case "left":
                new_column_id = self.app.get_possible_previous_column_id(
                    current_column_id
                )
            case "right":
                new_column_id = self.app.get_possible_next_column_id(current_column_id)

        self.update_task_status_on_move(new_column_id)
        self.post_message(self.Moved(taskcard=self, new_column=new_column_id))

    def update_task_status_on_move(self, new_column_id: int):
        update_column_dict = get_column_status_dict(
            reset=self.app.active_board.reset_column,
            start=self.app.active_board.start_column,
            finish=self.app.active_board.finish_column,
        )
        self.task_.update_task_status(
            new_column=new_column_id, update_column_dict=update_column_dict
        )

    def get_compact_metadata_str(self) -> Text:
        """Compact single-line metadata with icons."""
        parts = []

        # Creation date
        days = self.task_.days_since_creation
        if days == 0:
            parts.append(":calendar: today")
        elif days == 1:
            parts.append(":calendar: 1d")
        else:
            parts.append(f":calendar: {days}d")

        # Due date
        if self.task_.days_left is None:
            parts.append(":smiling_face_with_sunglasses: no due")
        elif self.task_.days_left == 0:
            parts.append(":hourglass_done: due now")
        elif self.task_.days_left == 1:
            parts.append(":hourglass_not_done: 1d :face_screaming_in_fear:")
        else:
            parts.append(f":hourglass_not_done: {self.task_.days_left}d")

        # Dependencies
        if self.task_.blocked_by:
            # Fetch all dependency tasks in a single query to avoid N+1 queries
            dep_tasks = self.app.backend.get_tasks_by_ids(self.task_.blocked_by)
            unfinished_deps = [t for t in dep_tasks if not t.finished]

            if unfinished_deps:
                count = len(unfinished_deps)
                parts.append(f":lock: blocked ({count})")
            else:
                parts.append(":unlocked: not blocked")
        elif self.task_.blocking:
            parts.append(f":exclamation_mark: blocking ({len(self.task_.blocking)})")
        else:
            parts.append(":white_check_mark: no dependencies")

        return Text.from_markup("  ".join(parts))

    @on(Click)
    def action_edit_task(self) -> None:
        self.app.push_screen(
            ModalTaskEditScreen(task=self.task_), callback=self.from_modal_update_task
        )

    def from_modal_update_task(self, updated_task: Task | None) -> None:
        if updated_task:
            self.task_ = updated_task
            self.refresh(recompose=True)

    @work()
    async def action_show_blocking_tasks(self) -> None:
        """Show which tasks are blocking this task by flashing them."""
        if not self.task_.blocked_by:
            self.app.notify(
                title="No Dependencies",
                message="This task has no blocking dependencies",
                severity="information",
                timeout=2,
            )
            return

        # Get all task cards on the board
        board_screen = self.app.get_screen("board")
        all_task_cards = board_screen.query(TaskCard).results()

        # Find task cards that are blocking this task
        blocking_cards = [
            card
            for card in all_task_cards
            if card.task_.task_id in self.task_.blocked_by
        ]

        if not blocking_cards:
            return

        def toggle_flash():
            for card in blocking_cards:
                card.toggle_class("blinking")

        # Start flashing with 100ms intervals
        self.set_interval(0.1, toggle_flash, repeat=5)

    @work()
    async def action_delete_task(self) -> None:
        confirm_deletion = await self.app.push_screen(
            ModalConfirmScreen(
                text=f"Delete task [blue]{self.task_.title}[/]?",
                button_text="Delete task",
            ),
            wait_for_dismiss=True,
        )
        if confirm_deletion:
            self.post_message(self.Delete(taskcard=self))
