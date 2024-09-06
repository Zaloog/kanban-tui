from typing import Iterable, TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.binding import Binding
from textual.events import Mount
from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Horizontal

from kanban_tui.widgets.task_column import Column
from kanban_tui.widgets.task_card import TaskCard
from kanban_tui.modal.modal_task_screen import ModalTaskEditScreen
from kanban_tui.widgets.filter_sidebar import FilterOverlay
from kanban_tui.database import update_task_db, delete_task_db

from kanban_tui.classes.task import Task


class KanbanBoard(Horizontal):
    app: "KanbanTui"

    BINDINGS = [
        Binding("n", "new_task", "New", show=True, priority=True),
        Binding("f1", "toggle_filter", "Filter", key_display="F1", show=True),
        Binding("j,down", "movement('down')", "Down", show=False),
        Binding("k, up", "movement('up')", "Up", show=False),
        Binding("h, left", "movement('left')", "Left", show=False),
        Binding("l, right", "movement('right')", "Right", show=False),
    ]
    selected_task: reactive[Task | None] = reactive(None)

    def _on_mount(self, event: Mount) -> None:
        self.watch(self.app, "task_list", self.get_first_card)
        return super()._on_mount(event)

    def compose(self) -> Iterable[Widget]:
        # for idx, column_name in enumerate(COLUMNS):
        for idx, column_name in enumerate(self.app.cfg.visible_columns):
            col_tasks = [task for task in self.app.task_list if task.column == idx]
            yield Column(title=column_name, tasklist=col_tasks)
        self.can_focus = False
        yield FilterOverlay()
        return super().compose()

    def action_new_task(self) -> None:
        self.app.push_screen(ModalTaskEditScreen(), callback=self.place_new_task)

    def place_new_task(self, task: Task):
        self.query(Column)[0].place_task(task=task)  # TODO
        # self.query(Column)[self.app.cfg.start_column].place_task(task=task)
        self.selected_task = task
        self.query_one(f"#taskcard_{self.selected_task.task_id}").focus()

    async def update_columns(self):
        for idx, column_name in enumerate(self.app.cfg.visible_columns):
            col_tasks = [task for task in self.app.task_list if task.column == idx]
            await self.query_one(f"#column_{column_name.lower()}").remove()

            self.mount(Column(title=column_name, tasklist=col_tasks))

    # Movement
    def action_movement(self, direction: Literal["up", "right", "down", "left"]):
        current_column_tasks = self.query(Column)[
            self.selected_task.column
        ].task_amount  # TODO
        # current_column = self.query(Column)[self.selected_task.column]
        row_idx = self.query_one(
            f"#taskcard_{self.selected_task.task_id}", TaskCard
        ).row
        match direction:
            case "up":
                match row_idx:
                    case 0:
                        self.query(Column)[self.selected_task.column].query(
                            TaskCard
                        )[  # TODO
                            current_column_tasks - 1
                        ].focus()
                    case _:
                        self.app.action_focus_previous()
            case "down":
                match row_idx:
                    case row_idx if row_idx == (current_column_tasks - 1):
                        self.query(Column)[self.selected_task.column].query(
                            TaskCard
                        )[  # TODO
                            0
                        ].focus()
                    case _:
                        self.app.action_focus_next()
            # TODO
            case "right":
                new_column_id = (self.selected_task.column + 1) % len(
                    self.app.cfg.visible_columns
                )
                new_column_tasks = self.query(Column)[new_column_id].task_amount
                match new_column_tasks:
                    case 0:
                        self.app.action_focus_next()
                    case new_column_tasks if new_column_tasks < current_column_tasks:
                        self.query(Column)[new_column_id].query(TaskCard)[
                            new_column_tasks - 1
                        ].focus()
                    case _:
                        self.query(Column)[new_column_id].query(TaskCard)[
                            row_idx
                        ].focus()
            # TODO
            case "left":
                new_column_id = (
                    self.selected_task.column + len(self.app.cfg.visible_columns) - 1
                ) % len(self.app.cfg.visible_columns)
                new_column_tasks = self.query(Column)[new_column_id].task_amount
                match new_column_tasks:
                    case 0:
                        self.app.action_focus_previous()
                    case new_column_tasks if new_column_tasks < current_column_tasks:
                        self.query(Column)[new_column_id].query(TaskCard)[
                            new_column_tasks - 1
                        ].focus()
                    case _:
                        self.query(Column)[new_column_id].query(TaskCard)[
                            row_idx
                        ].focus()

    @on(TaskCard.Focused)
    def get_current_card_position(self, event: TaskCard.Focused):
        self.selected_task = event.taskcard.task_

    @on(TaskCard.Moved)
    async def move_card_to_other_column(self, event: TaskCard.Moved):
        # remove focus and give focus back to same task in new column
        self.app.app_focus = False

        # TODO
        await self.query(Column)[self.selected_task.column].remove_task(
            self.selected_task
        )

        self.selected_task.column = event.new_column
        update_task_db(task=self.selected_task)

        self.query(Column)[event.new_column].place_task(self.selected_task)
        self.query_one(f"#taskcard_{self.selected_task.task_id}").focus()

        self.app.update_task_list()

    @on(TaskCard.Delete)
    async def delete_task(self, event: TaskCard.Delete):
        # TODO
        await self.query(Column)[event.taskcard.task_.column].remove_task(
            task=event.taskcard.task_
        )
        delete_task_db(task_id=event.taskcard.task_.task_id)
        self.app.update_task_list()

    def get_first_card(self):
        # Make it smooth when starting without any Tasks
        if not self.app.task_list:
            self.can_focus = True
            self.focus()
            self.notify(
                title="Welcome to Kanban Tui",
                message="Looks like you are new, press [blue]n[/] to create your first Card",
            )
        else:
            self.can_focus = False

    # Filter Stuff, to be implemented
    def action_toggle_filter(self) -> None:
        filter = self.query_one(FilterOverlay)
        # open filter
        if filter.has_class("-hidden"):
            self.query(TaskCard).set(disabled=True)
            filter.can_focus_children = True
            # Focus the first Widget on Filter
            filter.query_one("#category_filter").focus()
            filter.remove_class("-hidden")
        # close filter
        else:
            self.query(TaskCard).set(disabled=False)
            filter.can_focus_children = False
            # self.watch(FilterOverlay, 'filtered_task_list', self.change_card_visibility)
            if self.selected_task:
                self.query_one(
                    f"#taskcard_{self.selected_task.task_id}", TaskCard
                ).focus()
            else:
                self.app.action_focus_next()

            filter.add_class("-hidden")

    def change_card_visibility_on_filter(self):
        for task in self.app.task_list:
            for task_fil in self.query_one(FilterOverlay).filtered_task_list:
                if task.task_id == task_fil.task_id:
                    self.notify(f"{task.category}")
                    self.query_one(f"#taskcard_{task.task_id}").set_styles(
                        "display:block;"
                    ).disabled = False
                    continue
                    # self.query_one(f'#taskcard_{task.task_id}').remove_class('hidden').disabled = False
                else:
                    self.query_one(f"#taskcard_{task.task_id}").set_styles(
                        "display:none;"
                    ).disabled = True
                    continue
                    # self.query_one(f'#taskcard_{task.task_id}').add_class('hidden').disabled = True
