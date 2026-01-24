from typing import Iterable, TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui
    from kanban_tui.widgets.settings_widgets import AddRule


from textual import on
from textual.widget import Widget
from textual.binding import Binding
from textual.validation import Validator, ValidationResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button
from textual.containers import Vertical

from kanban_tui.classes.column import Column
from kanban_tui.widgets.custom_widgets import ButtonRow


class ModalUpdateColumnScreen(ModalScreen):
    app: "KanbanTui"
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(
        self, event: Optional["AddRule.Pressed"] = None, column: Column | None = None
    ) -> None:
        self.event = event or column
        super().__init__()

    def on_mount(self):
        if isinstance(self.event, Column):
            self.query_exactly_one(
                Input
            ).placeholder = f"Current column name: '{self.event.name}'"
            self.query_one(Button).label = "Rename column"
        else:
            self.query_one(Button).label = "Create column"
        self.query_one(Button).disabled = True

    def compose(self) -> Iterable[Widget]:
        column_names = [column.name for column in self.app.column_list]
        with Vertical():
            yield Input(
                placeholder="New Column Name",
                validate_on=["changed"],
                validators=[ValidColumn(columns=column_names)],
            )
            yield ButtonRow(id="horizontal_buttons")

    @on(Button.Pressed, "#btn_continue")
    def confirm_new_column(self):
        updated_name = self.query_one(Input).value
        self.dismiss(result=updated_name)

    @on(Button.Pressed, "#btn_cancel")
    def cancel_new_column(self):
        self.dismiss(result=None)

    @on(Input.Changed)
    def enable_if_valid(self, event: Input.Changed):
        self.query_exactly_one(
            "#btn_continue", Button
        ).disabled = not event.validation_result.is_valid


class ValidColumn(Validator):
    def __init__(self, columns: list[str], *args, **kwargs) -> None:
        self.columns = columns
        super().__init__(*args, **kwargs)

    def column_is_valid(self, value: str) -> bool:
        return value not in self.columns

    def column_is_empty(self, value: str) -> bool:
        return value.strip() == ""

    def validate(self, value: str) -> ValidationResult:
        """Check if column name is already present"""
        if self.column_is_empty(value):
            return self.failure()
        if self.column_is_valid(value):
            return self.success()
        else:
            return self.failure("Please choose a different column name")
