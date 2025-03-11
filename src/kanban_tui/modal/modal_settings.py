from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui
    from kanban_tui.widgets.settings_widgets import AddRule


from textual import on
from textual.widget import Widget
from textual.binding import Binding
from textual.validation import Validator, ValidationResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button
from textual.containers import Horizontal, Vertical


class ModalNewColumnScreen(ModalScreen):
    app: "KanbanTui"
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def __init__(self, event: "AddRule.Pressed") -> None:
        self.event = event
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        column_names = [column.name for column in self.app.column_list]
        with Vertical():
            yield Input(
                placeholder="New Column Name",
                validate_on=["changed"],
                validators=[ValidColumn(columns=column_names)],
            )
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Create Column",
                    id="btn_continue_new_col",
                    variant="success",
                    disabled=True,
                )
                yield Button("Cancel", id="btn_cancel_new_col", variant="error")
            return super().compose()

    @on(Button.Pressed, "#btn_continue_new_col")
    def confirm_new_column(self):
        self.dismiss(result=(self.event, self.query_one(Input).value))

    @on(Button.Pressed, "#btn_cancel_new_col")
    def cancel_new_column(self):
        self.dismiss(result=None)

    @on(Input.Changed)
    def enable_if_valid(self, event: Input.Changed):
        self.query_exactly_one(
            "#btn_continue_new_col", Button
        ).disabled = not event.validation_result.is_valid


class ValidColumn(Validator):
    def __init__(self, columns: list[str], *args, **kwargs) -> None:
        self.columns = columns
        super().__init__(*args, **kwargs)

    def column_is_valid(self, value: str) -> bool:
        return value not in self.columns

    def validate(self, value: str) -> ValidationResult:
        """Check if column name is already present"""
        if self.column_is_valid(value):
            return self.success()
        else:
            return self.failure("Please choose a different column name")
