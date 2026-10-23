from typing import TYPE_CHECKING, cast

from textual import on
from textual.binding import Binding
from textual.containers import Horizontal
from textual.geometry import Offset, Region, Spacing
from textual.widgets import Input, Label
from textual_autocomplete import AutoComplete, TargetState

from kanban_tui.classes.task import Task

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui
    from kanban_tui.widgets.board_widgets import KanbanBoard


class FilterQueryInput(Input):
    app: "KanbanTui"

    def action_delete_left(self) -> None:
        if not self.value and self.app.filter_field is not None:
            self.app.filter_field = None
            return
        super().action_delete_left()


class FilterAutoComplete(AutoComplete):
    app: "KanbanTui"

    def _align_and_rebuild(self) -> None:
        self._handle_target_update()

    def _handle_target_update(self) -> None:
        target_state = self._get_target_state()
        self._align_to_target()
        if target_state == self._target_state:
            return

        self._target_state: TargetState = target_state
        search_string = self.get_search_string(target_state)
        self._rebuild_options(target_state, search_string)
        if self.should_show_dropdown(search_string):
            self.action_show()
        else:
            self.action_hide()

    def get_search_string(self, target_state: TargetState) -> str:
        if target_state.text.startswith(":"):
            return target_state.text[1 : target_state.cursor_position]
        return super().get_search_string(target_state)

    def should_show_dropdown(self, _search_string: str) -> bool:
        if self.target.value.startswith(":"):
            return self.option_list.option_count > 0
        return False

    def _align_to_target(self) -> None:
        target_region = self.target.region
        width, height = self.option_list.outer_size
        x, y, _width, _height = Region(
            target_region.x,
            target_region.bottom,
            width,
            height,
        ).constrain(
            "inside",
            "none",
            Spacing.all(0),
            self.screen.scrollable_content_region,
        )
        self.absolute_offset = Offset(x, y)

    def post_completion(self) -> None:
        selected_field = self.target.value.casefold()
        if selected_field in {"title", "description", "category"}:
            self.app.filter_field = selected_field
            self.app.filter_query = ""
            self.target.value = ""
        super().post_completion()


class FilterBar(Horizontal):
    """Inline, session-only board search."""

    app: "KanbanTui"
    BINDINGS = [Binding("escape", "close", "Close search", show=False, priority=True)]
    category_names: dict[int, str]

    def __init__(self) -> None:
        super().__init__(id="filter_bar", classes="-hidden")
        self.category_names = {}
        self.search_input = FilterQueryInput(
            placeholder="Search all fields; type : to choose a filter",
            id="filter_query",
        )
        self.autocomplete = FilterAutoComplete(
            self.search_input,
            candidates=["Title", "Description", "Category"],
        )

    def compose(self):
        yield Label("Search", id="filter_prompt")
        yield self.search_input
        yield self.autocomplete

    def on_mount(self) -> None:
        self.refresh_category_names()
        self.watch(self.app, "task_list", self.refresh_category_names)
        self.watch(self.app, "filter_query", self.watch_filter_query, init=False)
        self.watch(self.app, "filter_field", self.watch_filter_field, init=False)

    def refresh_category_names(self) -> None:
        self.category_names = {
            category.category_id: category.name
            for category in self.app.backend.get_all_categories()
        }

    @on(Input.Changed, "#filter_query")
    def update_filter(self, event: Input.Changed) -> None:
        query = event.value.strip().casefold()
        self.app.filter_query = "" if query.startswith(":") else query

    def watch_filter_query(self, _old_query: str, _query: str) -> None:
        self.update_filter_subtitle()

    def watch_filter_field(self, _old_field: str | None, _field: str | None) -> None:
        self.update_filter_subtitle()

    def update_filter_subtitle(self) -> None:
        board = cast(
            "KanbanBoard",
            self.app.get_screen("board").query_one("KanbanBoard"),
        )
        query = self.app.filter_query
        field = self.app.filter_field
        search = self.query_one("#filter_query", FilterQueryInput)
        search.placeholder = (
            f"Backspace to remove {field} filter"
            if field
            else "Search all fields; type : to choose a filter"
        )
        if field:
            if query:
                self.border_subtitle = ""
                board.border_subtitle = f"🔍 {field.title()}: {query}"
            else:
                self.border_subtitle = f"🔍 {field.title()}"
                board.border_subtitle = ""
        elif query:
            self.border_subtitle = ""
            board.border_subtitle = f"🔍 All: {query}"
        else:
            self.border_subtitle = ""
            board.border_subtitle = ""

    @on(Input.Submitted, "#filter_query")
    def accept_filter(self, event: Input.Submitted) -> None:
        self.close_search()

    def action_close(self) -> None:
        self.app.filter_query = ""
        self.app.filter_field = None
        search = self.query_one("#filter_query", Input)
        search.value = ""
        self.close_search()

    def close_search(self) -> None:
        self.add_class("-hidden")
        board = cast(
            "KanbanBoard",
            self.app.get_screen("board").query_one("KanbanBoard"),
        )
        focused_task_id = (
            board.selected_task.task_id if board.selected_task is not None else None
        )
        if focused_task_id is not None:
            card = board.query_one_optional(f"#taskcard_{focused_task_id}")
            if card is not None:
                card.focus()
                return
        board.get_first_card()

    def matches(self, task: Task) -> bool:
        query = self.app.filter_query
        field = self.app.filter_field
        if not query:
            return True
        category_name = (
            self.category_names.get(task.category, "")
            if task.category is not None
            else ""
        )
        if field == "category":
            return query in category_name.casefold()
        if field == "title":
            searchable = task.title.casefold()
        elif field == "description":
            searchable = task.description.casefold()
        else:
            searchable = f"{task.title}\n{task.description}\n{category_name}".casefold()
        return query in searchable
