from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual.events import Mount
from textual.widget import Widget
from textual.reactive import reactive
from textual.widgets import Button, Label, SelectionList
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.date_select import CustomDateSelect
from kanban_tui.classes.task import Task


class FilterOverlay(Vertical):
    can_focus: bool = False
    can_focus_children: bool = False
    classes: str = "-hidden"
    filter: reactive[dict] = reactive({"categories": [], "order": "", "due_date": (0,)})
    task_list: reactive[list[Task]] = reactive([])
    filtered_task_list: reactive[list[Task]] = reactive([])

    def __init__(self, task_list: list[Task]) -> None:
        super().__init__(classes=self.classes, id="overlay_filter")
        if task_list:
            self.task_list.clear()
            for col in task_list:
                self.task_list.extend(col)
        self.filtered_task_list = self.task_list.copy()

    def compose(self) -> Iterable[Widget]:
        # Filters:
        # - Categories: select list? /Checkbox in Collapsible
        # - Sort by: Days Left, creation_date, Categories

        # Apply Button (Preview like show 7/29 cards)
        yield Label("Filter your displayed Tasks")
        yield Label("", id="label_task_filtered_amount")
        yield CategoryFilter()
        yield DateFilter()
        # Or a Switch
        yield Button("Cool button", id="btn_test")
        # Reset Filter Button
        yield Button("Cool button2")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        return super()._on_mount(event)

    async def watch_task_list(self):
        if self.task_list:
            self.query_one(CategoryFilter).get_categories(task_list=self.task_list)

    async def watch_filtered_task_list(self):
        self.query_one("#label_task_filtered_amount", Label).update(
            f"show {len(self.filtered_task_list)} / {len(self.task_list)} tasks"
        )

    def watch_filter(self):
        self.filtered_task_list.clear()
        # Change For-loop Order
        for key, filter_vals in self.filter.items():
            match key:
                case "categories":
                    for task in self.task_list:
                        if task.category in filter_vals:
                            self.filtered_task_list.append(task)
        self.mutate_reactive(FilterOverlay.filtered_task_list)

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged):
        self.filter["categories"] = event.selection_list.selected
        self.mutate_reactive(FilterOverlay.filter)


class CategoryFilter(Vertical):
    app: "KanbanTui"

    def __init__(self) -> None:
        super().__init__()
        self.border_title = "Category Filter"

    def compose(self) -> Iterable[Widget]:
        yield SelectionList()
        return super().compose()

    def get_categories(self, task_list: list[Task]):
        category_list = list(set(task.category for task in task_list))
        for category in category_list:
            if category:
                self.query_one(SelectionList).add_option(
                    Selection(
                        f"[black on {self.app.cfg.category_color_dict[category]}]{category}[/]",
                        category,
                        True,
                    )
                )
            else:
                self.query_one(SelectionList).add_option(
                    Selection(f"[black on $primary]{category}[/]", category, True)
                )


class DateFilter(Vertical):
    def __init__(self) -> None:
        super().__init__()
        self.border_title = "Date Filter"

    def compose(self) -> Iterable[Widget]:
        with Horizontal():
            yield Label("From")
            yield CustomDateSelect(
                placeholder="please select",
                format="YYYY-MM-DD",
                picker_mount="#overlay_filter",
                id="dateselect_start",
            )
        with Horizontal():
            yield Label("To")
            yield CustomDateSelect(
                placeholder="please select",
                format="YYYY-MM-DD",
                picker_mount="#overlay_filter",
                id="dateselect_end",
            )
        return super().compose()
