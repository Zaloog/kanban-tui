from typing import Iterable, TYPE_CHECKING


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.widget import Widget
from textual.binding import Binding

# from textual.validation import Validator, ValidationResult
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label  # , Button
from textual.containers import Vertical


class ModalAuthScreen(ModalScreen):
    app: "KanbanTui"
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def on_mount(self):
        self.notify(
            title="No Api Key found",
            message="Please enter a valid Api Key",
            severity="warning",
        )

    def compose(self) -> Iterable[Widget]:
        yield Footer()
        with Vertical():
            yield Label(
                f"Your Jira API Key is stored at `{self.app.backend.settings.auth_file_path}`"
            )
            yield Label(f"Your API Key is`{self.app.backend.api_key}`")
            yield Input()

    @on(Input.Submitted)
    def update_api_key(self, event: Input.Submitted):
        value = event.value
        self.app.backend.auth.set_jira_api_key(value)


#     @on(Input.Changed)
#     def enable_if_valid(self, event: Input.Changed):
#         self.query_exactly_one(
#             "#btn_continue_new_col", Button
#         ).disabled = not event.validation_result.is_valid
#
#
# class ValidApiKey(Validator):
#     def __init__(self, columns: list[str], *args, **kwargs) -> None:
#         self.columns = columns
#         super().__init__(*args, **kwargs)
#
#     def column_is_valid(self, value: str) -> bool:
#         return value not in self.columns
#
#     def column_is_empty(self, value: str) -> bool:
#         return value.strip() == ""
#
#     def validate(self, value: str) -> ValidationResult:
#         """Check if column name is already present"""
#         if self.column_is_empty(value):
#             return self.failure()
#         if self.column_is_valid(value):
#             return self.success()
#         else:
#             return self.failure("Please choose a different column name")
