from typing import Iterable, TYPE_CHECKING


if TYPE_CHECKING:
    from kanban_tui.app import KanbanTui


from textual import on
from textual.widget import Widget
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Button
from textual.containers import Vertical
from textual.validation import URL

from kanban_tui.widgets.custom_widgets import ButtonRow


class ModalBaseUrlScreen(ModalScreen):
    app: "KanbanTui"
    BINDINGS = [Binding("escape", "cancel_new_url", "Close")]

    def on_mount(self):
        if self.app.backend.settings.base_url:
            self.query_exactly_one(
                Input
            ).placeholder = f"Current jira base url: '{self.app.backend.base_url}'"
            self.query_one(Button).label = "Update base url"
        else:
            self.query_one(Button).label = "Set base url"
            self.query_one(Button).disabled = True

    def compose(self) -> Iterable[Widget]:
        with Vertical():
            yield Input(
                placeholder="Jira base url",
                valid_empty=False,
                validators=[URL()],
                validate_on=["changed"],
            )
            yield ButtonRow(id="horzontal_buttons")

    @on(Button.Pressed, "#btn_continue")
    def add_new_url(self):
        base_url = self.query_one(Input).value
        self.app.config.set_base_url(base_url)
        self.dismiss(result=base_url)

    @on(Button.Pressed, "#btn_cancel")
    def action_cancel_new_url(self):
        self.dismiss(result=None)

    @on(Input.Changed)
    def enable_if_valid(self, event: Input.Changed):
        is_valid = event.input.value and event.input.is_valid

        self.query_exactly_one("#btn_continue", Button).disabled = not is_valid
