from __future__ import annotations
from rich.console import RenderableType
from typing import TYPE_CHECKING, Literal

from kanban_tui.config import MovementModes

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from rich.text import Text
from textual import on, work
from textual.reactive import reactive
from textual.binding import Binding
from textual.events import Click
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Markdown, Rule
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
        yield Rule(classes="rules-taskinfo-separator")
        yield Label(self.get_creation_date_str(), classes="label-infos")
        yield Label(self.get_due_date_str(), classes="label-infos")
        yield Label(self.get_dependency_status_str(), classes="label-infos")
        yield Rule(classes="rules-taskinfo-separator")
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
        # self.query_one(".label-title", Label).visible = not self.expanded
        for label in self.query(".label-infos").results():
            label.display = self.app.config.task.always_expanded or self.expanded
        self.query_one(Markdown).display = (
            self.app.config.task.always_expanded or self.expanded
        )
        self.query_one(".rules-taskinfo-separator", Rule).display = (
            self.app.config.task.always_expanded or self.expanded
        )

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
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

    def get_due_date_str(self) -> RenderableType:
        match self.task_.days_left:
            case 0:
                return Text.from_markup(
                    f":hourglass_done: due date: {self.task_.days_left} days left"
                )
            case 1:
                return Text.from_markup(
                    f":hourglass_not_done: due date: {self.task_.days_left} day left :face_screaming_in_fear:"
                )
            case None:
                return Text.from_markup(":smiling_face_with_sunglasses: no due date")
            case _:
                return Text.from_markup(
                    f":hourglass_not_done: due date: {self.task_.days_left} days left"
                )

    def get_creation_date_str(self) -> RenderableType:
        creation_date_str = Text.from_markup(":calendar: created: ")
        match self.task_.days_since_creation:
            case 0:
                creation_date_str += "today"
                return creation_date_str
            case 1:
                creation_date_str += "yesterday"
                return creation_date_str
            case _:
                creation_date_str += f"{self.task_.days_since_creation} days ago"
                return creation_date_str

    def get_dependency_status_str(self) -> str | Text:
        """Return visual indicator for task dependency status."""
        # Check if task has dependencies that are unfinished
        if self.task_.blocked_by:
            unfinished_deps = []
            for dep_id in self.task_.blocked_by:
                dep_task = self.app.backend.get_task_by_id(dep_id)
                if dep_task and not dep_task.finished:
                    unfinished_deps.append(dep_task)

            if unfinished_deps:
                count = len(unfinished_deps)
                plural = "task" if count == 1 else "tasks"
                return Text.from_markup(f"⚠️ blocked by {count} unfinished {plural}")

        # Check if task is blocking other tasks
        if self.task_.blocking:
            count = len(self.task_.blocking)
            plural = "task" if count == 1 else "tasks"
            return Text.from_markup(f":link: blocking {count} {plural}")

        # No dependency relationships
        return Text.from_markup(":white_check_mark: no dependencies")

    @on(Click)
    def action_edit_task(self) -> None:
        self.app.push_screen(
            ModalTaskEditScreen(task=self.task_), callback=self.from_modal_update_task
        )

    def from_modal_update_task(self, updated_task: Task) -> None:
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

        # Store original colors for each card
        original_colors = {}
        for card in blocking_cards:
            original_colors[card] = card.styles.background

        # Flash animation using set_interval
        flash_count = [0]  # Use list to modify in closure

        def toggle_flash():
            for card in blocking_cards:
                if flash_count[0] % 2 == 0:
                    # Flash on - set to yellow
                    card.styles.background = "yellow"
                else:
                    # Flash off - restore original color
                    card.styles.background = original_colors[card]

            flash_count[0] += 1

            # Stop after 4 toggles (2 full flashes)
            if flash_count[0] >= 4:
                # Ensure all cards are back to original color
                for card in blocking_cards:
                    card.styles.background = original_colors[card]
                return False  # Stop the interval
            return True  # Continue the interval

        # Start flashing with 200ms intervals
        self.set_interval(0.2, toggle_flash)

        # Show notification with blocking task info
        blocking_task_titles = [
            f"#{card.task_.task_id} - {card.task_.title[:30]}"
            for card in blocking_cards
        ]
        self.app.notify(
            title="Blocked By",
            message="\n".join(blocking_task_titles),
            severity="warning",
            timeout=4,
        )

    @work()
    async def action_delete_task(self) -> None:
        confirm_deletion = await self.app.push_screen(
            ModalConfirmScreen(text=f"Delete Task [blue]{self.task_.title}[/]?"),
            wait_for_dismiss=True,
        )
        if confirm_deletion:
            self.post_message(self.Delete(taskcard=self))
