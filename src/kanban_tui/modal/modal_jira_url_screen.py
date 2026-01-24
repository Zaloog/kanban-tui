from typing import Iterable, TYPE_CHECKING


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Button
from textual.containers import Horizontal, Vertical


class ModalUpdateBaseUrl(ModalScreen):
    app: "KanbanTui"
    BINDINGS = [Binding("escape", "app.pop_screen", "Close")]

    def on_mount(self):
        if self.app.backend.base_url:
            self.query_exactly_one(
                Input
            ).placeholder = f"Current jira base url: '{self.app.backend.base_url}'"
            self.query_one(Button).label = "Update base url"

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Input(
                placeholder="Jira base url",
            )
            with Horizontal(id="horizontal_buttons_delete"):
                yield Button(
                    "Create Column",
                    id="btn_continue_new_col",
                    variant="success",
                    disabled=True,
                )
                yield Button("Cancel", id="btn_cancel_new_col", variant="error")

    @on(Button.Pressed, "#btn_continue_new_col")
    def confirm_new_column(self):
        updated_name = self.query_one(Input).value
        self.dismiss(result=updated_name)

    @on(Button.Pressed, "#btn_cancel_new_col")
    def cancel_new_column(self):
        self.dismiss(result=None)

    @on(Input.Changed)
    def enable_if_valid(self, event: Input.Changed):
        self.query_exactly_one(
            "#btn_continue_new_col", Button
        ).disabled = not event.validation_result.is_valid
