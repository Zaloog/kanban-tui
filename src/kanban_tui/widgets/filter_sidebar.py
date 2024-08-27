from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui

from textual.events import Mount
from textual.binding import Binding
from textual.widget import Widget
from textual.reactive import reactive
from textual.widgets import Button, Label, SelectionList
from textual.widgets.selection_list import Selection
from textual.containers import Vertical, Horizontal

from kanban_tui.widgets.date_select import CustomDateSelect
from kanban_tui.classes.task import Task


class FilterOverlay(Vertical):
    app: "KanbanTui"
    can_focus: bool = False
    can_focus_children: bool = False
    classes: str = "-hidden"
    filter: reactive[dict] = reactive({"categories": [], "order": "", "due_date": (0,)})
    filtered_task_list: reactive[list[Task]] = reactive([])

    def __init__(self) -> None:
        super().__init__(classes=self.classes, id="overlay_filter")
        self.filtered_task_list = self.app.task_list.copy()

    def compose(self) -> Iterable[Widget]:
        yield Label("Filter your displayed Tasks")
        yield PreviewLabel("", id="label_task_filtered_amount")
        yield CategoryFilter(id="category_filter")
        yield DateFilter()
        # Or a Switch
        yield Button("Cool button", id="btn_test")
        # Reset Filter Button
        yield Button("Cool button2")
        return super().compose()

    def _on_mount(self, event: Mount) -> None:
        self.watch(self.app, "task_list", self.init_filtered_task_list)
        return super()._on_mount(event)

    def init_filtered_task_list(self):
        self.filtered_task_list = self.app.task_list
        self.mutate_reactive(FilterOverlay.filtered_task_list)
        self.query_one("#label_task_filtered_amount", Label).update(
            f"show {len(self.filtered_task_list)} / {len(self.app.task_list)} tasks"
        )

    def watch_filter(self):
        self.filtered_task_list.clear()
        # Change For-loop Order
        for task in self.app.task_list:
            for key, filter_vals in self.filter.items():
                match key:
                    case "categories":
                        if task.category in filter_vals:
                            self.filtered_task_list.append(task)
        self.mutate_reactive(FilterOverlay.filtered_task_list)

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged):
        self.filter["categories"] = event.selection_list.selected
        self.mutate_reactive(FilterOverlay.filter)


class PreviewLabel(Label):
    current_shown: reactive[list] = reactive([])

    def _on_mount(self, event: Mount) -> None:
        self.watch(FilterOverlay, "filtered_task_list", self.update_current)
        return super()._on_mount(event)

    def update_current(self, fil):
        try:
            self.current_shown = len(fil)
        except TypeError:
            self.current_shown = len(self.app.task_list)

    def watch_current_shown(self):
        self.update(f"show {self.current_shown} / {len(self.app.task_list)} tasks")


class CategoryFilter(SelectionList):
    app: "KanbanTui"

    BINDINGS = [
        Binding("up,k", "cursor_up", "Cursor Up", show=False),
        Binding("down,j", "cursor_down", "Cursor Down", show=False),
    ]

    def __init__(self, id: str | None = None):
        super().__init__(id=id)
        self.border_title = "Category Filter"

    def on_mount(self):
        self.watch(self.app, "task_list", self.update_categories)
        return super().on_mount()

    def update_categories(self):
        category_list = list(set(task.category for task in self.app.task_list))
        for category in category_list:
            if category:
                self.add_option(
                    Selection(
                        f"[black on {self.app.cfg.category_color_dict[category]}]{category}[/]",
                        category,
                        True,
                    )
                )
            else:
                self.add_option(
                    Selection(f"[black on $primary]{category}[/]", category, True)
                )

    def get_categories(self):
        self.clear_options()
        category_list = list(set(task.category for task in self.app.task_list))
        for category in category_list:
            if category:
                self.add_option(
                    Selection(
                        f"[black on {self.app.cfg.category_color_dict[category]}]{category}[/]",
                        category,
                        True,
                    )
                )
            else:
                self.add_option(
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
