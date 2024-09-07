from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from kanban_tui.widgets.settings_widgets import AddRule


from textual import on
from textual.widget import Widget
from textual.validation import Validator, ValidationResult
from textual.screen import ModalScreen
from textual.widgets import Input, Button
from textual.containers import Horizontal, Vertical


class ModalNewColumnScreen(ModalScreen):
    def __init__(self, event: "AddRule.Pressed") -> None:
        self.event = event
        super().__init__()

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Input(
                placeholder="New Column Name",
                validate_on=["changed"],
                validators=[ValidColumn()],
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
    def show_help(self, event: Input.Changed):
        if not event.validation_result.is_valid:
            self.query_exactly_one("#btn_continue_new_col", Button).disabled = True
        else:
            self.query_exactly_one("#btn_continue_new_col", Button).disabled = False


class ValidColumn(Validator):
    def validate(self, value: str) -> ValidationResult:
        """Check a string is equal to its reverse."""
        if self.is_single_string(value):
            return self.success()
        else:
            return self.failure("Only Alpha Numeric names are allowed")

    @staticmethod
    def is_single_string(value: str) -> bool:
        return value.isalnum()
