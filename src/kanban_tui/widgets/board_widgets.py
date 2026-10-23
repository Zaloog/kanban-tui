from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.binding import Binding
from textual.containers import HorizontalScroll, VerticalScroll
from textual.events import MouseDown, MouseMove, MouseUp
from textual.reactive import reactive
from textual.widgets import Label

from kanban_tui.classes.task import Task
from kanban_tui.config import Backends
from kanban_tui.modal.modal_board_screen import ModalBoardOverviewScreen
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.widgets.task_column import Column


class KanbanBoard(HorizontalScroll):
    app: KanbanTui

    BINDINGS = [
        Binding("n", "new_task", "New Task", show=True, priority=True),
        Binding("/,ctrl+f", "toggle_filter", "Filter", show=True, priority=True),
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
    drag_target_position: int | None = None
    drag_target_column: int | None = None
    drag_target_card: TaskCard | None = None
    drag_target_before: bool | None = None

    async def on_mount(self):
        await self.populate_board()
        self.watch(self.app, "filter_query", self.watch_filter_query, init=False)
        self.watch(self.app, "filter_field", self.watch_filter_field, init=False)

    async def watch_filter_query(self, _old_query: str, _query: str) -> None:
        await self.refresh_columns()

    async def watch_filter_field(
        self, _old_field: str | None, _field: str | None
    ) -> None:
        await self.refresh_columns()

    def action_toggle_filter(self) -> None:
        from kanban_tui.widgets.filter_bar import FilterBar

        panel = self.screen.query_one(FilterBar)
        if panel.has_class("-hidden"):
            panel.remove_class("-hidden")
            panel.query_one("#filter_query").focus()
        else:
            panel.close_search()

    async def populate_board(self, *args):
        """Populate the board with columns"""
        await self.remove_children()

        for column in self.app.column_list:
            if column.visible:
                column_tasks = [
                    task
                    for task in self.app.task_list
                    if task.column == column.column_id
                    and self._matches_active_filter(task)
                ]
                await self.mount(
                    Column(
                        title=column.name,
                        task_list=column_tasks,
                        id_num=column.column_id,
                    )
                )
        self.get_first_card()

    async def refresh_columns(self) -> None:
        visible_columns = [column for column in self.app.column_list if column.visible]
        mounted_columns = list(self.query(Column))
        focused_widget = self.app.focused
        focused_task = (
            focused_widget.task_ if isinstance(focused_widget, TaskCard) else None
        )
        focused_task_id = focused_task.task_id if focused_task is not None else None

        mounted_column_ids = [
            int(column.id.split("_")[-1])
            for column in mounted_columns
            if column.id is not None
        ]
        visible_column_ids = [column.column_id for column in visible_columns]

        if mounted_column_ids != visible_column_ids:
            await self.populate_board()
            return

        if not all(
            self._column_ready_for_refresh(column) for column in mounted_columns
        ):
            await self.populate_board()
            return

        tasks_by_column: dict[int, list[Task]] = defaultdict(list)
        for task in self.app.task_list:
            if self._matches_active_filter(task):
                tasks_by_column[task.column].append(task)

        for column_model, column_widget in zip(
            visible_columns, mounted_columns, strict=False
        ):
            desired_tasks = tasks_by_column.get(column_model.column_id, [])
            await self._refresh_column_widget(
                column_model.name,
                column_widget,
                desired_tasks,
            )

        if focused_task_id is not None:
            focused_card = self.query_one_optional(
                f"#taskcard_{focused_task_id}", TaskCard
            )
            if focused_card is not None:
                focused_card.focus()
                return

        if focused_widget is not None and not isinstance(focused_widget, TaskCard):
            return

        self.get_first_card()

    def _matches_active_filter(self, task: Task) -> bool:
        from kanban_tui.widgets.filter_bar import FilterBar

        panel = self.screen.query_one_optional(FilterBar)
        return panel is None or panel.matches(task)

    def _column_ready_for_refresh(self, column: Column) -> bool:
        return bool(
            list(column.query(Label).results())
            and list(column.query(VerticalScroll).results())
        )

    def _column_has_same_task_ids(
        self, column: Column, desired_tasks: list[Task]
    ) -> bool:
        rendered_cards = column.get_rendered_cards()
        if len(rendered_cards) != len(desired_tasks):
            return False

        return all(
            card.task_ is not None and card.task_.task_id == task.task_id
            for card, task in zip(rendered_cards, desired_tasks, strict=False)
        )

    async def _refresh_column_widget(
        self,
        title: str,
        column: Column,
        desired_tasks: list[Task],
    ) -> None:
        column.set_title(title)
        column.sync_width()

        if self._column_has_same_task_ids(column, desired_tasks):
            self._refresh_existing_cards_in_place(column, desired_tasks)
            return

        if self._column_render_matches_tasks(column, desired_tasks):
            column.task_list = desired_tasks
            return

        await column.sync_tasks(desired_tasks)

    def _refresh_existing_cards_in_place(
        self,
        column: Column,
        desired_tasks: list[Task],
    ) -> None:
        rendered_cards = column.get_rendered_cards()
        for row_position, (card, task) in enumerate(
            zip(rendered_cards, desired_tasks, strict=False)
        ):
            card.row = row_position
            if not self.app.filter_query and not self.app.filter_field:
                task.position = row_position
            if self.app.needs_refresh or card.task_ != task:
                card.task_ = task
                card.refresh(recompose=True)

        column.task_list = desired_tasks
        column.task_amount = len(desired_tasks)

    def _column_render_matches_tasks(
        self, column: Column, desired_tasks: list[Task]
    ) -> bool:
        rendered_cards = column.get_rendered_cards()
        if len(rendered_cards) != len(desired_tasks):
            return False

        for row_position, (card, task) in enumerate(
            zip(rendered_cards, desired_tasks, strict=False)
        ):
            if card.row != row_position:
                return False
            if card.task_ != task:
                return False

        return True

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
        if not self.app.task_list or self.selected_task is None:
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
        """Updating the target column to drop task"""
        task = event.taskcard.task_
        if task is None:
            return
        self.scroll_visible(animate=False)
        current_column_id = self.target_column or task.column
        match event.direction:
            case "left":
                new_column_id = self.app.get_possible_previous_column_id(
                    current_column_id
                )
            case "right":
                new_column_id = self.app.get_possible_next_column_id(current_column_id)
        if new_column_id == task.column:
            self.target_column = None
            self.query_one(f"#column_{task.column}").scroll_visible(animate=False)
        else:
            self.query_one(f"#column_{new_column_id}").scroll_visible(animate=False)
            self.target_column = new_column_id
            self.start_target_column_timer()

    def start_target_column_timer(self):
        def reset_target_column():
            self.target_column = None
            self._clear_drag_target()
            self.timer = None

        if not self._timers:
            self.timer = self.set_timer(delay=1.2, callback=reset_target_column)
        else:
            self.timer.reset()

    def _clear_drag_target(self) -> None:
        if self.drag_target_card:
            self.drag_target_card.remove_class("drop-before", "drop-after")
        self.drag_target_card = None
        self.drag_target_before = None
        self.drag_target_position = None
        self.drag_target_column = None

    def _set_drag_target(
        self, target_card: TaskCard, before: bool, position: int, column_id: int
    ) -> None:
        if (
            self.drag_target_card is target_card
            and self.drag_target_before == before
            and self.drag_target_column == column_id
        ):
            self.drag_target_position = position
            return

        if self.drag_target_card:
            self.drag_target_card.remove_class("drop-before", "drop-after")

        self.drag_target_card = target_card
        self.drag_target_before = before
        self.drag_target_position = position
        self.drag_target_column = column_id

        target_card.remove_class("drop-before", "drop-after")
        if before:
            target_card.add_class("drop-before")
        else:
            target_card.add_class("drop-after")

    def _update_drag_reorder_target(
        self, column: Column, event: MouseMove, column_id: int, is_cross_column: bool
    ) -> None:
        if self.app.config.backend.mode != Backends.SQLITE:
            self._clear_drag_target()
            return

        if self.selected_task is None:
            self._clear_drag_target()
            return

        moving_card = self.query_one_optional(
            f"#taskcard_{self.selected_task.task_id}", TaskCard
        )
        if moving_card is None:
            self._clear_drag_target()
            return

        cards = list(column.query(TaskCard))
        other_cards = [card for card in cards if card is not moving_card]
        if not other_cards:
            if is_cross_column:
                if self.drag_target_card:
                    self.drag_target_card.remove_class("drop-before", "drop-after")
                self.drag_target_card = None
                self.drag_target_before = None
                self.drag_target_position = 0
                self.drag_target_column = column_id
            else:
                self._clear_drag_target()
            return

        y = event.screen_offset.y
        insert_index = len(other_cards)
        target_card = None
        before = False
        for idx, card in enumerate(other_cards):
            midpoint = card.region.y + (card.region.height / 2)
            if y < midpoint:
                insert_index = idx
                target_card = card
                before = True
                break

        if target_card is None:
            target_card = other_cards[-1]
            before = False

        self._set_drag_target(
            target_card=target_card,
            before=before,
            position=insert_index,
            column_id=column_id,
        )

    def _full_insert_position(self, column_id: int) -> int:
        """Translate a visible drop target into the full persisted column order."""
        moving_id = self.selected_task.task_id if self.selected_task else None
        full_tasks = sorted(
            (
                task
                for task in self.app.task_list
                if task.column == column_id and task.task_id != moving_id
            ),
            key=lambda task: task.position,
        )
        if self.drag_target_card is None:
            return 0 if not full_tasks else len(full_tasks)

        target_task = self.drag_target_card.task_
        if target_task is None:
            return len(full_tasks)
        target_id = target_task.task_id
        for index, task in enumerate(full_tasks):
            if task.task_id == target_id:
                return index if self.drag_target_before else index + 1
        return len(full_tasks)

    def _move_task_within_column(self, target_position: int) -> None:
        if self.app.config.backend.mode != Backends.SQLITE:
            return

        if self.selected_task is None:
            return

        column = self.query_one(f"#column_{self.selected_task.column}", Column)
        if column.id is None:
            return
        moving_card = self.query_one(
            f"#taskcard_{self.selected_task.task_id}", TaskCard
        )
        task_cards = list(column.query(TaskCard))
        if len(task_cards) <= 1:
            return

        current_position = moving_card.row
        if target_position == current_position:
            return

        column_id = int(column.id.rsplit("_", 1)[-1])
        full_target_position = self._full_insert_position(column_id)
        moved_task = self.app.backend.move_task_position(
            task_id=self.selected_task.task_id,
            target_position=full_target_position,
        )
        if moved_task is None:
            return
        self.selected_task = moved_task
        self.app.update_task_list()

        other_cards = [card for card in task_cards if card is not moving_card]
        scroll = column.query_one(VerticalScroll)
        if not other_cards:
            return

        if target_position <= 0:
            scroll.move_child(moving_card, before=other_cards[0])
        elif target_position >= len(other_cards):
            scroll.move_child(moving_card, after=other_cards[-1])
        else:
            scroll.move_child(moving_card, before=other_cards[target_position])

        for idx, card in enumerate(column.query(TaskCard)):
            card.row = idx

        moving_card.focus()

    def watch_target_column(self, old_column: int, new_column: int):
        if old_column is not None:
            self.query_one(f"#column_{old_column}", Column).remove_class("highlighted")

        if new_column is not None:
            self.query_one(f"#column_{new_column}", Column).add_class("highlighted")
        elif hasattr(self, "timer") and self.timer is not None:
            self.timer.reset()

    @on(TaskCard.Moved)
    async def action_confirm_move(self, event: TaskCard.Moved | None = None):
        # BUG Fix for None Column
        self.app.app_focus = False

        # If you confirm, just before the target column timer
        # resets, it can happen, that self.target column is None
        # here, which will raise an exception, because the column
        # field in the database has a NOT NULL constraint

        moving_task = self.selected_task
        active_board = self.app.active_board
        # Determine the target column
        target_column = event.new_column if event else self.target_column
        if moving_task is None or active_board is None or target_column is None:
            self.target_column = None
            self.app.app_focus = True
            return

        # Check if the task can move to the target column (dependency validation)
        can_move, reason = moving_task.can_move_to_column(
            target_column=target_column,
            start_column=active_board.start_column,
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

        # Try the backend update first before modifying local state,
        # so there is nothing to revert on failure.
        original_column = moving_task.column
        moving_task.column = target_column
        target_position = (
            self._full_insert_position(self.target_column)
            if event is None and self.mouse_down and self.target_column is not None
            else None
        )
        result = self.app.backend.update_task_status(
            new_task=moving_task,
            target_position=target_position,
            append_mode=self.app.config.task.append_mode,
        )
        updated_position = result.position if isinstance(result, Task) else None
        moving_task.column = original_column

        # Check if the update was successful (for backends that return status like Jira)
        if isinstance(result, dict) and not result.get("success", True):
            self.app.app_focus = True
            self.target_column = None

            self.app.notify(
                title="Status Update Failed",
                message=result.get("message", "Failed to update issue status"),
                severity="error",
                timeout=5,
            )
            return

        await self.query_one(f"#column_{original_column}", Column).remove_task(
            moving_task
        )

        # Update task status dates based on column transitions
        moving_task.update_task_status(
            new_column=target_column,
            update_column_dict={
                "reset": active_board.reset_column,
                "start": active_board.start_column,
                "finish": active_board.finish_column,
            },
        )

        moving_task.column = target_column
        if updated_position is not None:
            moving_task.position = updated_position

        display_position = (
            self.drag_target_position
            if event is None and self.mouse_down and self.target_column is not None
            else updated_position
        )
        await self.query_one(f"#column_{moving_task.column}", Column).place_task(
            moving_task,
            target_position=display_position,
        )

        self.app.update_task_list()

        # Refresh all task cards to update dependency status immediately
        moved_task_id = moving_task.task_id
        for task_card in self.query(TaskCard):
            # Update the task data from the backend to get latest dependency status
            task = task_card.task_
            if task is None:
                continue
            updated_task = self.app.backend.get_task_by_id(task.task_id)
            if updated_task:
                task_card.task_ = updated_task
                task_card.refresh(recompose=True)

        # Restore focus to the moved task
        self.query_one(f"#taskcard_{moved_task_id}", TaskCard).focus()

        self.target_column = None
        self.app.app_focus = True

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        return not (action == "confirm_move" and self.target_column is None)

    @on(TaskCard.Delete)
    async def delete_task(self, event: TaskCard.Delete):
        task = event.taskcard.task_
        if task is None:
            return
        await self.query_one(f"#column_{task.column}", Column).remove_task(task=task)
        self.app.backend.delete_task(task_id=task.task_id)
        self.app.update_task_list()

        if not self.app.task_list:
            self.get_first_card()

    @on(MouseDown)
    def lift_task(self, event: MouseDown):
        for taskcard in self.query(TaskCard):
            if taskcard.region.contains_point(event.screen_offset):
                self.mouse_down = True
                self.selected_task = taskcard.task_
                taskcard.focus()
                self._clear_drag_target()
                break

    @on(MouseUp)
    async def drop_task(self, event: MouseUp):
        if not self.mouse_down:
            return

        if self.target_column is not None:
            await self.action_confirm_move()
        elif self.drag_target_position is not None:
            self._move_task_within_column(self.drag_target_position)

        self._clear_drag_target()
        self.mouse_down = False

    @on(MouseMove)
    def move_task(self, event: MouseMove):
        if not self.mouse_down:
            return
        if self.selected_task is None:
            return
        selected_task = self.selected_task
        for column in self.query(Column):
            if column.region.contains_point(event.screen_offset):
                if column.id is None:
                    continue
                column_id = int(column.id.split("_")[-1])
                is_same_column = selected_task.column == column_id
                if is_same_column:
                    self.target_column = None
                    if self._timers:
                        self.timer.reset()
                    self._update_drag_reorder_target(
                        column=column,
                        event=event,
                        column_id=column_id,
                        is_cross_column=False,
                    )
                else:
                    self.target_column = column_id
                    self.start_target_column_timer()
                    self._update_drag_reorder_target(
                        column=column,
                        event=event,
                        column_id=column_id,
                        is_cross_column=True,
                    )
                return
        self._clear_drag_target()

    def get_first_card(self):
        # Make it smooth when starting without any Tasks
        if not list(self.query(TaskCard)):
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
