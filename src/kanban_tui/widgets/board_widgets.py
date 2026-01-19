from __future__ import annotations
from typing import TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.events import MouseDown, MouseMove, MouseUp
from textual.binding import Binding
from textual.reactive import reactive
from textual.containers import HorizontalScroll

from kanban_tui.widgets.task_column import Column
from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
from kanban_tui.modal.modal_board_screen import ModalBoardOverviewScreen
from kanban_tui.classes.task import Task


class KanbanBoard(HorizontalScroll):
    app: "KanbanTui"

    BINDINGS = [
        Binding("n", "new_task", "New Task", show=True, priority=True),
        Binding("j,down", "navigation('down')", "Down", show=False),
        Binding("k, up", "navigation('up')", "Up", show=False),
        Binding("h, left", "navigation('left')", "Left", show=False),
        Binding("l, right", "navigation('right')", "Right", show=False),
        Binding("B", "show_boards", "Show Boards", show=True, priority=True),
        Binding("enter", "confirm_move", "Confirm Move", show=True, priority=True),
    ]
    selected_task: reactive[Task | None] = reactive(None)
    target_column: reactive[int | None] = reactive(None, bindings=True, init=False)
    mouse_down: reactive[bool] = reactive(False)

    async def on_mount(self):
        await self.populate_board()

    async def populate_board(self, *args):
        """Populate the board with columns"""
        await self.remove_children()

        for column in self.app.column_list:
            if column.visible:
                column_tasks = [
                    task
                    for task in self.app.task_list
                    if task.column == column.column_id
                ]
                await self.mount(
                    Column(
                        title=column.name,
                        task_list=column_tasks,
                        id_num=column.column_id,
                    )
                )
        self.get_first_card()

    def action_new_task(self) -> None:
        self.app.push_screen(ModalTaskEditScreen(), callback=self.place_new_task)

    async def action_show_boards(self) -> None:
        await self.app.push_screen(
            ModalBoardOverviewScreen(), callback=self.populate_board
        )

    async def place_new_task(self, task: Task | None) -> None:
        if not task:
            return
        await self.query(Column)[0].place_task(task=task)
        self.selected_task = task
        self.query_one(f"#taskcard_{self.selected_task.task_id}", TaskCard).focus()

    # Movement
    def action_navigation(self, direction: Literal["up", "right", "down", "left"]):
        if not self.app.task_list:
            return

        current_column_tasks = self.query_one(
            f"#column_{self.selected_task.column}", Column
        ).task_amount
        row_idx = self.query_one(
            f"#taskcard_{self.selected_task.task_id}", TaskCard
        ).row
        match direction:
            case "up":
                match row_idx:
                    case 0:
                        self.query_one(
                            f"#column_{self.selected_task.column}", Column
                        ).query(TaskCard)[current_column_tasks - 1].focus()
                    case _:
                        self.app.action_focus_previous()
            case "down":
                match row_idx:
                    case row_idx if row_idx == (current_column_tasks - 1):
                        self.query_one(
                            f"#column_{self.selected_task.column}", Column
                        ).query(TaskCard)[0].focus()
                    case _:
                        self.app.action_focus_next()
            case "right":
                column_id_list = list(self.app.visible_column_dict.keys())
                column_index = column_id_list.index(self.selected_task.column)
                new_column_index = (column_index + 1) % len(
                    self.app.visible_column_dict
                )
                new_column_id = column_id_list[new_column_index]
                new_column_tasks = self.query_one(
                    f"#column_{new_column_id}", Column
                ).task_amount
                match new_column_tasks:
                    case 0:
                        self.app.action_focus_next()
                    case new_column_tasks if new_column_tasks <= row_idx:
                        self.query_one(f"#column_{new_column_id}", Column).query(
                            TaskCard
                        )[new_column_tasks - 1].focus()
                    case _:
                        self.query_one(f"#column_{new_column_id}", Column).query(
                            TaskCard
                        )[row_idx].focus()
            case "left":
                column_id_list = list(self.app.visible_column_dict.keys())
                column_index = column_id_list.index(self.selected_task.column)
                new_column_index = (
                    column_index + len(self.app.visible_column_dict) - 1
                ) % len(self.app.visible_column_dict)
                new_column_id = column_id_list[new_column_index]
                new_column_tasks = self.query_one(
                    f"#column_{new_column_id}", Column
                ).task_amount
                match new_column_tasks:
                    case 0:
                        self.app.action_focus_previous()
                    case new_column_tasks if new_column_tasks <= row_idx:
                        self.query_one(f"#column_{new_column_id}", Column).query(
                            TaskCard
                        )[new_column_tasks - 1].focus()
                    case _:
                        self.query_one(f"#column_{new_column_id}", Column).query(
                            TaskCard
                        )[row_idx].focus()

    @on(TaskCard.Focused)
    def get_current_card_position(self, event: TaskCard.Focused):
        self.selected_task = event.taskcard.task_

    @on(TaskCard.Target)
    def color_target_column(self, event: TaskCard.Target):
        self.scroll_visible()
        current_column_id = self.target_column or event.taskcard.task_.column
        match event.direction:
            case "left":
                new_column_id = self.app.get_possible_previous_column_id(
                    current_column_id
                )
            case "right":
                new_column_id = self.app.get_possible_next_column_id(current_column_id)
        if new_column_id == event.taskcard.task_.column:
            self.target_column = None
            self.query_one(f"#column_{event.taskcard.task_.column}").scroll_visible(
                animate=False
            )
        else:
            self.query_one(f"#column_{new_column_id}").scroll_visible(animate=False)
            self.target_column = new_column_id
            self.start_target_column_timer()

    def start_target_column_timer(self):
        def reset_target_column():
            self.target_column = None
            self.timer = None

        if not self._timers:
            self.timer = self.set_timer(delay=1.2, callback=reset_target_column)
        else:
            self.timer.reset()

    def watch_target_column(self, old_column: int, new_column: int):
        if old_column is not None:
            self.query_one(f"#column_{old_column}", Column).remove_class("highlighted")

        if new_column is not None:
            self.query_one(f"#column_{new_column}", Column).add_class("highlighted")
        else:
            self.timer.reset()

    @on(TaskCard.Moved)
    async def action_confirm_move(self, event: TaskCard.Moved | None = None):
        # BUG Fix for None Column
        self.app.app_focus = False

        # If you confirm, just before the target column timer
        # resets, it can happen, that self.target column is None
        # here, which will raise an exception, because the column
        # field in the database has a NOT NULL constraint

        # Determine the target column
        target_column = event.new_column if event else self.target_column

        # Check if the task can move to the target column (dependency validation)
        can_move, reason = self.selected_task.can_move_to_column(
            target_column=target_column,
            start_column=self.app.active_board.start_column,
            backend=self.app.backend,
        )

        if not can_move:
            # Reset app focus and show notification
            self.app.app_focus = True
            self.target_column = None
            self.app.notify(
                title="Movement Blocked",
                message=reason,
                severity="warning",
                timeout=5,
            )
            return

        await self.query_one(
            f"#column_{self.selected_task.column}", Column
        ).remove_task(self.selected_task)

        # Update task status dates based on column transitions
        self.selected_task.update_task_status(
            new_column=target_column,
            update_column_dict={
                "reset": self.app.active_board.reset_column,
                "start": self.app.active_board.start_column,
                "finish": self.app.active_board.finish_column,
            },
        )

        # Handles both movement modes
        self.selected_task.column = target_column

        self.app.backend.update_task_status(new_task=self.selected_task)

        await self.query_one(f"#column_{self.selected_task.column}", Column).place_task(
            self.selected_task
        )

        self.app.update_task_list()

        # Refresh all task cards to update dependency status immediately
        moved_task_id = self.selected_task.task_id
        for task_card in self.query(TaskCard):
            # Update the task data from the backend to get latest dependency status
            updated_task = self.app.backend.get_task_by_id(task_card.task_.task_id)
            if updated_task:
                task_card.task_ = updated_task
                task_card.refresh(recompose=True)

        # Restore focus to the moved task
        self.query_one(f"#taskcard_{moved_task_id}", TaskCard).focus()

        self.target_column = None
        self.app.app_focus = True

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "confirm_move":
            if self.target_column is None:
                return False
        return True

    @on(TaskCard.Delete)
    async def delete_task(self, event: TaskCard.Delete):
        await self.query_one(
            f"#column_{event.taskcard.task_.column}", Column
        ).remove_task(task=event.taskcard.task_)
        self.app.backend.delete_task(task_id=event.taskcard.task_.task_id)
        self.app.update_task_list()

        if not self.app.task_list:
            self.get_first_card()

    @on(MouseDown)
    def lift_task(self, event: MouseDown):
        for taskcard in self.query(TaskCard):
            if taskcard.region.contains_point(event.screen_offset):
                self.mouse_down = True

    @on(MouseUp)
    async def drop_task(self, event: MouseUp):
        if all((self.mouse_down, (self.target_column is not None))):
            await self.action_confirm_move()
        self.mouse_down = False

    @on(MouseMove)
    def move_task(self, event: MouseMove):
        if not self.mouse_down:
            return
        for column in self.query(Column):
            if column.region.contains_point(event.screen_offset):
                is_same_column = self.selected_task.column == int(
                    column.id.split("_")[-1]
                )
                if is_same_column:
                    self.target_column = None
                    if self._timers:
                        self.timer.reset()
                else:
                    self.target_column = int(column.id.split("_")[-1])
                    self.start_target_column_timer()

    def get_first_card(self):
        # Make it smooth when starting without any Tasks
        if not self.app.visible_task_list:
            self.can_focus = True
            self.focus()
            if not self.app.active_board:
                self.notify(
                    title="Welcome to Kanban Tui",
                    message="Looks like you are new, press [blue]n[/] to create your first Board",
                )
            elif not self.app.task_list:
                self.notify(
                    title="Welcome to Kanban Tui",
                    message="Looks like you are new, press [blue]n[/] to create your first Card",
                )
        else:
            self.can_focus = False
            self.app.action_focus_next()
